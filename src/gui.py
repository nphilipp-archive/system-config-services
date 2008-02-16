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

import async

import serviceherders
from serviceherders import SVC_ADDED, SVC_DELETED, SVC_CONF_UPDATING, SVC_CONF_CHANGED, SVC_STATUS_UPDATING, SVC_STATUS_CHANGED
import services
from services import SVC_STATUS_UNKNOWN, SVC_STATUS_STOPPED, SVC_STATUS_RUNNING, SVC_STATUS_DEAD

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
        SVC_COL_ENABLED:        gtk.gdk.Pixbuf,
        SVC_COL_STATUS:         gtk.gdk.Pixbuf,
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
        SVC_COL_ENABLED:    ["", gtk.CellRendererPixbuf, None, False, False, False, 40],
        SVC_COL_STATUS:     ["", gtk.CellRendererPixbuf, None, False, False, False, 40],
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

def _status_stock_icon (status):
    if status == SVC_STATUS_UNKNOWN:
        return gtk.STOCK_DIALOG_QUESTION
    elif status == SVC_STATUS_STOPPED:
        return gtk.STOCK_DISCONNECT
    elif status == SVC_STATUS_RUNNING:
        return gtk.STOCK_CONNECT
    elif status == SVC_STATUS_DEAD:
        return gtk.STOCK_STOP
    else:
        raise KeyError ("service: %s status: %d" % (self.service.name, status))

##############################################################################

class GUIServicesDetailsPainter (object):
    _xml_widgets = []

    _classes = None
    _classes_objects = { }

    """Abstract services details painter"""
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
        self.xml = xml
        self.service = service

        for wname in self._xml_widgets:
            w = xml.get_widget (wname)
            if w:
                setattr (self, wname, w)

    def paint_details (self):
        raise NotImplementedError

##############################################################################

class GUISysVServicesDetailsPainter (GUIServicesDetailsPainter):
    """Details painter for SysV services"""
    _xml_widgets = [
        'sysVServiceExplanationLabel',
        'sysVServiceEnabledIcon',
        'sysVServiceEnabledLabel',
        'sysVServiceStatusIcon',
        'sysVServiceStatusLabel',
        'sysVServiceDescriptionTextView'
    ]

    def __init__ (self, xml, service):
        super (GUISysVServicesDetailsPainter, self).__init__ (xml, service)

    def paint_details (self):
        if self.service.status_updating:
            self.sysVServiceStatusIcon.set_from_stock (gtk.STOCK_REFRESH,
                                                       gtk.ICON_SIZE_MENU)
        else:
            stock_icon = _status_stock_icon (self.service.status)
            self.sysVServiceStatusIcon.set_from_stock (stock_icon,
                                                       gtk.ICON_SIZE_MENU)

        if self.service.conf_updating:
            self.sysVServiceEnabledIcon.set_from_stock (gtk.STOCK_REFRESH,
                                                        gtk.ICON_SIZE_MENU)
        else:
            self.sysVServiceEnabledIcon.set_from_stock (gtk.STOCK_DIALOG_QUESTION,
                                                        gtk.ICON_SIZE_MENU)

##############################################################################

class GUIXinetdServicesDetailsPainter (GUIServicesDetailsPainter):
    _xml_widgets = [
        'xinetdExplanationLabel',
        'xinetdServiceStatusIcon',
        'xinetdServiceStatusLabel',
        'xinetdServiceDescription'
    ]

    def __init__ (self, xml, service):
        super (GUIXinetdServicesDetailsPainter, self).__init__ (xml, service)

    def paint_details (self):
        pass
        # FIXME

##############################################################################

class GUIServiceEntryPainter (object):
    def __new__ (cls, xml, service, *p, **k):
        if isinstance (service, services.SysVService):
            return object.__new__ (GUISysVServiceEntryPainter)
        elif isinstance (service, services.XinetdService):
            return object.__new__ (GUIXinetdServiceEntryPainter)
        else:
            raise TypeError ('service')

    def __init__ (self, xml, service):
        self._conf_updating = False

        self.xml = xml
        self.service = service

    def set_conf_updating (self, updating):
        if updating != self._conf_updating:
            self._conf_updating = updating
            # FIXME

##############################################################################

class GUISysVServiceEntryPainter (GUIServiceEntryPainter):
    def __init__ (self, xml, service):
        super (GUISysVServiceEntryPainter, self).__init__ (xml, service)
        self._status_updating = False

    def set_status_updating (self, updating):
        if updating != self._status_updating:
            self._conf_updating = updating
            # FIXME

##############################################################################

class GUIXinetdServiceEntryPainter (GUIServiceEntryPainter):
    pass

##############################################################################

