#!/usr/bin/python
# -*- coding: utf-8 -*-

# gui.py
# Copyright © 2008, 2009, 2011 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Authors: Nils Philippsen <nphilipp@redhat.com>

""" system-config-services: This module contains GUI functionality. """

import scservices.config as config
from scservices.core.systemd.manager import SystemDManager
from scservices.core.systemd.unit import SystemDService
from scservices.core.systemd.util import check_systemd_active

import os.path
import sys

import gobject
import gtk
import gtk.glade

import slip.dbus.polkit
import slip.gtk

import locale
locale.setlocale(locale.LC_ALL, '')

import gettext
_ = lambda x: gettext.ldgettext("system-config-services", x)

from scservices.core.legacy.serviceherders import SVC_ADDED, SVC_DELETED, \
    SVC_CONF_UPDATING, SVC_CONF_CHANGED, SVC_STATUS_UPDATING, \
    SVC_STATUS_CHANGED, SVC_HERDER_READY

import scservices.core.legacy.services as services
from scservices.core.legacy.services import SVC_STATUS_REFRESHING, \
    SVC_STATUS_UNKNOWN, SVC_STATUS_STOPPED, SVC_STATUS_RUNNING, \
    SVC_STATUS_DEAD, SVC_ENABLED_REFRESHING, SVC_ENABLED_ERROR, \
    SVC_ENABLED_YES, SVC_ENABLED_NO, SVC_ENABLED_CUSTOM

gtk.glade.bindtextdomain(config.domain)

all_svc_columns = (SVC_COL_SVC_OBJECT, SVC_COL_STATUS, SVC_COL_NAME,
        SVC_COL_REMARK) = range(4)

class GUIServicesListStore(gtk.ListStore):

    col_types = {
        SVC_COL_SVC_OBJECT: gobject.TYPE_PYOBJECT,
        SVC_COL_STATUS: gobject.TYPE_STRING,
        SVC_COL_NAME: gobject.TYPE_STRING,
        SVC_COL_REMARK: gobject.TYPE_STRING,
        }

    def __init__(self):
        col_types = []
        for col in all_svc_columns:
            col_types.append(self.col_types[col])
        gtk.ListStore.__init__(self, *col_types)
        self.set_default_sort_func(self._sort_by_name)
        self.set_sort_func(SVC_COL_NAME, self._sort_by_name)
        self.set_sort_column_id(SVC_COL_NAME, gtk.SORT_ASCENDING)

        self.service_iters = {}

    def _sort_by_name(self, treemodel, iter1, iter2, user_data=None):
        name1 = self.get(iter1, SVC_COL_NAME)
        name2 = self.get(iter2, SVC_COL_NAME)

        return name1 < name2 and -1 or name1 > name2 and 1 or 0

    def add_service(self, service):
        iter = self.append(None)
        self.set(iter,
                 SVC_COL_SVC_OBJECT, service,
                 SVC_COL_NAME, service.name)
        self.service_iters[service] = iter

    def _delete_svc_callback(self, model, path, iter, service):
        row_service = self.get_value(iter, SVC_COL_SVC_OBJECT)

        if row_service == service:
            self.remove(iter)
            return True

        return False

    def delete_service(self, service):
        self.foreach(self._delete_svc_callback, service)
        del self.service_iters[service]


class GUIServicesTreeView(gtk.TreeView):

    COL_TITLE = 0
    COL_CELL_RENDERER = 1
    COL_ATTRNAME = 2
    COL_CLICKABLE = 3
    COL_EXPAND = 4
    COL_RESIZABLE = 5
    COL_FIXED_WIDTH = 6
    COL_LAST = 7

    col_spec = {
        SVC_COL_STATUS: ["", gtk.CellRendererPixbuf, "stock_id",
            False, False, False,
            gtk.icon_size_lookup(gtk.ICON_SIZE_MENU)[0]],
        SVC_COL_NAME: [_("Name"), gtk.CellRendererText, "text",
            True, True, True,
            None],
        SVC_COL_REMARK: [_("Remarks"), gtk.CellRendererText, "text",
            True, True, True,
            None],
        }

    def __init__(self):
        self.model = GUIServicesListStore()

        gtk.TreeView.__init__(self, model=self.model)

        self.selection = self.get_selection()

        for column in xrange(1, len(all_svc_columns)):
            title = self.col_spec[column][self.COL_TITLE]
            cell_renderer = self.col_spec[column][self.COL_CELL_RENDERER]()

            attrname = self.col_spec[column][self.COL_ATTRNAME]
            if attrname:
                col = gtk.TreeViewColumn(title, cell_renderer,
                        **{attrname: column})
            else:
                col = gtk.TreeViewColumn(title, cell_renderer)

            clickable = self.col_spec[column][self.COL_CLICKABLE]
            expand = self.col_spec[column][self.COL_EXPAND]
            resizable = self.col_spec[column][self.COL_RESIZABLE]
            properties = {"clickable": clickable, "expand": expand,
                          "resizable": resizable}
            fixed_width = self.col_spec[column][self.COL_FIXED_WIDTH]
            if fixed_width != None:

                # add some padding

                fixed_width += 5
                properties["fixed-width"] = fixed_width

            col.set_properties(**properties)
            self.append_column(col)

        self.selection.set_mode(gtk.SELECTION_SINGLE)
        self.selection.connect("changed", self.on_selection_changed)

    def on_selection_changed(self, selection, *p):
        selected = selection.get_selected()
        if selected == None:
            self.emit("service-selected", None)
            return
        (model, iter) = selected
        if iter == None:
            self.emit("service-selected", None)
            return
        service = model.get(iter, SVC_COL_SVC_OBJECT)
        self.emit("service-selected", service[0])


