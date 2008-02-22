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

import gobject
import gamin
import gtk
import gtk.glade

from rhpl.translate import _, N_

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

class GUIServicesTreeStore (gtk.TreeStore):
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
        gtk.TreeStore.__init__ (self, *col_types)
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
        self.model = GUIServicesTreeStore ()

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
        SVC_STATUS_UNKNOWN: _("The status of this service is unknown."),
        SVC_STATUS_STOPPED: _("This service is stopped."),
        SVC_STATUS_RUNNING: _("This service is running."),
        SVC_STATUS_DEAD: _("This service is dead."),
        }

##############################################################################

class GladeUser (object):
    _xml_widgets = []

    def __init__ (self, xml):
        self.xml = xml

        for wname in self._xml_widgets:
            w = xml.get_widget (wname)
            if w:
                setattr (self, wname, w)
            else:
                raise KeyError (wname)

##############################################################################

class GUIServicesDetailsPainter (GladeUser):
    """Services details painter singleton factory"""

    _classes = None
    _classes_objects = { }

    def __new__ (cls, xml, service, *p, **k):
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

    def __init__ (self, xml, service):
        super (GUIServicesDetailsPainter, self).__init__ (xml)
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

    def __init__ (self, xml, service):
        super (GUISysVServicesDetailsPainter, self).__init__ (xml, service)

    def paint_details (self):
        self.sysVServiceExplanationLabel.set_markup (_("The <b>%(servicename)s</b> service is started once, usually when the system is booted, runs in the background and wakes up when needed.") % {'servicename': self.service.name})

        enabled = self.service.is_enabled ()
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

    def __init__ (self, xml, service):
        super (GUIXinetdServicesDetailsPainter, self).__init__ (xml, service)

    def paint_details (self):
        self.xinetdServiceExplanationLabel.set_markup (_("The <b>%(servicename)s</b> service will be started on demand by the xinetd service and ends when it has got nothing more to do.") % {'servicename': self.service.name})

        enabled = self.service.is_enabled ()
        self.xinetdServiceEnabledIcon.set_from_stock (_enabled_stock_id[enabled],
                                                      gtk.ICON_SIZE_MENU)
        self.xinetdServiceEnabledLabel.set_text (_enabled_text[enabled])

        if self.service.info.description:
            self.xinetdServiceDescriptionTextView.get_buffer ().set_text (self.service.info.description)
        else:
            self.xinetdServiceDescriptionTextView.get_buffer ().set_text ("")

##############################################################################

class GUIServiceEntryPainter (object):
    def __new__ (cls, treestore, service, *p, **k):
        if isinstance (service, services.SysVService):
            return object.__new__ (GUISysVServiceEntryPainter)
        elif isinstance (service, services.XinetdService):
            return object.__new__ (GUIXinetdServiceEntryPainter)
        else:
            raise TypeError ('service')

    def __init__ (self, treestore, service):
        self.treestore = treestore
        self.service = service

    def paint (self):
        raise NotImplementedError

##############################################################################

class GUISysVServiceEntryPainter (GUIServiceEntryPainter):
    def paint (self):
        iter = self.treestore.service_iters[self.service]
        self.treestore.set (iter, SVC_COL_ENABLED, _enabled_stock_id[self.service.is_enabled ()])
        self.treestore.set (iter, SVC_COL_STATUS, _status_stock_id[self.service.status])
        if self.service.info.shortdescription:
            self.treestore.set (iter, SVC_COL_REMARK, self.service.info.shortdescription)


##############################################################################

class GUIXinetdServiceEntryPainter (GUIServiceEntryPainter):
    def paint (self):
        iter = self.treestore.service_iters[self.service]
        self.treestore.set (iter, SVC_COL_ENABLED, _enabled_stock_id[self.service.is_enabled ()])
        self.treestore.set (iter, SVC_COL_STATUS, None)

##############################################################################

