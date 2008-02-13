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
from serviceherders import SVC_ADDED, SVC_DELETED, SVC_CHANGED
import services

gtk.glade.bindtextdomain (config.domain)

SVC_COL_SVC_OBJECT = 0
SVC_COL_ENABLED = 1
SVC_COL_STATUS = 2
SVC_COL_NAME = 3
SVC_COL_REMARK = 4
SVC_COL_LAST = 5

class GUIServicesTreeStore (gtk.TreeStore):
    col_types = {
        SVC_COL_SVC_OBJECT:     gobject.TYPE_PYOBJECT,
        SVC_COL_ENABLED:        gtk.gdk.Pixbuf,
        SVC_COL_STATUS:         gtk.gdk.Pixbuf,
        SVC_COL_NAME:           gobject.TYPE_STRING,
        SVC_COL_REMARK:         gobject.TYPE_STRING,
    }

    def __init__ (self, serviceherders):
        col_types = []
        for col in xrange (SVC_COL_LAST):
            col_types.append (self.col_types [col])
        gtk.TreeStore.__init__ (self, *col_types)
        self.set_default_sort_func (self._sort_by_name)
        self.set_sort_func (SVC_COL_NAME, self._sort_by_name)
        self.set_sort_column_id (SVC_COL_NAME, gtk.SORT_ASCENDING)

        self.serviceherders = serviceherders

        for herder in serviceherders:
            herder.subscribe (self.on_services_changed)

    def _sort_by_name (self, treemodel, iter1, iter2, user_data = None):
        name1 = self.get (iter1, SVC_COL_NAME)
        name2 = self.get (iter2, SVC_COL_NAME)

        return name1 < name2 and -1 or name1 > name2 and 1 or 0

    def _delete_svc_callback (self, model, path, iter, service):
        row_service = self.get_value (iter, SVC_COL_SVC_OBJECT)

        if row_service == service:
            self.remove (iter)
            return True

        return False

    def on_services_changed (self, change, service):
        #print "GUIServicesTreeStore.on_services_changed (%s, %s)" % (('SVC_ADDED', 'SVC_DELETED', 'SVC_CHANGED')[change], service)
        if change == SVC_ADDED:
            iter = self.append (None)
            self.set (iter, SVC_COL_SVC_OBJECT, service, SVC_COL_NAME, service.name)
        elif change == SVC_DELETED:
            self.foreach (self._delete_svc_callback, service)
        elif change == SVC_CHANGED:
            pass

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

    def __init__ (self, serviceherders):
        self.model = GUIServicesTreeStore (serviceherders)
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

class GUIServicesList (object):
    SERVICE_TYPE_NONE = 0
    SERVICE_TYPE_SYSV = 1
    SERVICE_TYPE_XINETD = 2

    def __init__ (self, xml, serviceherders):
        self.xml = xml
        self.serviceherders = serviceherders

        servicesScrolledWindow = xml.get_widget ('servicesScrolledWindow')
        servicesTreeView = xml.get_widget ('servicesTreeView')
        servicesScrolledWindow.remove (servicesTreeView)

        self.servicesTreeView = GUIServicesTreeView (serviceherders)
        self.servicesTreeView.show ()
        self.servicesTreeView.connect ('service-selected', self.on_service_selected)

        servicesScrolledWindow.add (self.servicesTreeView)

        self.servicesDetailsNotebook = self.xml.get_widget ("servicesDetailsNotebook")

    def on_service_selected (self, treeview, service, *args):
        if isinstance (service, services.SysVService):
            self.servicesDetailsNotebook.set_current_page (self.SERVICE_TYPE_SYSV)
        elif isinstance (service, services.XinetdService):
            self.servicesDetailsNotebook.set_current_page (self.SERVICE_TYPE_XINETD)
        else:
            self.servicesDetailsNotebook.set_current_page (self.SERVICE_TYPE_NONE)

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
    GUI ().run ()
