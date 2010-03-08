# -*- coding: utf-8 -*-

# scservices.dbus.service.serviceherder: DBUS wrapper for service herders
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
# Nils Philippsen <nils@redhat.com>

import dbus.service
import slip.dbus.service
import slip.dbus.polkit as polkit

from scservices.core.serviceherders import SVC_ADDED, SVC_DELETED
from scservices.dbus.service.services import DBusService

from scservices.dbus import dbus_service_name


class DBusServiceHerder(slip.dbus.service.Object):

    default_polkit_auth_required = "org.fedoraproject.config.services.manage"

    def __init__(self, bus_name, object_path, herder, persistent=None):
        slip.dbus.service.Object.__init__(self, bus_name, object_path,
                persistent)

        self.herder = herder
        self.herder.subscribe(self.on_services_changed)

        self.services_dbusservices = {}

    def on_services_changed(self, herder, change, service):

        # ignore herder as we know which one is affected

        if change == SVC_ADDED:
            self.on_service_added(service)
        elif change == SVC_DELETED:
            self.on_service_deleted(service)

        if service:
            servicename = service.name
        else:
            servicename = ""

        self.notify(change, servicename)

    def on_service_added(self, service):
        if service in self.services_dbusservices:
            raise KeyError("service %s added twice to %s" % (service, self))
        self.services_dbusservices[service] = DBusService(self.connection,
                self._service_object_path(service), service)

    def on_service_deleted(self, service):
        dbusservice = self.services_dbusservices[service]
        dbusservice.remove_from_connection(connection=self.connection,
                path=self._service_object_path(service))
        del self.services_dbusservices[service]

    @polkit.require_auth("org.fedoraproject.config.services.info")
    @dbus.service.method(dbus_interface=dbus_service_name + ".ServiceHerder",
                         out_signature="b")
    def is_ready(self):
        return self.herder.ready

    @polkit.require_auth("org.fedoraproject.config.services.info")
    @dbus.service.method(dbus_interface=dbus_service_name + ".ServiceHerder",
                         out_signature="as")
    def list_services(self):
        return map(lambda service: service.name,
                   self.services_dbusservices.keys())

    @dbus.service.signal(dbus_interface=dbus_service_name + ".ServiceHerder",
                         signature="us")
    def notify(self, change, servicename):
        pass

    def _service_object_path(self, service):
        name = service.name.replace("-", "_")
        return "%s/Services/%s" % (self._object_path, name)


