# -*- coding: utf-8 -*-

# scservices.dbus.service.systemd.manager: polkit-enabled DBUS wrapper for
# systemd manager
#
# Copyright © 2011 Red Hat, Inc.
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
#import slip.dbus.polkit as polkit

from scservices.core.systemd.manager import SystemDManager
from scservices.core.systemd.constants.dbus import manager_interface


class DBusSystemDManager(slip.dbus.service.Object):

    default_polkit_auth_required = "org.fedoraproject.config.services.manage"

    def __init__(self, bus_name, object_path, manager, persistent=None):
        assert isinstance(manager, SystemDManager)

        slip.dbus.service.Object.__init__(self, bus_name, object_path,
                persistent)

        self.manager = manager

    @dbus.service.method(dbus_interface=manager_interface,
            in_signature="ss", out_signature="o")
    def RestartUnit(self, name, mode):
        return self.manager.RestartUnit(name, mode)

    @dbus.service.method(dbus_interface=manager_interface,
            in_signature="ss", out_signature="o")
    def StartUnit(self, name, mode):
        return self.manager.StartUnit(name, mode)

    @dbus.service.method(dbus_interface=manager_interface,
            in_signature="ss", out_signature="o")
    def StopUnit(self, name, mode):
        return self.manager.StopUnit(name, mode)
