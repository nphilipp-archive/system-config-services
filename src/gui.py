#!/usr/bin/python
# -*- coding: utf-8 -*-
""" system-config-services: This module contains GUI functionality. """
# gui.py
# Copyright © 2008 Red Hat, Inc.
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

import config

import os.path
import gobject
import gamin
import gtk
import gtk.glade

import gtk_label_autowrap

import gettext
gettext.install ('system-config-services')

import serviceherders
from serviceherders import SVC_ADDED, SVC_DELETED, SVC_CONF_UPDATING, SVC_CONF_CHANGED, SVC_STATUS_UPDATING, SVC_STATUS_CHANGED
import services
from services import SVC_STATUS_REFRESHING, SVC_STATUS_UNKNOWN, SVC_STATUS_STOPPED, SVC_STATUS_RUNNING, SVC_STATUS_DEAD, SVC_ENABLED_REFRESHING, SVC_ENABLED_YES, SVC_ENABLED_NO, SVC_ENABLED_CUSTOM

gtk.glade.bindtextdomain (config.domain)

SVC_COL_SVC_OBJECT = 0
SVC_COL_ENABLED = 1
SVC_COL_STATUS = 2
SVC_COL_NAME = 3
SVC_COL_REMARK = 4
SVC_COL_LAST = 5

##############################################################################

class GUIServicesListStore (gtk.ListStore):
    col_types = {
        SVC_COL_SVC_OBJECT:     gobject.TYPE_PYOBJECT,
        SVC_COL_ENABLED:        gobject.TYPE_STRING,
        SVC_COL_STATUS:         gobject.TYPE_STRING,
        SVC_COL_NAME:           gobject.TYPE_STRING,
        SVC_COL_REMARK:         gobject.TYPE_STRING,
    }

    def __init__ (self):
        col_types = []
        for col in xrange (SVC_COL_LAST):
            col_types.append (self.col_types [col])
        gtk.ListStore.__init__ (self, *col_types)
        self.set_default_sort_func (self._sort_by_name)
        self.set_sort_func (SVC_COL_NAME, self._sort_by_name)
        self.set_sort_column_id (SVC_COL_NAME, gtk.SORT_ASCENDING)

        self.service_iters = {}

    def _sort_by_name (self, treemodel, iter1, iter2, user_data = None):
        name1 = self.get (iter1, SVC_COL_NAME)
        name2 = self.get (iter2, SVC_COL_NAME)

        return name1 < name2 and -1 or name1 > name2 and 1 or 0

    def add_service (self, service):
        iter = self.append (None)
        self.set (iter, SVC_COL_SVC_OBJECT, service, SVC_COL_NAME, service.name)
        self.service_iters[service] = iter

    def _delete_svc_callback (self, model, path, iter, service):
        row_service = self.get_value (iter, SVC_COL_SVC_OBJECT)

        if row_service == service:
            self.remove (iter)
            return True

        return False

    def delete_service (self, service):
        self.foreach (self._delete_svc_callback, service)
        del self.service_iters[service]

##############################################################################