_service_selected_signal = gobject.signal_new("service-selected",
        GUIServicesTreeView, gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION,
        gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, ))

_enabled_stock_id = {
    SVC_ENABLED_REFRESHING: gtk.STOCK_REFRESH,
    SVC_ENABLED_ERROR: gtk.STOCK_DIALOG_WARNING,
    SVC_ENABLED_YES: gtk.STOCK_YES,
    SVC_ENABLED_NO: gtk.STOCK_NO,
    SVC_ENABLED_CUSTOM: gtk.STOCK_PREFERENCES,
    'fixme': '', # FIXME
    'enabled': gtk.STOCK_YES,
    'active': gtk.STOCK_YES,
    'disabled': gtk.STOCK_NO,
    'inactive': gtk.STOCK_NO,
    'masked': gtk.STOCK_DIALOG_ERROR,
    }

_enabled_text = {
    SVC_ENABLED_REFRESHING: _("This service is being refreshed right now."),
    SVC_ENABLED_ERROR: _("Getting information about this service failed."),
    SVC_ENABLED_YES: _("This service is enabled."),
    SVC_ENABLED_NO: _("This service is disabled."),
    SVC_ENABLED_CUSTOM: \
            _("This service is enabled in runlevels: %(runlevels)s"),
    'fixme': "Enabled, disabled, who knows?", # FIXME
    'enabled': _("This service is enabled."),
    'active': _("This service is enabled."),
    'disabled': _("This service is disabled."),
    'inactive': _("This service is disabled."),
    'masked': _("This service is masked."),
    }

_status_stock_id = {
    SVC_STATUS_REFRESHING: gtk.STOCK_REFRESH,
    SVC_STATUS_UNKNOWN: gtk.STOCK_DIALOG_QUESTION,
    SVC_STATUS_STOPPED: gtk.STOCK_DISCONNECT,
    SVC_STATUS_RUNNING: gtk.STOCK_CONNECT,
    SVC_STATUS_DEAD: gtk.STOCK_DIALOG_WARNING,
    }

_status_text = {
    SVC_STATUS_REFRESHING: _("This service is being refreshed right now."),
    SVC_STATUS_UNKNOWN: _("The status of this service is unknown."),
    SVC_STATUS_STOPPED: _("This service is stopped."),
    SVC_STATUS_RUNNING: _("This service is running."),
    SVC_STATUS_DEAD: _("This service is dead."),
    }

def _xinetd_enabled_icon_text(enabled):
    xinetd_enabled_icon_text = {
            SVC_ENABLED_REFRESHING: (gtk.STOCK_REFRESH,
                _("This service is being refreshed right now.")),
            SVC_ENABLED_ERROR: (gtk.STOCK_DIALOG_WARNING,
                _("Getting information about this service failed.")),
            SVC_ENABLED_YES: (gtk.STOCK_CONNECT, ("This service is enabled.")),
            SVC_ENABLED_NO: (gtk.STOCK_DISCONNECT,
                _("This service is disabled.")),
        }

    return xinetd_enabled_icon_text[enabled]

def _systemd_active_sub_state_icon_text(active_state, sub_state):
    if active_state == 'inactive':
        icon = gtk.STOCK_DISCONNECT
        if sub_state == 'dead':
            text = _("This unit is inactive.")
        else:
            text = _("This unit is inactive: %(sub_state)s") % locals()
    elif active_state == 'active':
        if sub_state == 'running':
            icon = gtk.STOCK_MEDIA_PLAY
            text = _("This unit is running.")
        elif sub_state == 'exited':
            icon = gtk.STOCK_MEDIA_STOP
            text = _("This unit has finished.")
        else:
            icon = gtk.STOCK_CONNECT
            text = _("This unit is active: %(sub_state)s") % locals()
    elif active_state == 'failed':
        icon = gtk.STOCK_DIALOG_WARNING
        text = _("This unit has failed: %(sub_state)s") % locals()
    elif active_state == 'activating':
        icon = gtk.STOCK_MEDIA_FORWARD
        if sub_state == 'start':
            text = _("This unit is starting.")
        else:
            text = _("This unit is activating: %(sub_state)s") % locals()
    elif active_state == 'deactivating':
        icon = gtk.STOCK_MEDIA_NEXT
        text = _("This unit is deactivating: %(sub_state)s") % locals()
    else:
        icon = gtk.STOCK_DIALOG_QUESTION
        text = _("The state of this unit is unknown: %(active_state)s/%(sub_state)s") % locals()

    return icon, text


class GladeController(object):

    _xml_widgets = []

    def __init__(self, xml):
        self.xml = xml

        for wname in self._xml_widgets:
            w = xml.get_widget(wname)
            if w:
                setattr(self, wname, w)
            else:
                raise KeyError(wname)

        # connect defined signals with callback methods

        xml.signal_autoconnect(self)


