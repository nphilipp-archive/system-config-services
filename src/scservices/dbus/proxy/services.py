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

from scservices.dbus.proxy.servicesinfo import DBusServiceInfoProxy, \
    DBusSysVServiceInfoProxy, DBusXinetdServiceInfoProxy

from scservices.dbus import dbus_service_name

import dbus
import slip.dbus.polkit as polkit
from slip.util.hookable import HookableSet


class DBusServiceProxy(object):

    info_class = DBusServiceInfoProxy

    def __init__(self, name, bus, herder):
        super(DBusServiceProxy, self).__init__()
        self.name = name
        self.bus = bus
        self.herder = herder

        self.dbus_service_path = herder.dbus_service_path + "/Services/" + \
            self.dbus_name
        self.dbus_object = bus.get_object(dbus_service_name,
                self.dbus_service_path)
        self.svc_interface = dbus.Interface(self.dbus_object,
                "org.fedoraproject.Config.Services.Service")

        self.info = self.info_class(name, bus, self)

    def __repr__(self):
        return "<%s.%s object at %x: %s>" % (self.__class__.__module__,
                self.__class__.__name__, id(self), self.name)

    @property
    def dbus_name(self):
        if "_dbus_name" not in dir(self):
            self._dbus_name = self.name.replace("-", "_")
        return self._dbus_name


class DBusChkconfigServiceProxy(DBusServiceProxy):

    def __init__(self, *p, **k):
        super(DBusChkconfigServiceProxy, self).__init__(*p, **k)
        self.chkconfig_interface = dbus.Interface(self.dbus_object,
                "org.fedoraproject.Config.Services.ChkconfigService")

    @polkit.enable_proxy(authfail_result=None)
    def enable(self):
        return self.chkconfig_interface.enable()

    @polkit.enable_proxy(authfail_result=None)
    def disable(self):
        return self.chkconfig_interface.disable()

    @polkit.enable_proxy
    def get_enabled(self):
        return self.chkconfig_interface.get_enabled()

    @polkit.enable_proxy
    def is_chkconfig_running(self):
        return self.chkconfig_interface.is_chkconfig_running()


class DBusSysVServiceProxy(DBusChkconfigServiceProxy):

    info_class = DBusSysVServiceInfoProxy

    def __init__(self, *p, **k):
        super(DBusSysVServiceProxy, self).__init__(*p, **k)
        self.sysv_interface = dbus.Interface(self.dbus_object,
                "org.fedoraproject.Config.Services.SysVService")

    @polkit.enable_proxy(authfail_result=None)
    def start(self):
        return self.sysv_interface.start()

    @polkit.enable_proxy(authfail_result=None)
    def stop(self):
        return self.sysv_interface.stop()

    @polkit.enable_proxy(authfail_result=None)
    def restart(self):
        return self.sysv_interface.restart()

    @polkit.enable_proxy(authfail_result=None)
    def reload(self):
        return self.sysv_interface.reload()

    @property
    @polkit.enable_proxy
    def status(self):
        return self.sysv_interface.get_status()

    @property
    @polkit.enable_proxy
    def status_updates_running(self):
        return self.sysv_interface.get_status_updates_running()

    @polkit.enable_proxy
    def _get_runlevels(self):
        if not hasattr(self, "_runlevels"):
            self._runlevels = HookableSet()
            self._runlevels.add_hook(self._save_runlevels)
        self._runlevels.hooks_enabled = False
        self._runlevels.clear()
        self._runlevels.update(self.sysv_interface.get_runlevels())
        self._runlevels.hooks_enabled = True
        return self._runlevels

    def _set_runlevels(self, runlevels):
        self.runlevels
        if self._runlevels != runlevels:
            self._runlevels.freeze_hooks()
            self._runlevels.clear()
            self._runlevels.update(runlevels)
            self._runlevels.thaw_hooks()

    @polkit.enable_proxy(authfail_result=None)
    def _save_runlevels(self):
        return self.sysv_interface.set_runlevels(list(self._runlevels))

    runlevels = property(_get_runlevels, _set_runlevels)


SysVService = DBusSysVServiceProxy


class DBusXinetdServiceProxy(DBusChkconfigServiceProxy):

    info_class = DBusXinetdServiceInfoProxy

    def __init__(self, *p, **k):
        super(DBusXinetdServiceProxy, self).__init__(*p, **k)
        self.xinetd_interface = dbus.Interface(self.dbus_object,
                "org.fedoraproject.Config.Services.XinetdService")


XinetdService = DBusXinetdServiceProxy