class GUIServicesTreeView (gtk.TreeView):
    COL_TITLE = 0
    COL_CELL_RENDERER = 1
    COL_ATTRNAME = 2
    COL_CLICKABLE = 3
    COL_EXPAND = 4
    COL_RESIZABLE = 5
    COL_FIXED_WIDTH = 6
    COL_LAST = 7

    col_spec = {
        SVC_COL_ENABLED:    ["", gtk.CellRendererPixbuf, "stock_id", False, False, False, gtk.icon_size_lookup (gtk.ICON_SIZE_MENU)[0]],
        SVC_COL_STATUS:     ["", gtk.CellRendererPixbuf, "stock_id", False, False, False, gtk.icon_size_lookup (gtk.ICON_SIZE_MENU)[0]],
        SVC_COL_NAME:       [_("Name"), gtk.CellRendererText, "text", True, True, True, None],
        SVC_COL_REMARK:     [_("Remarks"), gtk.CellRendererText, "text", True, True, True, None],
    }

    def __init__ (self):
        self.model = GUIServicesListStore ()

        gtk.TreeView.__init__ (self, model = self.model) 

        self.selection = self.get_selection ()

        for column in xrange (1, SVC_COL_LAST):
            title = self.col_spec[column][self.COL_TITLE]
            cell_renderer = self.col_spec[column][self.COL_CELL_RENDERER] ()

            attrname = self.col_spec[column][self.COL_ATTRNAME]
            if attrname:
                col = gtk.TreeViewColumn (title, cell_renderer, **{attrname: column})
            else:
                col = gtk.TreeViewColumn (title, cell_renderer)

            clickable = self.col_spec[column][self.COL_CLICKABLE]
            expand = self.col_spec[column][self.COL_EXPAND]
            resizable = self.col_spec[column][self.COL_RESIZABLE]
            properties = {'clickable': clickable, 'expand': expand, 'resizable': resizable}
            fixed_width = self.col_spec[column][self.COL_FIXED_WIDTH]
            if fixed_width != None:
                # add some padding
                fixed_width += 5
                properties['fixed-width'] = fixed_width

            col.set_properties (**properties)
            self.append_column (col)

        self.selection.set_mode (gtk.SELECTION_SINGLE)
        self.selection.connect ('changed', self.on_selection_changed)

    def on_selection_changed (self, selection, *p):
        selected = selection.get_selected ()
        if selected == None:
            self.emit ('service-selected', None)
            return
        (model, iter) = selected
        if iter == None:
            self.emit ('service-selected', None)
            return
        service = model.get (iter, SVC_COL_SVC_OBJECT)
        self.emit ('service-selected', service[0])

_service_selected_signal = gobject.signal_new ('service-selected', GUIServicesTreeView, gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, ))

##############################################################################

_enabled_stock_id = {
        SVC_ENABLED_REFRESHING: gtk.STOCK_REFRESH,
        SVC_ENABLED_YES: gtk.STOCK_YES,
        SVC_ENABLED_NO: gtk.STOCK_NO,
        SVC_ENABLED_CUSTOM: gtk.STOCK_PREFERENCES,
        }

_enabled_text = {
        SVC_ENABLED_REFRESHING: _("This service is being refreshed right now."),
        SVC_ENABLED_YES: _("This service is enabled."),
        SVC_ENABLED_NO: _("This service is disabled."),
        SVC_ENABLED_CUSTOM: _("This service is enabled in runlevels: %(runlevels)s"),
        }

##############################################################################

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

##############################################################################

class GladeController (object):
    _xml_widgets = []

    def __init__ (self, xml):
        self.xml = xml

        for wname in self._xml_widgets:
            w = xml.get_widget (wname)
            if w:
                setattr (self, wname, w)
            else:
                raise KeyError (wname)

        # connect defined signals with callback methods
        xml.signal_autoconnect (self)

##############################################################################

class GUIServicesDetailsPainter (GladeController):
    """Services details painter singleton factory"""

    _classes = None
    _classes_objects = { }

    def __new__ (cls, serviceslist, service, *p, **k):
        if GUIServicesDetailsPainter._classes == None:
            GUIServicesDetailsPainter._classes = {
                services.SysVService: GUISysVServicesDetailsPainter,
                services.XinetdService: GUIXinetdServicesDetailsPainter,
            }

        painter_class = None

        for svc_cls, ptr_cls in GUIServicesDetailsPainter._classes.iteritems ():
            if isinstance (service, svc_cls):
                painter_class = ptr_cls
                break

        if not painter_class:
            raise TypeError ('service: %s' % service)

        if not GUIServicesDetailsPainter._classes_objects.has_key (painter_class):
            GUIServicesDetailsPainter._classes_objects[painter_class] = \
                object.__new__ (painter_class)

        return GUIServicesDetailsPainter._classes_objects[painter_class]

    def __init__ (self, serviceslist, service):
        super (GUIServicesDetailsPainter, self).__init__ (serviceslist.xml)
        self.serviceslist = serviceslist
        self.service = service

    def paint_details (self):
        raise NotImplementedError

##############################################################################

