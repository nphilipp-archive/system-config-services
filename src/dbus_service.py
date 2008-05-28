#!/usr/bin/python
# -*- coding: utf-8 -*-
# dbus_service.py: dbus service
#
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
# Authors:
# Nils Philippsen <nphilipp@redhat.com>

import gamin
import gobject

import dbus
import dbus.service
import slip.dbus.service
import dbus.mainloop.glib

import serviceherders
from serviceherders import SVC_ADDED, SVC_DELETED, SVC_CONF_UPDATING, SVC_CONF_CHANGED, SVC_STATUS_UPDATING, SVC_STATUS_CHANGED

import services
from services import SVC_STATUS_REFRESHING, SVC_STATUS_UNKNOWN, SVC_STATUS_STOPPED, SVC_STATUS_RUNNING, SVC_STATUS_DEAD
from services import SVC_ENABLED_REFRESHING, SVC_ENABLED_YES, SVC_ENABLED_NO, SVC_ENABLED_CUSTOM

##############################################################################

class DBusService (slip.dbus.service.TimeoutObject):
    def __new__ (cls, bus, object_path, service, **k):
        srv_cls_dbussrv_cls = {
                services.SysVService: DBusSysVService,
                services.XinetdService: DBusXinetdService,
                }

        for srv_cls, dbussrv_cls in srv_cls_dbussrv_cls.iteritems ():
            if isinstance (service, srv_cls):
                return super (DBusService, cls).__new__ (dbussrv_cls, bus, object_path, service, **k)
        raise NotImplementedError

    def __init__ (self, bus, object_path, service):
        slip.dbus.service.TimeoutObject.__init__ (self, bus, object_path)

        self.service = service

    @dbus.service.method (dbus_interface = "org.fedoraproject.Config.Services.Service", in_signature = "", out_signature = "")
    def save (self):
        raise NotImplementedError

##############################################################################

class DBusChkconfigService (DBusService):
    @dbus.service.method (dbus_interface = "org.fedoraproject.Config.Services.ChkconfigService", in_signature = "", out_signature = "")
    def enable (self):
        self.service.enable ()

    @dbus.service.method (dbus_interface = "org.fedoraproject.Config.Services.ChkconfigService", in_signature = "", out_signature = "")
    def disable (self):
        self.service.disable ()

    @dbus.service.method (dbus_interface = "org.fedoraproject.Config.Services.ChkconfigService", in_signature = "", out_signature = "b")
    def get_enabled (self):
        return self.service.get_enabled ()

##############################################################################

class DBusSysVService (DBusChkconfigService):
    # FIXME
    def save (self, runlevels):
        pass

    @dbus.service.method (dbus_interface = "org.fedoraproject.Config.Services.SysVService", in_signature = "", out_signature = "")
    def start (self):
        self.service.start ()

    @dbus.service.method (dbus_interface = "org.fedoraproject.Config.Services.SysVService", in_signature = "", out_signature = "")
    def stop (self):
        self.service.stop ()

    @dbus.service.method (dbus_interface = "org.fedoraproject.Config.Services.SysVService", in_signature = "", out_signature = "")
    def restart (self):
        self.service.restart ()

    @dbus.service.method (dbus_interface = "org.fedoraproject.Config.Services.SysVService", in_signature = "", out_signature = "")
    def reload (self):
        self.service.reload ()

    @dbus.service.method (dbus_interface = "org.fedoraproject.Config.Services.SysVService", in_signature = "", out_signature = "i")
    def get_status (self):
        return self.service.status

    @dbus.service.method (dbus_interface = "org.fedoraproject.Config.Services.SysVService", in_signature = "", out_signature = "i")
    def get_status_updates_running (self):
        return self.service.status_updates_running

    @dbus.service.method (dbus_interface = "org.fedoraproject.Config.Services.SysVService", in_signature = "", out_signature = "s")
    def get_shortdescription (self):
        if self.service.info.shortdescription:
            return self.service.info.shortdescription
        else:
            return ""

    @dbus.service.method (dbus_interface = "org.fedoraproject.Config.Services.SysVService", in_signature = "", out_signature = "s")
    def get_description (self):
        if self.service.info.description:
            return self.service.info.description
        else:
            return ""

    @dbus.service.method (dbus_interface = "org.fedoraproject.Config.Services.SysVService", in_signature = "", out_signature = "ai")
    def get_runlevels (self):
        return list (self.service.runlevels)

##############################################################################

class DBusXinetdService (DBusChkconfigService):
    @dbus.service.method (dbus_interface = "org.fedoraproject.Config.Services.XinetdService", in_signature = "b", out_signature = "")
    def save (self, enabled):
        self.service.enabled = enabled
        self.service.save ()
    
    @dbus.service.method (dbus_interface = "org.fedoraproject.Config.Services.XinetdService", in_signature = "", out_signature = "s")
    def get_description (self):
        if self.service.info.description:
            return self.service.info.description
        else:
            return ""

##############################################################################

class DBusServiceHerder (slip.dbus.service.TimeoutObject):
    def __init__ (self, bus, object_path, herder):
        slip.dbus.service.TimeoutObject.__init__ (self, bus, object_path)

        self.herder = herder
        self.herder.subscribe (self.on_services_changed)

        self.services_dbusservices = {}

    @dbus.service.method (dbus_interface = "org.fedoraproject.Config.Services.ServiceHerder", in_signature = "", out_signature = "s")
    def ping (self):
        return "pong"

    def on_services_changed (self, change, service):
        if change == SVC_ADDED:
            self.on_service_added (service)
        elif change == SVC_DELETED:
            self.on_service_deleted (service)

        self.notify (change, service.name)

    def on_service_added (self, service):
        if service in self.services_dbusservices:
            raise KeyError ("service %s added twice to %s" % (service, self))
        self.services_dbusservices[service] = DBusService (self.connection, self._service_object_path (service), service)

    def on_service_deleted (self, service):
        dbusservice = self.services_dbusservices[service]
        dbusservice.remove_from_connection (connection = self.connection, path = self._service_object_path (service))
        del self.services_dbusservices[service]

    @dbus.service.method (dbus_interface = "org.fedoraproject.Config.Services.ServiceHerder", out_signature = "as")
    def list_services (self):
        return map (lambda service: service.name, self.services_dbusservices.keys ())

    @dbus.service.signal (dbus_interface = "org.fedoraproject.Config.Services.ServiceHerder.notify", signature = "us")
    def notify (self, change, servicename):
        pass

    def _service_object_path (self, service):
        name = service.name.replace ('-', '_')
        return "%s/Services/%s" % (self._object_path, name)

##############################################################################

def run_service ():
    mainloop = gobject.MainLoop()
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    system_bus = dbus.SystemBus()
    name = dbus.service.BusName("org.fedoraproject.Config.Services", system_bus)

    filemon = gamin.WatchMonitor ()
    filemon_fd = filemon.get_fd ()

    dbus_herder_objects = []

    for herder_cls in serviceherders.herder_classes:
        herder = herder_cls (filemon)
        dbus_herder_object = DBusServiceHerder (system_bus, "/org/fedoraproject/Config/Services/ServiceHerders/%s" % herder_cls.__name__, herder)
        dbus_herder_objects.append (dbus_herder_object)

    def filemon_handle_events (source, condition, data = None):
        filemon.handle_events ()
        return True

    gobject.io_add_watch (filemon_fd, gobject.IO_IN | gobject.IO_PRI, filemon_handle_events)

    slip.dbus.service.set_mainloop (mainloop)
    print "Running system-config-services dbus service."
    mainloop.run ()

##############################################################################

if __name__ == "__main__":
    run_service ()
