# -*- coding: utf-8 -*-
# scservices.dbus.proxy.services: DBus proxy objects for services
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

from scservices.dbus import dbus_service_name

import slip.dbus.polkit as polkit

##############################################################################

class DBusServiceInfoProxy (object):
    def __init__ (self, name, bus, service):
        self.name = name
        self.bus = bus
        self.service = service

        self.dbus_service_path = self.service.dbus_service_path
        self.dbus_object = bus.get_object (dbus_service_name,
                self.dbus_service_path)

##############################################################################

class DBusSysVServiceInfoProxy (DBusServiceInfoProxy):
    @property
    @polkit.enable_proxy
    def shortdescription (self):
        return self.dbus_object.get_shortdescription (dbus_interface = "org.fedoraproject.Config.Services.SysVService")

    @property
    @polkit.enable_proxy
    def description (self):
        return self.dbus_object.get_description (dbus_interface = "org.fedoraproject.Config.Services.SysVService")

##############################################################################

class DBusXinetdServiceInfoProxy (DBusServiceInfoProxy):
    @property
    @polkit.enable_proxy
    def description (self):
        return self.dbus_object.get_description (dbus_interface = "org.fedoraproject.Config.Services.XinetdService")