class GUISysVServicesDetailsPainter (GUIServicesDetailsPainter):
    """Details painter for SysV services"""
    _xml_widgets = (
        'sysVServiceExplanationLabel',
        'sysVServiceEnabledIcon',
        'sysVServiceEnabledLabel',
        'sysVServiceStatusIcon',
        'sysVServiceStatusLabel',
        'sysVServiceDescriptionTextView'
    )

    def __init__ (self, serviceslist, service):
        super (GUISysVServicesDetailsPainter, self).__init__ (serviceslist, service)

    def paint_details (self):
        self.sysVServiceExplanationLabel.set_markup (_("The <b>%(servicename)s</b> service is started once, usually when the system is booted, runs in the background and wakes up when needed.") % {'servicename': self.service.name})

        enabled = self.service.get_enabled ()
        self.sysVServiceEnabledIcon.set_from_stock (_enabled_stock_id[enabled],
                                                    gtk.ICON_SIZE_MENU)
        if enabled == SVC_ENABLED_CUSTOM:
            runlevels = ", ".join (map (str, sorted (self.service.runlevels)))
            self.sysVServiceEnabledLabel.set_text (_enabled_text[enabled] % {'runlevels': runlevels})
        else:
            self.sysVServiceEnabledLabel.set_text (_enabled_text[enabled])

        if self.service.status_updates_running > 0:
            self.sysVServiceStatusIcon.set_from_stock (gtk.STOCK_REFRESH,
                                                       gtk.ICON_SIZE_MENU)
            self.sysVServiceStatusLabel.set_text (_("This service is updated currently."))
        else:
            stock_icon_id = _status_stock_id [self.service.status]
            self.sysVServiceStatusIcon.set_from_stock (stock_icon_id,
                                                       gtk.ICON_SIZE_MENU)
            self.sysVServiceStatusLabel.set_text (_status_text [self.service.status])

        if self.service.info.description:
            self.sysVServiceDescriptionTextView.get_buffer ().set_text (self.service.info.description)
        else:
            self.sysVServiceDescriptionTextView.get_buffer ().set_text ("")

##############################################################################

class GUIXinetdServicesDetailsPainter (GUIServicesDetailsPainter):
    _xml_widgets = (
        'xinetdServiceExplanationLabel',
        'xinetdServiceEnabledIcon',
        'xinetdServiceEnabledLabel',
        'xinetdServiceDescriptionTextView'
    )

    def __init__ (self, serviceslist, service):
        super (GUIXinetdServicesDetailsPainter, self).__init__ (serviceslist, service)

    def paint_details (self):
        self.xinetdServiceExplanationLabel.set_markup (_("The <b>%(servicename)s</b> service will be started on demand by the xinetd service and ends when it has got nothing more to do.") % {'servicename': self.service.name})

        enabled = self.service.get_enabled ()
        xinetd_service = self.serviceslist.xinetd_service
        if enabled == SVC_ENABLED_YES and not xinetd_service:
            self.xinetdServiceEnabledIcon.set_from_stock (
                    gtk.STOCK_DIALOG_WARNING,
                    gtk.ICON_SIZE_MENU
                    )
            self.xinetdServiceEnabledLabel.set_markup (_("This service is enabled, but the <b>xinetd</b> package is not installed. This service does not work without it."))
        elif enabled == SVC_ENABLED_YES and xinetd_service.status != SVC_STATUS_RUNNING:
            self.xinetdServiceEnabledIcon.set_from_stock (
                    gtk.STOCK_DIALOG_WARNING,
                    gtk.ICON_SIZE_MENU
                    )
            self.xinetdServiceEnabledLabel.set_markup (_("This service is enabled, but the <b>xinetd</b> service is not running. This service does not work without it."))
        else:

            self.xinetdServiceEnabledIcon.set_from_stock (
                    _enabled_stock_id[enabled],
                    gtk.ICON_SIZE_MENU
                    )
            self.xinetdServiceEnabledLabel.set_text (_enabled_text[enabled])

        if self.service.info.description:
            self.xinetdServiceDescriptionTextView.get_buffer ().set_text (self.service.info.description)
        else:
            self.xinetdServiceDescriptionTextView.get_buffer ().set_text ("")

##############################################################################