class GUIServicesDetailsPainter(GladeController):

    """Services details painter singleton factory"""

    _classes = None
    _classes_objects = {}

    def __new__(cls, serviceslist, service, *p, **k):
        if GUIServicesDetailsPainter._classes == None:
            GUIServicesDetailsPainter._classes = {
                    SystemDService: GUISystemDServicesDetailsPainter,
                    services.SysVService: GUISysVServicesDetailsPainter,
                    services.XinetdService: GUIXinetdServicesDetailsPainter}

        painter_class = None

        for (svc_cls, ptr_cls) in \
            GUIServicesDetailsPainter._classes.iteritems():
            if isinstance(service, svc_cls):
                painter_class = ptr_cls
                break

        if not painter_class:
            raise TypeError("service: %s" % service)

        if painter_class not in GUIServicesDetailsPainter._classes_objects:
            GUIServicesDetailsPainter._classes_objects[painter_class] = \
                object.__new__(painter_class)

        return GUIServicesDetailsPainter._classes_objects[painter_class]

    def __init__(self, serviceslist, service):
        super(GUIServicesDetailsPainter, self).__init__(serviceslist.xml)
        self.serviceslist = serviceslist
        self.service = service

    def paint_details(self):
        raise NotImplementedError


class GUISystemDServicesDetailsPainter(GUIServicesDetailsPainter):

    """Details painter for systemd services"""

    _xml_widgets = (
        "SystemDServiceExplanationLabel",
        "SystemDServiceEnabledIcon",
        "SystemDServiceEnabledLabel",
        "SystemDServiceStatusIcon",
        "SystemDServiceStatusLabel",
        "SystemDServiceDescriptionTextView",
        )

    def paint_details(self):
        self.SystemDServiceExplanationLabel.set_markup(
                _("The <b>%(servicename)s</b> service is managed by systemd. "
                  "It may be started then run in the background, or be "
                  "activated on demand, or run once for preparation or "
                  "cleanup purposes.") % {'servicename': self.service.name})

        enabled = 'fixme' # FIXME

        self.SystemDServiceEnabledIcon.set_from_stock(
                _enabled_stock_id[enabled], gtk.ICON_SIZE_MENU)
        self.SystemDServiceEnabledLabel.set_text(_enabled_text[enabled])

        icon, text = _systemd_active_sub_state_icon_text(
                self.service.ActiveState, self.service.SubState)
        self.SystemDServiceStatusIcon.set_from_stock(icon, gtk.ICON_SIZE_MENU)
        self.SystemDServiceStatusLabel.set_text(text)

        description = self.service.Description
        self.SystemDServiceDescriptionTextView.get_buffer().set_text(
                description)


class GUISysVServicesDetailsPainter(GUIServicesDetailsPainter):

    """Details painter for SysV services"""

    _xml_widgets = (
        "sysVServiceExplanationLabel",
        "sysVServiceEnabledIcon",
        "sysVServiceEnabledLabel",
        "sysVServiceStatusIcon",
        "sysVServiceStatusLabel",
        "sysVServiceDescriptionTextView",
        )

    def paint_details(self):
        self.sysVServiceExplanationLabel.set_markup(
                _("The <b>%(servicename)s</b> service is started once, "
                  "usually when the system is booted, runs in the background "
                  "and wakes up when needed.") %
                {"servicename": self.service.name})

        enabled = self.service.get_enabled()
        self.sysVServiceEnabledIcon.set_from_stock(_enabled_stock_id[enabled],
                gtk.ICON_SIZE_MENU)
        if enabled == SVC_ENABLED_CUSTOM:
            runlevels = ", ".join(map(str, sorted(self.service.runlevels)))
            self.sysVServiceEnabledLabel.set_text(_enabled_text[enabled] %
                     {"runlevels": runlevels})
        else:
            self.sysVServiceEnabledLabel.set_text(_enabled_text[enabled])

        if self.service.status_updates_running > 0:
            self.sysVServiceStatusIcon.set_from_stock(gtk.STOCK_REFRESH,
                    gtk.ICON_SIZE_MENU)
            self.sysVServiceStatusLabel.set_text(
                    _("This service is updated currently."))
        else:
            stock_icon_id = _status_stock_id[self.service.status]
            self.sysVServiceStatusIcon.set_from_stock(stock_icon_id,
                    gtk.ICON_SIZE_MENU)
            self.sysVServiceStatusLabel.set_text(
                    _status_text[self.service.status])

        if self.service.info.description:
            self.sysVServiceDescriptionTextView.get_buffer().\
                    set_text(self.service.info.description)
        else:
            self.sysVServiceDescriptionTextView.get_buffer().set_text("")


