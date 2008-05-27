# -*- coding: utf-8 -*-
# dbus_proxy.py: dbus proxy objects
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

import copy

import dbus
import dbus.service

from serviceherders import SVC_ADDED, SVC_DELETED, SVC_CONF_UPDATING, SVC_CONF_CHANGED, SVC_STATUS_UPDATING, SVC_STATUS_CHANGED

from services import SVC_STATUS_REFRESHING, SVC_STATUS_UNKNOWN, SVC_STATUS_STOPPED, SVC_STATUS_RUNNING, SVC_STATUS_DEAD
from services import SVC_ENABLED_REFRESHING, SVC_ENABLED_YES, SVC_ENABLED_NO, SVC_ENABLED_CUSTOM

dbus_service_name = "org.fedoraproject.Config.Services"
dbus_service_path = "/org/fedoraproject/Config/Services"

##############################################################################

class DBusServiceProxy (object):
    def __init__ (self, name, bus, herder):
        super (DBusServiceProxy, self).__init__ ()
        self.bus = bus
        self.herder = herder

        self.dbus_service_path = herder.dbus_service_path + "/Services/" + name
        self.dbus_object = bus.get_object (dbus_service_name, self.dbus_service_path)

    @property
    def name (self):
        if "_name" not in dir (self):
            self._name = self.dbus_object.get_name ()
        return self._name

    def save (self):
        self.dbus_object.save ()

##############################################################################

class DBusChkconfigServiceProxy (DBusServiceProxy):
    def enable (self):
        self.dbus_object.enable ()

    def disable (self):
        self.dbus_object.disable ()

##############################################################################

class DBusSysVServiceProxy (DBusChkconfigServiceProxy):
    def start (self):
        self.dbus_object.start ()

    def stop (self):
        self.dbus_object.stop ()

    def restart (self):
        self.dbus_object.restart ()

    def reload (self):
        self.dbus_object.reload ()

SysVService = DBusSysVServiceProxy

##############################################################################

class DBusXinetdServiceProxy (DBusChkconfigServiceProxy):
    pass

XinetdService = DBusXinetdServiceProxy

##############################################################################

class DBusServiceHerderProxy (object):
    object_path = dbus_service_path + "/ServiceHerders/"

    def __init__ (self, bus):
        super (DBusServiceHerderProxy, self).__init__ ()

        self.bus = bus
        self.dbus_service_path = dbus_service_path + "/ServiceHerders/" + self.object_name
        self.dbus_object = bus.get_object (dbus_service_name, self.dbus_service_path)
        self.services_dbus_object = bus.get_object (dbus_service_name, self.dbus_service_path + "/Services")

        self.dbus_object.connect_to_signal ("notify", self.dbus_notify)


        i = self.services_dbus_object.Introspect (dbus_interface = "org.freedesktop.DBus.Introspectable")

        print "i:", i

        self.services = {}
        self.subscribers = set ()

    class _Subscriber (object):
        def __init__ (self, remote_method_or_function, p, k):
            self.remote_method_or_function = remote_method_or_function
            self.p = p
            self.k = k

    def subscribe (self, remote_method_or_function, *p, **k):
        self.subscribers.add (self._Subscriber (remote_method_or_function, p, k))
        for service in self.services.itervalues ():
            remote_method_or_function (change = SVC_ADDED, service = service)

    def dbus_notify (self, change, service_name):
        for subscriber in self.subscribers:
            k = copy.copy (subscriber.k)
            service = self.service_class (service_name, self.bus, self)
            k["service"] = service
            subscriber.remote_method_or_function (change = change, *subscriber.p, **k)

##############################################################################

class DBusSysVServiceHerderProxy (DBusServiceHerderProxy):
    object_name = "SysVServiceHerder"
    service_class = DBusSysVServiceProxy

##############################################################################

class DBusXinetdServiceHerderProxy (DBusServiceHerderProxy):
    object_name = "XinetdServiceHerder"
    service_class = DBusXinetdServiceProxy

##############################################################################

herder_classes = [ DBusSysVServiceHerderProxy, DBusXinetdServiceHerderProxy ]

if __name__ == "__main__":
    import dbus.mainloop.glib
    import gobject

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    system_bus = dbus.SystemBus ()

    mainloop = gobject.MainLoop ()
    sysv = DBusSysVServiceHerderProxy (system_bus)
    xinetd = DBusXinetdServiceHerderProxy (system_bus)

    mainloop.run ()