class GUIServiceEntryPainter (object):
    def __new__ (cls, serviceslist, service, *p, **k):
        if isinstance (service, services.SysVService):
            return object.__new__ (GUISysVServiceEntryPainter)
        elif isinstance (service, services.XinetdService):
            return object.__new__ (GUIXinetdServiceEntryPainter)
        else:
            raise TypeError ('service')

    def __init__ (self, serviceslist, service):
        self.serviceslist = serviceslist
        self.treestore = serviceslist.servicesTreeStore
        self.service = service

    def paint (self):
        raise NotImplementedError

##############################################################################

class GUISysVServiceEntryPainter (GUIServiceEntryPainter):
    def paint (self):
        iter = self.treestore.service_iters[self.service]
        self.treestore.set (iter, SVC_COL_ENABLED, _enabled_stock_id[self.service.get_enabled ()])
        self.treestore.set (iter, SVC_COL_STATUS, _status_stock_id[self.service.status])
        if self.service.info.shortdescription:
            self.treestore.set (iter, SVC_COL_REMARK, self.service.info.shortdescription)


##############################################################################

class GUIXinetdServiceEntryPainter (GUIServiceEntryPainter):
    def paint (self):
        iter = self.treestore.service_iters[self.service]
        enabled = self.service.get_enabled ()
        xinetd_service = self.serviceslist.xinetd_service
        if enabled == SVC_ENABLED_YES and (not xinetd_service \
                or xinetd_service.status != SVC_STATUS_RUNNING):
            self.treestore.set (iter, SVC_COL_ENABLED, gtk.STOCK_DIALOG_WARNING)
        else:
            self.treestore.set (iter, SVC_COL_ENABLED, _enabled_stock_id[self.service.get_enabled ()])
        self.treestore.set (iter, SVC_COL_STATUS, None)

##############################################################################

