#!/usr/bin/python
# -*- coding: utf-8 -*-
# scservices.dbus.service.services: DBus wrappers for services
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

import dbus.service
import slip.dbus.service

import scservices.core.services as services

from scservices.dbus import dbus_service_name

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

    @dbus.service.method (dbus_interface = dbus_service_name + ".Service", in_signature = "", out_signature = "")
    def save (self):
        raise NotImplementedError

##############################################################################

class DBusChkconfigService (DBusService):
    @dbus.service.method (dbus_interface = dbus_service_name + ".ChkconfigService", in_signature = "", out_signature = "")
    def enable (self):
        self.service.enable ()

    @dbus.service.method (dbus_interface = dbus_service_name + ".ChkconfigService", in_signature = "", out_signature = "")
    def disable (self):
        self.service.disable ()

    @dbus.service.method (dbus_interface = dbus_service_name + ".ChkconfigService", in_signature = "", out_signature = "b")
    def get_enabled (self):
        return self.service.get_enabled ()

##############################################################################

class DBusSysVService (DBusChkconfigService):
    # FIXME
    def save (self, runlevels):
        pass

    @dbus.service.method (dbus_interface = dbus_service_name + ".SysVService", in_signature = "", out_signature = "")
    def start (self):
        self.service.start ()

    @dbus.service.method (dbus_interface = dbus_service_name + ".SysVService", in_signature = "", out_signature = "")
    def stop (self):
        self.service.stop ()

    @dbus.service.method (dbus_interface = dbus_service_name + ".SysVService", in_signature = "", out_signature = "")
    def restart (self):
        self.service.restart ()

    @dbus.service.method (dbus_interface = dbus_service_name + ".SysVService", in_signature = "", out_signature = "")
    def reload (self):
        self.service.reload ()

    @dbus.service.method (dbus_interface = dbus_service_name + ".SysVService", in_signature = "", out_signature = "i")
    def get_status (self):
        return self.service.status

    @dbus.service.method (dbus_interface = dbus_service_name + ".SysVService", in_signature = "", out_signature = "i")
    def get_status_updates_running (self):
        return self.service.status_updates_running

    @dbus.service.method (dbus_interface = dbus_service_name + ".SysVService", in_signature = "", out_signature = "s")
    def get_shortdescription (self):
        if self.service.info.shortdescription:
            return self.service.info.shortdescription
        else:
            return ""

    @dbus.service.method (dbus_interface = dbus_service_name + ".SysVService", in_signature = "", out_signature = "s")
    def get_description (self):
        if self.service.info.description:
            return self.service.info.description
        else:
            return ""

    @dbus.service.method (dbus_interface = dbus_service_name + ".SysVService", in_signature = "", out_signature = "ai")
    def get_runlevels (self):
        return list (self.service.runlevels)

##############################################################################

class DBusXinetdService (DBusChkconfigService):
    @dbus.service.method (dbus_interface = dbus_service_name + ".XinetdService", in_signature = "b", out_signature = "")
    def save (self, enabled):
        self.service.enabled = enabled
        self.service.save ()
    
    @dbus.service.method (dbus_interface = dbus_service_name + ".XinetdService", in_signature = "", out_signature = "s")
    def get_description (self):
        if self.service.info.description:
            return self.service.info.description
        else:
            return ""

