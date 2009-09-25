# -*- coding: utf-8 -*-

# scservices.dbus.proxy.services: DBus proxy objects for services
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

from scservices.dbus import dbus_service_name

import dbus
import slip.dbus.polkit as polkit


class DBusServiceInfoProxy(object):

    def __init__(self, name, bus, service):
        self.name = name
        self.bus = bus
        self.service = service

        self.dbus_service_path = self.service.dbus_service_path
        self.dbus_object = bus.get_object(dbus_service_name,
                self.dbus_service_path)
        self.svc_interface = dbus.Interface(self.dbus_object,
                "org.fedoraproject.Config.Services.Service")


class DBusSysVServiceInfoProxy(DBusServiceInfoProxy):

    def __init__(self, *p, **k):
        super(DBusSysVServiceInfoProxy, self).__init__(*p, **k)
        self.sysv_interface = dbus.Interface(self.dbus_object,
                "org.fedoraproject.Config.Services.SysVService")

    @property
    @polkit.enable_proxy
    def shortdescription(self):
        return self.sysv_interface.get_shortdescription()

    @property
    @polkit.enable_proxy
    def description(self):
        return self.sysv_interface.get_description()


class DBusXinetdServiceInfoProxy(DBusServiceInfoProxy):

    def __init__(self, *p, **k):
        super(DBusXinetdServiceInfoProxy, self).__init__(*p, **k)
        self.xinetd_interface = dbus.Interface(self.dbus_object,
                "org.fedoraproject.Config.Services.XinetdService")

    @property
    @polkit.enable_proxy
    def description(self):
        return self.xinetd_interface.get_description()