class GUIServicesList (GladeController):
    SVC_PAGE_NONE = 0
    SVC_PAGE_SYSV = 1
    SVC_PAGE_XINETD = 2

    _service_xml_widgets = (
            'serviceEnable',
            'serviceDisable',
            'serviceCustomize',
            'serviceStart',
            'serviceStop',
            'serviceRestart',
            #'serviceInformation',
            'serviceEnableButton',
            'serviceDisableButton',
            'serviceCustomizeButton',
            'serviceStartButton',
            'serviceStopButton',
            'serviceRestartButton',
            #'serviceInformationButton',
            )

    _xml_widgets = _service_xml_widgets + (
            'servicesScrolledWindow',
            'servicesDetailsNotebook',
            'serviceRunlevel2',
            'serviceRunlevel3',
            'serviceRunlevel4',
            'serviceRunlevel5',
            )

    def __init__ (self, xml, serviceherders):
        self.current_service = None
        self.xinetd_service = None
        self.service_painters = {}

        super (GUIServicesList, self).__init__ (xml)
        self.serviceherders = serviceherders

        self.runlevels_checkboxes = {
                2: self.serviceRunlevel2,
                3: self.serviceRunlevel3,
                4: self.serviceRunlevel4,
                5: self.serviceRunlevel5
                }

        self.checkboxes_runlevels = {}
        # connect these signal handlers here so we can block/unblock them later
        self.runlevels_toggled_handlers = {}
        for rl, cb in self.runlevels_checkboxes.iteritems ():
            self.checkboxes_runlevels[cb] = rl
            self.runlevels_toggled_handlers[rl] = cb.connect ("toggled", self.on_serviceRunlevels_toggled)

        servicesTreeView = xml.get_widget ('servicesTreeView')
        self.servicesScrolledWindow.remove (servicesTreeView)

        self.servicesTreeView = GUIServicesTreeView ()
        self.servicesTreeView.show ()
        self.servicesTreeView.set_rules_hint (True)
        self.servicesTreeView.connect ('service-selected', self.on_service_selected)

        self.servicesTreeStore = self.servicesTreeView.model

        self.servicesScrolledWindow.add (self.servicesTreeView)

        self.on_service_selected ()

        for herder in serviceherders:
            herder.subscribe (self.on_services_changed)

    def _update_runlevel_menu (self):
        for rl in xrange (2, 6):
            self.runlevels_checkboxes[rl].handler_block (self.runlevels_toggled_handlers[rl])
            self.runlevels_checkboxes[rl].set_active (rl in self.current_service.runlevels)
            self.runlevels_checkboxes[rl].handler_unblock (self.runlevels_toggled_handlers[rl])

    def on_serviceRunlevels_toggled (self, menuitem):
        rl = self.checkboxes_runlevels[menuitem]
        state = menuitem.get_active ()

        if state:
            self.current_service.runlevels.add (rl)
        else:
            self.current_service.runlevels.discard (rl)

    def on_serviceCustomize_menu_unmap_event (self, menu, event):
        if self.current_service.is_dirty ():
            self.current_service.save ()

    def on_service_selected (self, treeview = None, service = None, *args):
        self.current_service = service
        if service:
            GUIServicesDetailsPainter (self, service).paint_details ()
        if isinstance (service, services.SysVService):
            self.servicesDetailsNotebook.set_current_page (self.SVC_PAGE_SYSV)
            self._update_runlevel_menu ()
        elif isinstance (service, services.XinetdService):
            self.servicesDetailsNotebook.set_current_page (self.SVC_PAGE_XINETD)
        else:
            self.servicesDetailsNotebook.set_current_page (self.SVC_PAGE_NONE)
        self._set_widgets_sensitivity ()

    def _set_widgets_sensitivity (self):
        map (lambda x: self._set_service_widget_sensitive (x, self.current_service),
             self._service_xml_widgets)

    def _set_service_widget_sensitive (self, wname, service):
        try:
            w = getattr (self, wname)
        except AttributeError:
            return

        if wname.endswith ('Button'):
            wname = wname[:-6]

        if not service:
            w.set_sensitive (False)
            return

        sensitive = True

        if wname in ('serviceEnable', 'serviceDisable'):
            is_enabled = service.get_enabled ()
            if is_enabled == SVC_ENABLED_REFRESHING:
                sensitive = False
            elif wname == 'serviceEnable':
                sensitive = (is_enabled != SVC_ENABLED_YES)
            elif wname == 'serviceDisable':
                sensitive = (is_enabled != SVC_ENABLED_NO)
        elif wname in ('serviceCustomize', 'serviceStart', 'serviceStop', 'serviceRestart'):
            if isinstance (service, services.SysVService):
                if service.status == SVC_STATUS_REFRESHING:
                    sensitive = False
                elif wname == 'serviceCustomize':
                    sensitive = True
                elif wname == 'serviceStart':
                    sensitive = (service.status != SVC_STATUS_RUNNING)
                elif wname == 'serviceStop':
                    sensitive = (service.status in (SVC_STATUS_UNKNOWN, SVC_STATUS_RUNNING))
                elif wname == 'serviceRestart':
                    sensitive = (service.status == SVC_STATUS_RUNNING)
            else:
                sensitive = False
        else:
            sensitive = True

        w.set_sensitive (sensitive)

    def on_services_changed (self, change, service):
        if change == SVC_ADDED:
            self.on_service_added (service)
        elif change == SVC_DELETED:
            self.on_service_deleted (service)
        elif change == SVC_CONF_UPDATING:
            self.on_service_conf_updating (service)
        elif change == SVC_CONF_CHANGED:
            self.on_service_conf_changed (service)
        elif change == SVC_STATUS_UPDATING:
            self.on_service_status_updating (service)
        elif change == SVC_STATUS_CHANGED:
            self.on_service_status_changed (service)
        else:
            raise KeyError ("change: %d", change)

    def _update_xinetd_service_entries (self):
        for service, painter in self.service_painters.iteritems ():
            if isinstance (service, services.XinetdService):
                painter.paint ()

    def on_service_added (self, service):
        self.servicesTreeStore.add_service (service)
        self.service_painters[service] = GUIServiceEntryPainter (self, service)
        self.service_painters[service].paint ()
        if service.name == "xinetd" and isinstance (service, services.SysVService):
            self.xinetd_service = service
            if isinstance (self.current_service, services.XinetdService):
                GUIServicesDetailsPainter (self, self.current_service).paint_details ()
            self._update_xinetd_service_entries ()

    def on_service_deleted (self, service):
        self.servicesTreeStore.delete_service (service)
        if service == self.current_service:
            self.on_service_selected (service = None)
        try:
            del self.service_painters[service]
        except KeyError:
            pass
        if service == self.xinetd_service:
            self.xinetd_service = None
            if isinstance (self.current_service, services.XinetdService):
                GUIServicesDetailsPainter (self, self.current_service).paint_details ()
            self._update_xinetd_service_entries ()

    def on_service_conf_updating (self, service):
        self.service_painters[service].paint ()
        self._set_widgets_sensitivity ()

    def on_service_conf_changed (self, service):
        self.service_painters[service].paint ()
        if service == self.current_service:
            GUIServicesDetailsPainter (self, service).paint_details ()
            if isinstance (service, services.SysVService):
                self._update_runlevel_menu ()
        self._set_widgets_sensitivity ()

    def on_service_status_updating (self, service):
        self.service_painters[service].paint ()
        self._set_widgets_sensitivity ()

    def on_service_status_changed (self, service):
        if self.service_painters.has_key (service):
            self.service_painters[service].paint ()
            if service == self.current_service:
                GUIServicesDetailsPainter (self, service).paint_details ()
            if service == self.xinetd_service:
                if isinstance (self.current_service, services.XinetdService):
                    GUIServicesDetailsPainter (self, self.current_service).paint_details ()
                self._update_xinetd_service_entries ()
        else:
            # service might have been deleted
            pass
        self._set_widgets_sensitivity ()