class GUIXinetdServicesDetailsPainter(GUIServicesDetailsPainter):

    _xml_widgets = ("xinetdServiceExplanationLabel",
                    "xinetdServiceEnabledIcon", "xinetdServiceEnabledLabel",
                    "xinetdServiceDescriptionTextView")

    def __init__(self, serviceslist, service):
        super(GUIXinetdServicesDetailsPainter, self).__init__(serviceslist,
                service)

    def paint_details(self):
        self.xinetdServiceExplanationLabel.set_markup(
                _("The <b>%(servicename)s</b> service will be started on "
                  "demand by the xinetd service and ends when it has nothing "
                  "more to do.") %
                {"servicename": self.service.name})

        enabled = self.service.get_enabled()
        xinetd_service = self.serviceslist.xinetd_service
        if enabled == SVC_ENABLED_YES and not xinetd_service:
            self.xinetdServiceEnabledIcon.set_from_stock(
                    gtk.STOCK_DIALOG_WARNING,
                    gtk.ICON_SIZE_MENU)
            self.xinetdServiceEnabledLabel.set_markup(
                    _("This service is enabled, but the <b>xinetd</b> package "
                    "is not installed. This service does not work without it."
                    ))
        elif enabled == SVC_ENABLED_YES and (
                isinstance(xinetd_service, SystemDService) and
                xinetd_service.ActiveState != 'active' or
                xinetd_service.status != SVC_STATUS_RUNNING):
            self.xinetdServiceEnabledIcon.set_from_stock(
                    gtk.STOCK_DIALOG_WARNING,
                    gtk.ICON_SIZE_MENU)
            self.xinetdServiceEnabledLabel.set_markup(
                    _("This service is enabled, but the <b>xinetd</b> "
                      "service is not running. This service does not work "
                      "without it."))
        else:
            icon, text = _xinetd_enabled_icon_text(enabled)
            self.xinetdServiceEnabledIcon.set_from_stock(icon,
                    gtk.ICON_SIZE_MENU)
            self.xinetdServiceEnabledLabel.set_text(text)

        if self.service.info.description:
            self.xinetdServiceDescriptionTextView.get_buffer().set_text(
                    self.service.info.description)
        else:
            self.xinetdServiceDescriptionTextView.get_buffer().set_text("")


class GUIServiceEntryPainter(object):

    def __new__(cls, serviceslist, service, *p, **k):
        if isinstance(service, SystemDService):
            return object.__new__(GUISystemDServiceEntryPainter)
        elif isinstance(service, services.SysVService):
            return object.__new__(GUISysVServiceEntryPainter)
        elif isinstance(service, services.XinetdService):
            return object.__new__(GUIXinetdServiceEntryPainter)
        else:
            raise TypeError("service")

    def __init__(self, serviceslist, service):
        self.serviceslist = serviceslist
        self.treestore = serviceslist.servicesTreeStore
        self.service = service

    def paint(self):
        raise NotImplementedError


class GUISystemDServiceEntryPainter(GUIServiceEntryPainter):

    def paint(self):
        iter = self.treestore.service_iters[self.service]
        self.treestore.set(iter, SVC_COL_STATUS,
                _systemd_active_sub_state_icon_text(self.service.ActiveState,
                    self.service.SubState)[0])
        self.treestore.set(iter, SVC_COL_REMARK, self.service.Description)


class GUISysVServiceEntryPainter(GUIServiceEntryPainter):

    def paint(self):
        iter = self.treestore.service_iters[self.service]
        self.treestore.set(iter, SVC_COL_STATUS,
                           _status_stock_id[self.service.status])
        if self.service.info.shortdescription:
            self.treestore.set(iter, SVC_COL_REMARK,
                               self.service.info.shortdescription)


class GUIXinetdServiceEntryPainter(GUIServiceEntryPainter):

    def paint(self):
        iter = self.treestore.service_iters[self.service]
        enabled = self.service.get_enabled()
        xinetd_service = self.serviceslist.xinetd_service
        if enabled == SVC_ENABLED_YES and (not xinetd_service or
                isinstance(xinetd_service, SystemDService) and
                xinetd_service.ActiveState != 'active' or
                xinetd_service.status != SVC_STATUS_RUNNING):
            self.treestore.set(iter, SVC_COL_STATUS,
                               gtk.STOCK_DIALOG_WARNING)
        else:
            self.treestore.set(iter, SVC_COL_STATUS,
                    _xinetd_enabled_icon_text(enabled)[0])