class GUIServicesList (GladeUser):
    SVC_PAGE_NONE = 0
    SVC_PAGE_SYSV = 1
    SVC_PAGE_XINETD = 2

    _service_xml_widgets = (
            'serviceEnable',
            'serviceDisable',
            'serviceStart',
            'serviceStop',
            'serviceRestart',
            'serviceInformation',
            'serviceEnableButton',
            'serviceDisableButton',
            'serviceStartButton',
            'serviceStopButton',
            'serviceRestartButton',
            'serviceInformationButton',
            )

    _xml_widgets = _service_xml_widgets + (
            'servicesScrolledWindow',
            'servicesDetailsNotebook',
            )

    def __init__ (self, xml, serviceherders):
        self.current_service = None
        self.service_painters = {}

        super (GUIServicesList, self).__init__ (xml)
        self.serviceherders = serviceherders

        servicesTreeView = xml.get_widget ('servicesTreeView')
        self.servicesScrolledWindow.remove (servicesTreeView)

        self.servicesTreeView = GUIServicesTreeView ()
        self.servicesTreeView.show ()
        self.servicesTreeView.connect ('service-selected', self.on_service_selected)

        self.servicesTreeStore = self.servicesTreeView.model

        self.servicesScrolledWindow.add (self.servicesTreeView)

        self.on_service_selected ()

        for herder in serviceherders:
            herder.subscribe (self.on_services_changed)

    def on_service_selected (self, treeview = None, service = None, *args):
        self.current_service = service
        if service:
            GUIServicesDetailsPainter (self.xml, service).paint_details ()
        if isinstance (service, services.SysVService):
            self.servicesDetailsNotebook.set_current_page (self.SVC_PAGE_SYSV)
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
            is_enabled = service.is_enabled ()
            if is_enabled == SVC_ENABLED_REFRESHING:
                sensitive = False
            elif wname == 'serviceEnable':
                sensitive = (is_enabled != SVC_ENABLED_YES)
            elif wname == 'serviceDisable':
                sensitive = (is_enabled != SVC_ENABLED_NO)
        elif wname in ('serviceStart', 'serviceStop', 'serviceRestart'):
            if isinstance (service, services.SysVService):
                if service.status == SVC_STATUS_REFRESHING:
                    sensitive = False
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

    def on_service_added (self, service):
        self.servicesTreeStore.add_service (service)
        self.service_painters[service] = GUIServiceEntryPainter (self.servicesTreeStore, service)
        self.service_painters[service].paint ()

    def on_service_deleted (self, service):
        self.servicesTreeStore.delete_service (service)
        if service == self.current_service:
            self.on_service_selected (service = None)
        try:
            del self.service_painters[service]
        except KeyError:
            pass

    def on_service_conf_updating (self, service):
        self.service_painters[service].paint ()
        self._set_widgets_sensitivity ()

    def on_service_conf_changed (self, service):
        self.service_painters[service].paint ()
        if service == self.current_service:
            GUIServicesDetailsPainter (self.xml, service).paint_details ()
        self._set_widgets_sensitivity ()

    def on_service_status_updating (self, service):
        self.service_painters[service].paint ()
        self._set_widgets_sensitivity ()

    def on_service_status_changed (self, service):
        if self.service_painters.has_key (service):
            self.service_painters[service].paint ()
            if service == self.current_service:
                GUIServicesDetailsPainter (self.xml, service).paint_details ()
        else:
            # service might have been deleted
            pass
        self._set_widgets_sensitivity ()

##############################################################################

class MainWindow (GladeUser):
    _xml_widgets = (
            'helpContents',
            'helpContentsButton',
            'servicesDetailsNotebook',
            'aboutDialog'
            )

    def __init__ (self, serviceherders):
        try:
            xml = gtk.glade.XML ("system-config-services.glade",
                                 domain = config.domain)
        except RuntimeError:
            xml = gtk.glade.XML (os.path.join (config.datadir,
                                 "system-config-services.glade"),
                                 domain = config.domain)

        super (MainWindow, self).__init__ (xml)

        self.servicesList = GUIServicesList (xml = self.xml, serviceherders = serviceherders)

        self.toplevel = xml.get_widget ("mainWindow")
        self.toplevel.connect ('delete_event', gtk.main_quit)

        # the tabs are visible in the glade file to improve maintainability ...
        # ... so we hide them
        self.servicesDetailsNotebook.set_show_tabs (False)

        self.aboutDialog.set_name (config.name)
        self.aboutDialog.set_version (config.version)

        # connect defined signals with callback methods
        xml.signal_autoconnect (self)

    def on_programQuit_activate (self, *args):
        gtk.main_quit ()

    def on_serviceEnable_activate (self, *args):
        service = self.servicesList.current_service
        if service:
            service.enable ()

    def on_serviceEnable_show_menu (self, *args):
        print "MainWindow.on_serviceEnable_show_menu (%s)" % ', '.join (map (lambda x: str(x), args))

    def on_serviceDisable_activate (self, *args):
        service = self.servicesList.current_service
        if service:
            service.disable ()

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
        print "MainWindow.on_helpContents_activate (%s)" % ', '.join (map (lambda x: str(x), args))

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