##############################################################################

class ServiceRunlevelDialog (GladeController):
    _xml_widgets = (
            'serviceRunlevelsDialog',
            'serviceRunlevelsExplanationLabel',
            'serviceRunlevel2Button',
            'serviceRunlevel3Button',
            'serviceRunlevel4Button',
            'serviceRunlevel5Button',
            )

    def __init__ (self, xml, main_window, service):
        super (ServiceRunlevelDialog, self).__init__ (xml)
        self.service = service

        self.runlevels_checkboxes = {
                2: self.serviceRunlevel2Button,
                3: self.serviceRunlevel3Button,
                4: self.serviceRunlevel4Button,
                5: self.serviceRunlevel5Button
                }

        self.serviceRunlevelsDialog.set_transient_for (main_window)

        self.serviceRunlevelsExplanationLabel.set_markup (_("Enable the <b>%(service)s</b> service in these runlevels:") % {'service': service.name})

        for i in xrange (2, 6):
            cb = self.runlevels_checkboxes[i]
            if i in service.runlevels:
                cb.set_active (True)
            else:
                cb.set_active (False)

    def run (self):
        response = self.serviceRunlevelsDialog.run ()
        if response == gtk.RESPONSE_OK:
            enabled_runlevels = set ()
            for i in xrange (2, 6):
                cb = self.runlevels_checkboxes[i]
                if cb.get_active ():
                    enabled_runlevels.add (i)
            self.service.runlevels = enabled_runlevels
            self.service.save ()
        self.serviceRunlevelsDialog.destroy ()

##############################################################################

