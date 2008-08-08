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

from scservices.dbus.proxy.servicesinfo import DBusServiceInfoProxy, DBusSysVServiceInfoProxy, DBusXinetdServiceInfoProxy

from scservices.dbus import dbus_service_name

import slip.dbus.polkit as polkit
from slip.util.hookable import HookableSet

##############################################################################

class DBusServiceProxy (object):
    info_class = DBusServiceInfoProxy

    def __init__ (self, name, bus, herder):
        super (DBusServiceProxy, self).__init__ ()
        self.name = name
        self.bus = bus
        self.herder = herder

        self.dbus_service_path = herder.dbus_service_path + "/Services/" + self.dbus_name
        self.dbus_object = bus.get_object (dbus_service_name, self.dbus_service_path)

        self.info = self.info_class (name, bus, self)

    def __repr__ (self):
        return "<%s.%s object at %x: %s>" % (self.__class__.__module__, self.__class__.__name__, id (self), self.name)

    @property
    def dbus_name (self):
        if "_dbus_name" not in dir (self):
            self._dbus_name = self.name.replace ("-", "_")
        return self._dbus_name

    @polkit.enable_proxy
    def save (self):
        self.dbus_object.save (dbus_interface = "org.fedoraproject.Config.Services.Service")

##############################################################################

class DBusChkconfigServiceProxy (DBusServiceProxy):
    @polkit.enable_proxy
    def enable (self):
        self.dbus_object.enable (dbus_interface = "org.fedoraproject.Config.Services.ChkconfigService")

    @polkit.enable_proxy
    def disable (self):
        self.dbus_object.disable (dbus_interface = "org.fedoraproject.Config.Services.ChkconfigService")

    @polkit.enable_proxy
    def get_enabled (self):
        return self.dbus_object.get_enabled (dbus_interface = "org.fedoraproject.Config.Services.ChkconfigService")

##############################################################################

class DBusSysVServiceProxy (DBusChkconfigServiceProxy):
    info_class = DBusSysVServiceInfoProxy

    @polkit.enable_proxy
    def start (self):
        self.dbus_object.start (dbus_interface = "org.fedoraproject.Config.Services.SysVService")

    @polkit.enable_proxy
    def stop (self):
        self.dbus_object.stop (dbus_interface = "org.fedoraproject.Config.Services.SysVService")

    @polkit.enable_proxy
    def restart (self):
        self.dbus_object.restart (dbus_interface = "org.fedoraproject.Config.Services.SysVService")

    @polkit.enable_proxy
    def reload (self):
        self.dbus_object.reload (dbus_interface = "org.fedoraproject.Config.Services.SysVService")

    @property
    @polkit.enable_proxy
    def status (self):
        return self.dbus_object.get_status (dbus_interface = "org.fedoraproject.Config.Services.SysVService")

    @property
    @polkit.enable_proxy
    def status_updates_running (self):
        return self.dbus_object.get_status_updates_running (dbus_interface = "org.fedoraproject.Config.Services.SysVService")

    @polkit.enable_proxy
    def _get_runlevels (self):
        if not hasattr (self, "_runlevels"):
            self._runlevels = HookableSet ()
            self._runlevels.add_hook (self._save_runlevels)
        self._runlevels.hooks_enabled = False
        self._runlevels.clear ()
        self._runlevels.update (self.dbus_object.get_runlevels (dbus_interface = "org.fedoraproject.Config.Services.SysVService"))
        self._runlevels.hooks_enabled = True
        return self._runlevels

    def _set_runlevels (self, runlevels):
        if self.runlevels != runlevels:
            self.runlevels.freeze_hooks ()
            self.runlevels.clear ()
            self.runlevels.update (runlevels)
            self.runlevels.thaw_hooks ()

    @polkit.enable_proxy
    def _save_runlevels (self):
        self.dbus_object.set_runlevels (list (self._runlevels), dbus_interface = "org.fedoraproject.Config.Services.SysVService")

    runlevels = property (_get_runlevels, _set_runlevels)

SysVService = DBusSysVServiceProxy

##############################################################################

class DBusXinetdServiceProxy (DBusChkconfigServiceProxy):
    info_class = DBusXinetdServiceInfoProxy

XinetdService = DBusXinetdServiceProxy