class GUIServicesList(GladeController):

    SVC_PAGE_NONE = 0
    SVC_PAGE_SYSV = 1
    SVC_PAGE_XINETD = 2
    SVC_PAGE_SYSTEMD = 3

    _service_xml_widgets = (
        "serviceEnable",
        "serviceDisable",
        "serviceCustomize",
        "serviceStart",
        "serviceStop",
        "serviceRestart",
        # "serviceInformation",
        "serviceEnableButton",
        "serviceDisableButton",
        "serviceCustomizeButton",
        "serviceStartButton",
        "serviceStopButton",
        "serviceRestartButton",
        # "serviceInformationButton",
        )

    _xml_widgets = _service_xml_widgets + (
        "mainWindow",
        "servicesListDetailsPaned",
        "servicesScrolledWindow",
        "servicesDetailsNotebook",
        "serviceRunlevel2",
        "serviceRunlevel3",
        "serviceRunlevel4",
        "serviceRunlevel5",
        )

    def __init__(self, xml, serviceherders, systemd_manager):
        self.busy_cursor = gtk.gdk.Cursor(gtk.gdk.WATCH)
        self.inhibit_recursion = False

        self.current_service = None
        self.xinetd_service = None
        self.service_painters = {}

        super(GUIServicesList, self).__init__(xml)

        self.runlevels_checkboxes = {
            2: self.serviceRunlevel2,
            3: self.serviceRunlevel3,
            4: self.serviceRunlevel4,
            5: self.serviceRunlevel5,
            }

        self.checkboxes_runlevels = {}

        # connect these signal handlers here so we can block/unblock them later

        self.runlevels_toggled_handlers = {}
        for (rl, cb) in self.runlevels_checkboxes.iteritems():
            self.checkboxes_runlevels[cb] = rl
            self.runlevels_toggled_handlers[rl] = cb.connect("toggled",
                    self.on_serviceRunlevels_toggled)

        servicesTreeView = xml.get_widget("servicesTreeView")
        self.servicesScrolledWindow.remove(servicesTreeView)

        self.servicesTreeView = GUIServicesTreeView()
        self.servicesTreeView.show()
        self.servicesTreeView.set_rules_hint(True)
        self.servicesTreeView.connect("service-selected",
                                      self.on_service_selected)

        self.servicesTreeStore = self.servicesTreeView.model

        self.servicesScrolledWindow.add(self.servicesTreeView)

        self.on_service_selected()

        self.mainWindow.realize()

        self.disable()

        self.systemd_manager = systemd_manager
        if systemd_manager:
            systemd_manager.connect("unit_new", self.on_systemd_unit_new)
            systemd_manager.connect("unit_removed",
                    self.on_systemd_unit_removed)
            systemd_manager.connect("discovery_started",
                    self.on_systemd_manager_discovery_started)
            systemd_manager.connect("discovery_finished",
                    self.on_systemd_manager_discovery_finished)
            if not systemd_manager.discovering:
                # simulate systemd manager discovering already known units
                for unit in systemd_manager.units.itervalues():
                    self.on_unit_new(systemd_manager, unit)
                self.on_systemd_discovery_finished(systemd_manager)

        self.serviceherders = set(serviceherders)
        self.serviceherders_ready = set()

        for herder in serviceherders:
            herder.subscribe(self.on_services_changed)
            if herder.ready:
                self.on_service_herder_ready(herder)

    def on_systemd_unit_new(self, manager, unit):
        if isinstance(unit, SystemDService):
            self.on_service_added(unit)
            unit.connect("properties_changed", self.on_unit_properties_changed)

    def on_systemd_unit_removed(self, manager, unit):
        if isinstance(unit, SystemDService):
            self.on_service_removed(unit)

    def on_systemd_manager_discovery_started(self, manager):
        pass

    def on_systemd_manager_discovery_finished(self, manager):
        self.enable_on_discovery_finished()

    def enable_on_discovery_finished(self):
        if self.serviceherders == self.serviceherders_ready and not (
                self.systemd_manager and self.systemd_manager.discovering):
            self.enable()
        else:
            self.disable()

    def _update_runlevel_menu(self):
        for rl in xrange(2, 6):
            self.runlevels_checkboxes[rl].handler_block(self.runlevels_toggled_handlers[rl])
            self.runlevels_checkboxes[rl].set_active(rl in
                     self.current_service.runlevels)
            self.runlevels_checkboxes[rl].handler_unblock(self.runlevels_toggled_handlers[rl])

    def on_serviceRunlevels_toggled(self, menuitem):
        rl = self.checkboxes_runlevels[menuitem]
        state = menuitem.get_active()

        if state:
            self.current_service.runlevels.add(rl)
        else:
            self.current_service.runlevels.discard(rl)

    def on_service_selected(self, treeview=None, service=None, *args):
        self.current_service = service
        if service:
            GUIServicesDetailsPainter(self, service).paint_details()
        if isinstance(service, SystemDService):
            self.servicesDetailsNotebook.set_current_page(
                    self.SVC_PAGE_SYSTEMD)
        elif isinstance(service, services.SysVService):
            self.servicesDetailsNotebook.set_current_page(self.SVC_PAGE_SYSV)
            self._update_runlevel_menu()
        elif isinstance(service, services.XinetdService):
            self.servicesDetailsNotebook.set_current_page(self.SVC_PAGE_XINETD)
        else:
            self.servicesDetailsNotebook.set_current_page(self.SVC_PAGE_NONE)
        self._set_widgets_sensitivity()

    def _set_widgets_sensitivity(self):
        for widget in self._service_xml_widgets:
            self._set_service_widget_sensitive(widget, self.current_service)

    def _set_service_widget_sensitive(self, wname, service):
        try:
            w = getattr(self, wname)
        except AttributeError:
            return

        if wname.endswith("Button"):
            wname = wname[:-6]

        if not service:
            w.set_sensitive(False)
            return

        sensitive = True

        if wname in ("serviceEnable", "serviceDisable"):
            if isinstance(service, SystemDService):
                sensitive = False
            else:
                is_enabled = service.get_enabled()

                if is_enabled in (SVC_ENABLED_REFRESHING, SVC_ENABLED_ERROR):
                    sensitive = False
                elif wname == "serviceEnable":
                    sensitive = is_enabled not in (SVC_ENABLED_YES, 'enabled')
                elif wname == "serviceDisable":
                    sensitive = is_enabled not in (SVC_ENABLED_NO, 'disabled')
        elif wname in ("serviceCustomize", "serviceStart", "serviceStop",
                       "serviceRestart"):
            if isinstance(service, services.SysVService):
                if service.status == SVC_STATUS_REFRESHING:
                    sensitive = False
                elif wname == "serviceCustomize":
                    sensitive = True
                elif wname == "serviceStart":
                    sensitive = service.status != SVC_STATUS_RUNNING
                elif wname == "serviceStop":
                    sensitive = service.status in (SVC_STATUS_UNKNOWN,
                            SVC_STATUS_RUNNING)
                elif wname == "serviceRestart":
                    sensitive = service.status == SVC_STATUS_RUNNING
            elif isinstance(service, SystemDService):
                astate = service.ActiveState
                if wname == 'serviceCustomize':
                    sensitive = False
                elif wname == 'serviceStart':
                    sensitive = service.CanStart and astate != 'active'
                elif wname == 'serviceStop':
                    sensitive = service.CanStop and astate != 'inactive'
                elif wname == 'serviceRestart':
                    sensitive = (service.CanStart and service.CanStop and
                            astate != 'inactive')
            else:
                sensitive = False
        else:
            sensitive = True

        w.set_sensitive(sensitive)

    def on_services_changed(self, herder, change, service):
        if not self.inhibit_recursion:
            self.inhibit_recursion = True
            while gtk.events_pending():
                gtk.main_iteration()
            self.inhibit_recursion = False
        if change == SVC_ADDED:
            self.on_service_added(service)
        elif change == SVC_DELETED:
            self.on_service_deleted(service)
        elif change == SVC_CONF_UPDATING:
            self.on_service_conf_updating(service)
        elif change == SVC_CONF_CHANGED:
            self.on_service_conf_changed(service)
        elif change == SVC_STATUS_UPDATING:
            self.on_service_status_updating(service)
        elif change == SVC_STATUS_CHANGED:
            self.on_service_status_changed(service)
        elif change == SVC_HERDER_READY:
            self.on_service_herder_ready(herder)
        else:
            raise KeyError("change: %d", change)

    def _update_xinetd_service_entries(self):
        for (service, painter) in self.service_painters.iteritems():
            if isinstance(service, services.XinetdService):
                painter.paint()

    def on_service_added(self, service):
        # eats legacy SysVService, XinetdService and new-style SystemDService
        # instances

        self.servicesTreeStore.add_service(service)
        self.service_painters[service] = GUIServiceEntryPainter(self, service)
        self.service_painters[service].paint()
        if service.name == "xinetd" and isinstance(service,
                (SystemDService, services.SysVService)):
            self.xinetd_service = service
            if isinstance(self.current_service, services.XinetdService):
                GUIServicesDetailsPainter(self, self.current_service).\
                        paint_details()
            self._update_xinetd_service_entries()

        if not self._enabled:
            iter = self.servicesTreeStore.get_iter_first()
            if iter:
                path = self.servicesTreeStore.get_path(iter)
                self.servicesTreeView.scroll_to_cell(path)

    def find_new_service_path_to_select(self):

        # determine which service to select now

        path_to_select = None

        (model, current_iter) = self.servicesTreeView.selection.get_selected()

        if current_iter:

            # find next service in list

            current_path = model.get_path(current_iter)

            next_iter = model.iter_next(current_iter)
            if next_iter:
                path_to_select = model.get_path(next_iter)
            else:

                # find previous service in list

                iter = model.get_iter_first()
                prev_iter = None
                while iter and model.get_path(iter) != current_path:
                    new_iter = model.iter_next(iter)
                    if new_iter:
                        prev_iter = iter
                        iter = new_iter
                    else:
                        prev_iter = None
                        break
                if prev_iter:
                    path_to_select = model.get_path(prev_iter)
        return path_to_select

    def on_service_deleted(self, service):
        if service == self.current_service:
            path_to_select = self.find_new_service_path_to_select()
            if path_to_select:
                self.servicesTreeView.selection.select_path(path_to_select)
            else:
                self.servicesTreeView.selection.unselect_all()

            # self.on_service_selected (service = self.find_new_service_to_select ())

        self.servicesTreeStore.delete_service(service)

        try:
            del self.service_painters[service]
        except KeyError:
            pass

        if service == self.xinetd_service:
            self.xinetd_service = None
            if isinstance(self.current_service, services.XinetdService):
                GUIServicesDetailsPainter(self, self.current_service).\
                        paint_details()
            self._update_xinetd_service_entries()

    def on_service_conf_updating(self, service):
        self.service_painters[service].paint()
        self._set_widgets_sensitivity()

    def on_unit_properties_changed(self, unit, interface, changed_properties,
            invalidated_properties):
        self.on_service_conf_changed(unit)
        self.on_service_status_changed(unit)

    def on_service_conf_changed(self, service):
        self.service_painters[service].paint()
        if service == self.current_service:
            GUIServicesDetailsPainter(self, service).paint_details()
            if isinstance(service, services.SysVService):
                self._update_runlevel_menu()
        self._set_widgets_sensitivity()

    def on_service_status_updating(self, service):
        self.service_painters[service].paint()
        self._set_widgets_sensitivity()

    def on_service_status_changed(self, service):
        if self.service_painters.has_key(service):
            self.service_painters[service].paint()
            if service == self.current_service:
                GUIServicesDetailsPainter(self, service).paint_details()
            if service == self.xinetd_service:
                if isinstance(self.current_service, services.XinetdService):
                    GUIServicesDetailsPainter(self, self.current_service).\
                            paint_details()
                self._update_xinetd_service_entries()
        else:

            # service might have been deleted

            pass

        self._set_widgets_sensitivity()

    def on_service_herder_ready(self, herder):
        self.serviceherders_ready.add(herder)
        self.enable_on_discovery_finished()

    def disable(self):
        self._enabled = False
        self.servicesListDetailsPaned.set_sensitive(False)
        self.mainWindow.window.set_cursor(self.busy_cursor)

    def enable(self):

        # if the list isn't empty, select the first entry

        iter = self.servicesTreeStore.get_iter_first()
        if iter != None:
            self.servicesTreeView.selection.select_iter(iter)

            self.servicesListDetailsPaned.set_sensitive(True)
            self.mainWindow.window.set_cursor(None)
            self._enabled = True


