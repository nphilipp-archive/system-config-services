# -*- coding: utf-8 -*-

# scservices.dbus.service.services: DBus wrappers for services
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
# Nils Philippsen <nils@redhat.com>

import dbus.service
import slip.dbus.service
import slip.dbus.polkit as polkit

import scservices.core.services as services

from scservices.dbus import dbus_service_name


class DBusService(slip.dbus.service.Object):

    default_polkit_auth_required = "org.fedoraproject.config.services.manage"

    def __new__(cls, bus_name, object_path, service, **k):
        srv_cls_dbussrv_cls = {services.SysVService: DBusSysVService,
                               services.XinetdService: DBusXinetdService}

        for (srv_cls, dbussrv_cls) in srv_cls_dbussrv_cls.iteritems():
            if isinstance(service, srv_cls):
                return super(DBusService, cls).__new__(dbussrv_cls)
        raise NotImplementedError

    def __init__(self, bus_name, object_path, service):
        slip.dbus.service.Object.__init__(self, bus_name, object_path)

        self.service = service


class DBusChkconfigService(DBusService):

    @polkit.require_auth("org.fedoraproject.config.services.manage")
    @dbus.service.method(dbus_interface=dbus_service_name +
                          ".ChkconfigService", in_signature="",
                         out_signature="")
    def enable(self):
        self.service.enable()

    @polkit.require_auth("org.fedoraproject.config.services.manage")
    @dbus.service.method(dbus_interface=dbus_service_name +
                          ".ChkconfigService", in_signature="",
                         out_signature="")
    def disable(self):
        self.service.disable()

    @polkit.require_auth("org.fedoraproject.config.services.info")
    @dbus.service.method(dbus_interface=dbus_service_name +
                          ".ChkconfigService", in_signature="",
                         out_signature="i")
    def get_enabled(self):
        return self.service.get_enabled()

    @polkit.require_auth("org.fedoraproject.config.services.info")
    @dbus.service.method(dbus_interface=dbus_service_name +
                          ".ChkconfigService", in_signature="",
                         out_signature="b")
    def is_chkconfig_running(self):
        return self.service.is_chkconfig_running()


class DBusSysVService(DBusChkconfigService):

    @polkit.require_auth("org.fedoraproject.config.services.manage")
    @dbus.service.method(dbus_interface=dbus_service_name + ".SysVService",
                         in_signature="", out_signature="")
    def start(self):
        self.service.start()

    @polkit.require_auth("org.fedoraproject.config.services.manage")
    @dbus.service.method(dbus_interface=dbus_service_name + ".SysVService",
                         in_signature="", out_signature="")
    def stop(self):
        self.service.stop()

    @polkit.require_auth("org.fedoraproject.config.services.manage")
    @dbus.service.method(dbus_interface=dbus_service_name + ".SysVService",
                         in_signature="", out_signature="")
    def restart(self):
        self.service.restart()

    @polkit.require_auth("org.fedoraproject.config.services.manage")
    @dbus.service.method(dbus_interface=dbus_service_name + ".SysVService",
                         in_signature="", out_signature="")
    def reload(self):
        self.service.reload()

    @polkit.require_auth("org.fedoraproject.config.services.info")
    @dbus.service.method(dbus_interface=dbus_service_name + ".SysVService",
                         in_signature="", out_signature="i")
    def get_status(self):
        return self.service.status

    @polkit.require_auth("org.fedoraproject.config.services.info")
    @dbus.service.method(dbus_interface=dbus_service_name + ".SysVService",
                         in_signature="", out_signature="i")
    def get_status_updates_running(self):
        return self.service.status_updates_running

    @polkit.require_auth("org.fedoraproject.config.services.info")
    @dbus.service.method(dbus_interface=dbus_service_name + ".SysVService",
                         in_signature="", out_signature="s")
    def get_shortdescription(self):
        if self.service.info.shortdescription:
            return self.service.info.shortdescription
        else:
            return ""

    @polkit.require_auth("org.fedoraproject.config.services.info")
    @dbus.service.method(dbus_interface=dbus_service_name + ".SysVService",
                         in_signature="", out_signature="s")
    def get_description(self):
        if self.service.info.description:
            return self.service.info.description
        else:
            return ""

    @polkit.require_auth("org.fedoraproject.config.services.info")
    @dbus.service.method(dbus_interface=dbus_service_name + ".SysVService",
                         in_signature="", out_signature="ai")
    def get_runlevels(self):
        return list(self.service.runlevels)

    @polkit.require_auth("org.fedoraproject.config.services.manage")
    @dbus.service.method(dbus_interface=dbus_service_name + ".SysVService",
                         in_signature="ai", out_signature="")
    def set_runlevels(self, runlevels):
        self.service.runlevels = set(runlevels)


class DBusXinetdService(DBusChkconfigService):

    @polkit.require_auth("org.fedoraproject.config.services.info")
    @dbus.service.method(dbus_interface=dbus_service_name + ".XinetdService",
                         in_signature="", out_signature="s")
    def get_description(self):
        if self.service.info.description:
            return self.service.info.description
        else:
            return ""


