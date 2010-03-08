# -*- coding: utf-8 -*-

# scservices.dbus.proxy.serviceherders: DBus proxy objects for service herders
#
# Copyright © 2008, 2009 Red Hat, Inc.
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

from scservices.core.serviceherders import SVC_ADDED, SVC_DELETED

from scservices.dbus.proxy.services import DBusSysVServiceProxy, \
    DBusXinetdServiceProxy

from scservices.dbus import dbus_service_name, dbus_service_path

import dbus
import slip.dbus.polkit as polkit


class DBusServiceHerderProxy(object):

    object_path = dbus_service_path + "/ServiceHerders/"

    def __init__(self, bus):
        self.bus = bus
        self.dbus_service_path = self.object_path + self.object_name
        self.dbus_object = bus.get_object(dbus_service_name,
                self.dbus_service_path)
        self.herder_interface = dbus.Interface(self.dbus_object,
                "org.fedoraproject.Config.Services.ServiceHerder")
        self.services_dbus_object = bus.get_object(dbus_service_name,
                self.dbus_service_path + "/Services")

        self.services = {}

        self.freeze_level = 0
        self.frozen_notifications = None

        self.freeze_notifications()

        self.subscribers = set()

        self.dbus_object.connect_to_signal("notify", self.notify)

        for service_name in self.list_services():
            self.services[service_name] = self.service_class(service_name,
                    bus, self)
        self.thaw_notifications()

    @property
    @polkit.enable_proxy
    def ready(self):
        return self.herder_interface.is_ready()

    @polkit.enable_proxy
    def list_services(self):
        return self.herder_interface.list_services()


    class _Subscriber(object):

        def __init__(self, remote_method_or_function, p, k):
            self.remote_method_or_function = remote_method_or_function
            self.p = p
            self.k = k


    class _Notification(object):

        def __init__(self, subscriber, service_name, change):
            self.subscriber = subscriber
            self.service_name = service_name
            self.change = change


    def subscribe(self, remote_method_or_function, *p, **k):
        self.subscribers.add(self._Subscriber(remote_method_or_function, p,
                             k))
        self.freeze_notifications()
        for service in self.services.itervalues():
            remote_method_or_function(herder=self, change=SVC_ADDED,
                                      service=service)
        self.thaw_notifications()

    def dbus_notify(self, subscriber, service_name, change):
        if change == SVC_ADDED:
            self.services[service_name] = self.service_class(service_name,
                    self.bus, self)

        if service_name != "":
            service = self.services[service_name]
        else:

            # service_name is empty if the herder signals being ready

            service = None
        k = copy.copy(subscriber.k)
        k["service"] = service
        subscriber.remote_method_or_function(herder=self, change=change,
                *subscriber.p, **k)

        if change == SVC_DELETED:
            del self.services[service_name]

    @property
    def frozen(self):
        return self.freeze_level > 0

    def freeze_notifications(self):
        self.freeze_level += 1
        if not self.frozen_notifications:
            self.frozen_notifications = []

    def thaw_notifications(self):
        assert self.freeze_level >= 1
        if self.freeze_level == 1:
            for n in self.frozen_notifications:
                self.dbus_notify(n.subscriber, n.service_name, n.change)
            self.frozen_notifications = None
        self.freeze_level -= 1

    def notify(self, change, service_name):
        for subscriber in self.subscribers:
            if not self.frozen:
                self.dbus_notify(subscriber, service_name, change)
            else:
                self.frozen_notifications.append(
                        self._Notification(subscriber, service_name, change))


class DBusSysVServiceHerderProxy(DBusServiceHerderProxy):

    object_name = "SysVServiceHerder"
    service_class = DBusSysVServiceProxy


class DBusXinetdServiceHerderProxy(DBusServiceHerderProxy):

    object_name = "XinetdServiceHerder"
    service_class = DBusXinetdServiceProxy


herder_classes = [DBusSysVServiceHerderProxy, DBusXinetdServiceHerderProxy]