class MainWindow (GladeController):
    _xml_widgets = (
            #'serviceEnableButton',
            #'serviceEnable_popupMenu',
            'serviceRunlevelsDialog',
            'helpContents',
            'helpContentsButton',
            'servicesDetailsNotebook',
            'sysVServiceExplanationLabel',
            'xinetdServiceExplanationLabel',
            'aboutDialog'
            )

    def __init__ (self, serviceherders):
        if os.access ("system-config-services.glade", os.R_OK):
            fd = open ("system-config-services.glade", "r")
        else:
            fd = open (os.path.join (config.datadir, "system-config-services.glade"), "r")

        self.xmlbuf = fd.read ()
        fd.close ()

        xml = gtk.glade.xml_new_from_buffer (self.xmlbuf, len (self.xmlbuf), domain = config.domain)

        super (MainWindow, self).__init__ (xml)

        self.servicesList = GUIServicesList (xml = self.xml, serviceherders = serviceherders)

        self.toplevel = xml.get_widget ("mainWindow")
        self.toplevel.connect ('delete_event', gtk.main_quit)

        # enable service popup menu
        #self.serviceEnableButton.set_menu (self.serviceEnable_popupMenu)

        # the tabs are visible in the glade file to improve maintainability ...
        # ... so we hide them
        self.servicesDetailsNotebook.set_show_tabs (False)

        self.aboutDialog.set_name (config.name)
        self.aboutDialog.set_version (config.version)

        gtk_label_autowrap.set_autowrap (self.sysVServiceExplanationLabel)
        gtk_label_autowrap.set_autowrap (self.xinetdServiceExplanationLabel)

    ### Callbacks

    def on_programQuit_activate (self, *args):
        gtk.main_quit ()

    def _xinetd_reload (self, service):
        xinetd_service = self.servicesList.xinetd_service
        if xinetd_service and xinetd_service.status == SVC_STATUS_RUNNING:
            while service.is_chkconfig_running ():
                while gtk.events_pending ():
                    gtk.main_iteration ()
            xinetd_service.reload ()


    def on_serviceEnable_activate (self, *args):
        service = self.servicesList.current_service
        if service:
            service.enable ()
            if isinstance (service, services.XinetdService):
                self._xinetd_reload (service)

    #def on_serviceEnable_show_menu (self, *args):
    #    print "MainWindow.on_serviceEnable_show_menu (%s)" % ', '.join (map (lambda x: str(x), args))

    def on_serviceDisable_activate (self, *args):
        service = self.servicesList.current_service
        if service:
            service.disable ()
            if isinstance (service, services.XinetdService):
                self._xinetd_reload (service)

    def on_serviceCustomize_activate (self, *args):
        service = self.servicesList.current_service
        if service:
            xml = gtk.glade.xml_new_from_buffer (self.xmlbuf, len (self.xmlbuf), domain = config.domain)
            ServiceRunlevelDialog (xml, self.toplevel, service).run ()

    def on_serviceStart_activate (self, *args):
        service = self.servicesList.current_service
        if service:
            service.start ()

    def on_serviceStop_activate (self, *args):
        service = self.servicesList.current_service
        if service:
            service.stop ()

    def on_serviceRestart_activate (self, *args):
        service = self.servicesList.current_service
        if service:
            service.restart ()

    def on_serviceInformation_activate (self, *args):
        print "MainWindow.on_serviceInformation_activate (%s)" % ', '.join (map (lambda x: str(x), args))

    def on_helpContents_activate (self, *args):
        help_page = "ghelp:system-config-services"
        path = "/usr/bin/yelp"

        if not os.access (path, os.X_OK):
            d = gtk.MessageDialog (self.toplevel, 0,
                        gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE,
                        _("The help viewer could not be found. To be able to view help, the 'yelp' package needs to be installed."))
            d.set_position (gtk.WIN_POS_CENTER)
            d.run ()
            d.destroy ()
            return

        pid = os.fork ()
        if pid == 0:
            os.execv (path, (path, help_page))

    def on_helpAbout_activate (self, *args):
        self.aboutDialog.show ()
        self.aboutDialog.window.raise_ ()

    def on_aboutDialog_close (self, *args):
        self.aboutDialog.hide ()
        return True

##############################################################################

class GUI (object):
    def __init__ (self):
        self._filemon = gamin.WatchMonitor ()
        self._filemon_fd = self._filemon.get_fd ()
        gobject.io_add_watch (self._filemon_fd, gobject.IO_IN | gobject.IO_PRI,
                              self._mon_handle_events)

        self.serviceherders = []
        for cls in serviceherders.herder_classes:
            self.serviceherders.append (cls (mon = self._filemon))

        self.mainWindow = MainWindow (serviceherders = self.serviceherders)

    def _mon_handle_events (self, source, condition, data = None):
        self._filemon.handle_events ()
        return True

    def run (self):
        try:
            self.mainWindow.toplevel.show ()
            gtk.main ()
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    try:
        GUI ().run ()
    except KeyboardInterrupt:
        pass