class GUIServicesList (object):
    SERVICE_TYPE_NONE = 0
    SERVICE_TYPE_SYSV = 1
    SERVICE_TYPE_XINETD = 2

    def __init__ (self, xml, serviceherders):
        self.current_service = None
        self.service_painters = {}

        self.xml = xml
        self.serviceherders = serviceherders

        servicesScrolledWindow = xml.get_widget ('servicesScrolledWindow')
        servicesTreeView = xml.get_widget ('servicesTreeView')
        servicesScrolledWindow.remove (servicesTreeView)

        self.servicesTreeView = GUIServicesTreeView ()
        self.servicesTreeView.show ()
        self.servicesTreeView.connect ('service-selected', self.on_service_selected)

        self.servicesTreeStore = self.servicesTreeView.model

        servicesScrolledWindow.add (self.servicesTreeView)

        self.servicesDetailsNotebook = self.xml.get_widget ("servicesDetailsNotebook")

        for herder in serviceherders:
            herder.subscribe (self.on_services_changed)

    def on_service_selected (self, treeview = None, service = None, *args):
        self.current_service = service
        GUIServicesDetailsPainter (self.xml, service).paint_details ()
        if isinstance (service, services.SysVService):
            self.servicesDetailsNotebook.set_current_page (self.SERVICE_TYPE_SYSV)
        elif isinstance (service, services.XinetdService):
            self.servicesDetailsNotebook.set_current_page (self.SERVICE_TYPE_XINETD)
        else:
            self.servicesDetailsNotebook.set_current_page (self.SERVICE_TYPE_NONE)

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
        #self._service_conf_changed (service)

    def on_service_deleted (self, service):
        self.servicesTreeStore.delete_service (service)
        if service == self.current_service:
            self.on_service_selected (service = None)
        try:
            self.service_painters[service]
        except KeyError:
            pass

    def on_service_conf_updating (self, service):
        if not self.service_painters.has_key (service):
            self.service_painters[service] = GUIServiceEntryPainter (self.xml, service)
        self.service_painters[service].set_conf_updating (True)

    def on_service_conf_changed (self, service):
        if not self.service_painters.has_key (service):
            self.service_painters[service] = GUIServiceEntryPainter (self.xml, service)
        self.service_painters[service].set_conf_updating (False)
        if service == self.current_service:
            GUIServicesDetailsPainter (self.xml, service).paint_details ()

    def on_service_status_updating (self, service):
        if not self.service_painters.has_key (service):
            self.service_painters[service] = GUIServiceEntryPainter (self.xml, service)
        self.service_painters[service].set_status_updating (True)

    def on_service_status_changed (self, service):
        if not self.service_painters.has_key (service):
            self.service_painters[service] = GUIServiceEntryPainter (self.xml, service)
        self.service_painters[service].set_status_updating (False)
        if service == self.current_service:
            GUIServicesDetailsPainter (self.xml, service).paint_details ()

##############################################################################

class MainWindow (object):
    def __init__ (self, serviceherders):
        try:
            self.xml = gtk.glade.XML ("system-config-services.glade",
                                      domain = config.domain)
        except RuntimeError:
            self.xml = gtk.glade.XML (os.path.join (config.datadir,
                                                    "system-config-services.glade"),
                                      domain = config.domain)

        self.servicesList = GUIServicesList (xml = self.xml, serviceherders = serviceherders)

        self.toplevel = self.xml.get_widget ("mainWindow")
        self.toplevel.connect ('delete_event', gtk.main_quit)

        # the tabs are visible in the glade file to improve maintainability ...
        self.servicesDetailsNotebook = self.xml.get_widget ("servicesDetailsNotebook")
        # ... so we hide them
        self.servicesDetailsNotebook.set_show_tabs (False)

        self.aboutDialog = self.xml.get_widget ("aboutDialog")
        self.aboutDialog.set_name (config.name)
        self.aboutDialog.set_version (config.version)

        # connect defined signals with callback methods
        self.xml.signal_autoconnect (self)

    def on_programQuit_activate (self, *args):
        gtk.main_quit ()

    def on_serviceEnable_activate (self, *args):
        print "MainWindow.on_serviceEnable_activate (%s)" % ', '.join (map (lambda x: str(x), args))

    def on_serviceEnable_show_menu (self, *args):
        print "MainWindow.on_serviceEnable_show_menu (%s)" % ', '.join (map (lambda x: str(x), args))

    def on_serviceDisable_activate (self, *args):
        print "MainWindow.on_serviceDisable_activate (%s)" % ', '.join (map (lambda x: str(x), args))

    def on_serviceStart_activate (self, *args):
        print "MainWindow.on_serviceStart_activate (%s)" % ', '.join (map (lambda x: str(x), args))

    def on_serviceStop_activate (self, *args):
        print "MainWindow.on_serviceStop_activate (%s)" % ', '.join (map (lambda x: str(x), args))

    def on_serviceRestart_activate (self, *args):
        print "MainWindow.on_serviceRestart_activate (%s)" % ', '.join (map (lambda x: str(x), args))

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

    def refresh_interface (self):
        gtk.main_iteration (block = False) 

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
        async.queues_kill ()