class ServiceRunlevelDialog(GladeController):

    _xml_widgets = (
        "serviceRunlevelsDialog",
        "serviceRunlevelsExplanationLabel",
        "serviceRunlevel2Button",
        "serviceRunlevel3Button",
        "serviceRunlevel4Button",
        "serviceRunlevel5Button",
        )

    def __init__(self, xml, main_window, service):
        super(ServiceRunlevelDialog, self).__init__(xml)
        self.service = service

        self.runlevels_checkboxes = {
            2: self.serviceRunlevel2Button,
            3: self.serviceRunlevel3Button,
            4: self.serviceRunlevel4Button,
            5: self.serviceRunlevel5Button,
            }

        self.serviceRunlevelsDialog.set_transient_for(main_window)

        self.serviceRunlevelsExplanationLabel.set_markup(
                _("Enable the <b>%(service)s</b> service in these "
                  "runlevels:") % {"service": service.name})

        for i in xrange(2, 6):
            cb = self.runlevels_checkboxes[i]
            if i in service.runlevels:
                cb.set_active(True)
            else:
                cb.set_active(False)

    def run(self):
        response = self.serviceRunlevelsDialog.run()
        if response == gtk.RESPONSE_OK:
            enabled_runlevels = set()
            for i in xrange(2, 6):
                cb = self.runlevels_checkboxes[i]
                if cb.get_active():
                    enabled_runlevels.add(i)
            self.service.runlevels = enabled_runlevels
        self.serviceRunlevelsDialog.destroy()


