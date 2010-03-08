# -*- coding: utf-8 -*-

# scservices.dbus.service: dbus backend service for system-config-services
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

import gobject
import dbus
import dbus.mainloop.glib
import gamin

import slip.dbus
import slip.dbus.service

from scservices.core.serviceherders import herder_classes
from scservices.dbus.service.serviceherder import DBusServiceHerder

from scservices.dbus import dbus_service_name, dbus_service_path


def run_service(persistent=False):
    mainloop = gobject.MainLoop()
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    slip.dbus.mainloop.mainloop_class = slip.dbus.mainloop.GlibMainLoop
    system_bus = slip.dbus.SystemBus()
    name = dbus.service.BusName(dbus_service_name, system_bus)

    filemon = gamin.WatchMonitor()
    filemon_fd = filemon.get_fd()

    dbus_herder_objects = []

    for herder_cls in herder_classes:
        herder = herder_cls(filemon)
        dbus_herder_object = DBusServiceHerder(name, dbus_service_path +
                 "/ServiceHerders/%s" % herder_cls.__name__,
                herder, persistent=persistent)
        dbus_herder_objects.append(dbus_herder_object)

    def filemon_handle_events(source, condition, data=None):
        filemon.handle_events()
        return True

    gobject.io_add_watch(filemon_fd, gobject.IO_IN | gobject.IO_PRI,
                         filemon_handle_events)

    slip.dbus.service.set_mainloop(mainloop)
    print "Running system-config-services dbus service at '%s'." % \
         dbus_service_name
    mainloop.run()


if __name__ == "__main__":
    import sys
    if "--persistent" in sys.argv[1:]:
        persistent = True
    else:
        persistent = False
    run_service(persistent=persistent)