class MainWindow(GladeController):

    _xml_widgets = (
        # "serviceEnableButton",
        # "serviceEnable_popupMenu",
        "serviceRunlevelsDialog",
        "helpContents",
        "helpContentsButton",
        "servicesDetailsNotebook",
        "sysVServiceExplanationLabel",
        "xinetdServiceExplanationLabel",
        "aboutDialog",
        )

    def __init__(self, mainloop, serviceherders, systemd_manager):
        if os.access("system-config-services.glade", os.R_OK):
            fd = open("system-config-services.glade", "r")
        else:
            fd = open(os.path.join(config.datadir,
                      "system-config-services.glade"), "r")

        self.xmlbuf = fd.read()
        fd.close()

        xml = gtk.glade.xml_new_from_buffer(self.xmlbuf, len(self.xmlbuf),
                domain=config.domain)

        super(MainWindow, self).__init__(xml)

        self.mainloop = mainloop
        self.maincontext = mainloop.get_context()

        self.servicesList = GUIServicesList(xml=self.xml,
                serviceherders=serviceherders, systemd_manager=systemd_manager)

        self.toplevel = xml.get_widget("mainWindow")
        self.toplevel.connect("delete_event", self.on_programQuit_activate)

        # enable service popup menu
        # self.serviceEnableButton.set_menu (self.serviceEnable_popupMenu)

        # the tabs are visible in the glade file to improve maintainability ...
        # ... so we hide them

        self.servicesDetailsNotebook.set_show_tabs(False)

        self.aboutDialog.set_name(config.name)
        self.aboutDialog.set_version(config.version)
        self.aboutDialog.set_transient_for(self.toplevel)

        slip.gtk.label_set_autowrap(self.sysVServiceExplanationLabel)
        slip.gtk.label_set_autowrap(self.xinetdServiceExplanationLabel)

    # ## Callbacks

    def on_programQuit_activate(self, *args):
        self.mainloop.quit()

    def _xinetd_reload(self, service):
        xinetd_service = self.servicesList.xinetd_service
        if xinetd_service and xinetd_service.status == SVC_STATUS_RUNNING:
            while service.is_chkconfig_running():
                while self.maincontext.pending():
                    self.maincontext.iteration()
            xinetd_service.reload()

    def on_serviceEnable_activate(self, *args):
        service = self.servicesList.current_service
        if service:
            service.enable()
            if isinstance(service, services.XinetdService):
                self._xinetd_reload(service)

    # def on_serviceEnable_show_menu (self, *args):
    #    print "MainWindow.on_serviceEnable_show_menu (%s)" % ', '.join (map (lambda x: str(x), args))

    def on_serviceDisable_activate(self, *args):
        service = self.servicesList.current_service
        if service:
            service.disable()
            if isinstance(service, services.XinetdService):
                self._xinetd_reload(service)

    def on_serviceCustomize_activate(self, *args):
        service = self.servicesList.current_service
        if service:
            xml = gtk.glade.xml_new_from_buffer(self.xmlbuf,
                    len(self.xmlbuf), domain=config.domain)
            ServiceRunlevelDialog(xml, self.toplevel, service).run()

    def on_serviceStart_activate(self, *args):
        service = self.servicesList.current_service
        if service:
            service.start()

    def on_serviceStop_activate(self, *args):
        service = self.servicesList.current_service
        if service:
            service.stop()

    def on_serviceRestart_activate(self, *args):
        service = self.servicesList.current_service
        if service:
            service.restart()

    def on_serviceInformation_activate(self, *args):
        print "MainWindow.on_serviceInformation_activate (%s)" % \
                ", ".join(map(lambda x: str(x), args))

    def on_helpContents_activate(self, *args):
        help_page = "ghelp:system-config-services"
        path = "/usr/bin/yelp"

        if not os.access(path, os.X_OK):
            d = gtk.MessageDialog(self.toplevel, 0, gtk.MESSAGE_WARNING,
                                  gtk.BUTTONS_CLOSE,
                                  _("The help viewer could not be found. To "
                                    "be able to view help, the 'yelp' package "
                                    "needs to be installed."))
            d.set_position(gtk.WIN_POS_CENTER)
            d.run()
            d.destroy()
            return

        pid = os.fork()
        if pid == 0:
            os.execv(path, (path, help_page))

    def on_helpAbout_activate(self, *args):
        self.aboutDialog.show()
        self.aboutDialog.window.raise_()

    def on_aboutDialog_close(self, *args):
        self.aboutDialog.hide()
        return True


class UIController(object):

    polkit_actions = ("org.fedoraproject.config.services.info",
                      "org.fedoraproject.config.services.manage")

    def __init__(self, use_dbus=None):
        """Initialize a UIController object.

use_dbus: Whether or not to access privileged functionality via the
          system-config-services DBus mechanism. Passing None means to check if
          the necessary PolicyKit authorizations are obtainable (in theory) and
          fall back to direct access if they are not."""

        global serviceherders, services

        self.mainloop = gobject.MainLoop()

        # We need DBus in all cases to access systemd
        import dbus.mainloop.glib
        import slip.dbus
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        bus = slip.dbus.SystemBus()

        if use_dbus == None:
            if slip.dbus.polkit.AreAuthorizationsObtainable(self.polkit_actions):
                use_dbus = True
            else:
                use_dbus = False

        if check_systemd_active():
            self.systemd_manager = systemd_manager = SystemDManager(bus,
                    use_polkit=use_dbus)
        else:
            self.systemd_manager = systemd_manager = None

        serviceherders = None
        services = None
        if use_dbus:
            (serviceherders, services) = self.dbus_init()
            if serviceherders and services:
                self.use_dbus = True
        else:
            (serviceherders, services) = self.direct_init()
            if serviceherders and services:
                self.use_dbus = False

        if not serviceherders or not services:
            if use_dbus != False:
                print >> sys.stderr, "Setting up DBus connection failed."
            if use_dbus != True:
                print >> sys.stderr, "Acquiring direct service control failed."
            print >> sys.stderr, "Exiting."
            sys.exit(1)

        if not systemd_manager:
            print >> sys.stdout, "Couldn't acquire connection to systemd. Falling back to legacy SysV scheme."
            herder_classes = serviceherders.herder_classes
        else:
            # filter out SysV service herder as systemd supplants its
            # functionality
            herder_classes = [ x for x in serviceherders.herder_classes
                    if "sysv" not in x.__name__.lower() ]

        self.serviceherders = []
        for cls in herder_classes:
            if not self.use_dbus:
                self.serviceherders.append(cls(mon=self._filemon))
            else:
                self.serviceherders.append(cls(bus=self._bus))

        self.mainWindow = MainWindow(mainloop=self.mainloop,
                                     serviceherders=self.serviceherders,
                                     systemd_manager=self.systemd_manager)

    def dbus_init(self):
        import dbus.mainloop.glib
        import slip.dbus
        import scservices.dbus.proxy.serviceherders as serviceherders
        import scservices.dbus.proxy.services as services
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self._bus = slip.dbus.SystemBus()
        return (serviceherders, services)

    def direct_init(self):
        import gamin
        import scservices.core.legacy.serviceherders as serviceherders
        import scservices.core.legacy.services as services
        self._filemon = gamin.WatchMonitor()
        self._filemon_fd = self._filemon.get_fd()
        gobject.io_add_watch(self._filemon_fd, gobject.IO_IN |
                              gobject.IO_PRI, self._mon_handle_events)
        return (serviceherders, services)

    def _mon_handle_events(self, source, condition, data=None):
        self._filemon.handle_events()
        return True

    def run(self):
        try:
            self.mainWindow.toplevel.show()
            self.mainloop.run()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    if "--no-dbus" in sys.argv[1:]:
        use_dbus = False
    elif "--dbus" in sys.argv[1:]:
        use_dbus = True
    else:
        use_dbus = None

    UIController(use_dbus=use_dbus).run()
