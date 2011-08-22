# -*- coding: utf-8 -*-

# scservices.core.systemd.manager: DBUS wrapper for systemd manager
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


import gobject

import dbus
import slip.dbus.polkit as polkit

import constants.dbus

from unit import SystemDUnit

class SystemDManager(gobject.GObject):

    def __init__(self, bus, use_polkit=True, subscribe=True):
        super(SystemDManager, self).__init__()
        self.bus = bus
        self.bus_path = constants.dbus.manager_path
        self.bus_object = bus.get_object(constants.dbus.service_name,
                self.bus_path)

        self.manager_interface = dbus.Interface(self.bus_object,
                constants.dbus.manager_interface)
        #self.manager_interface.connect_to_signal('JobNew', self.on_job_new)
        #self.manager_interface.connect_to_signal('JobRemoved', self.on_job_removed)
        self.manager_interface.connect_to_signal('UnitNew', self.on_unit_new)
        self.manager_interface.connect_to_signal('UnitRemoved', self.on_unit_removed)

        self.units = {}

        self.use_polkit = use_polkit

        if use_polkit:
            self.polkit_bus_path = constants.dbus.polkit_manager_path
            self.privileged_manager_object = bus.get_object(
                    constants.dbus.polkit_service_name, self.polkit_bus_path)
            self.privileged_manager_interface = dbus.Interface(
                    self.privileged_manager_object,
                    constants.dbus.manager_interface)
        else:
            self.privileged_manager_interface = self.manager_interface

        if subscribe:
            self.subscribe()

        self.discover_units()

    @polkit.enable_proxy
    def subscribe(self):
        return self.manager_interface.Subscribe()

    @polkit.enable_proxy
    def unsubscribe(self):
        return self.manager_interface.Unsubscribe()

    def discover_units(self):
        self.discovering = True
        self.emit('discovery_started')
        self.manager_interface.ListUnits(
                reply_handler=self.on_discover_units_reply,
                error_handler=self.on_discover_units_error)

    def on_discover_units_reply(self, units_data):
        for (unit_id, unit_desc, load_state, active_state, sub_state,
                following, unit_path, job_id, job_type, job_path) in units_data:
            self.on_unit_new(unit_id, unit_path)

        self.discovering = False
        self.emit('discovery_finished')

    def on_discover_units_error(self, *p, **k):
        self.discovering = False
        self.emit('discovery_failed')

    def on_unit_new(self, unit_id, unit_path):
        if unit_id in self.units:
            # unit might have slipped in during discovery
            return

        new_unit = SystemDUnit(self, unit_id, unit_path)

        self.units[unit_id] = new_unit

        self.emit('unit_new', new_unit)

    def on_unit_removed(self, unit_id, unit_path):
        try:
            removed_unit = self.units.pop(unit_id)
        except KeyError:
            # shield against units added/removed out of order
            pass
        else:
            removed_unit.remove()
            self.emit('unit_removed', removed_unit)

    @polkit.enable_proxy
    def RestartUnit(self, name, mode='replace'):
        return self.privileged_manager_interface.RestartUnit(name, mode)

    @polkit.enable_proxy
    def StartUnit(self, name, mode='replace'):
        return self.privileged_manager_interface.StartUnit(name, mode)

    @polkit.enable_proxy
    def StopUnit(self, name, mode='replace'):
        return self.privileged_manager_interface.StopUnit(name, mode)

    @polkit.enable_proxy
    def ReloadUnit(self, name, mode='replace'):
        return self.privileged_manager_interface.ReloadUnit(name, mode)

    @polkit.enable_proxy
    def ReloadOrRestartUnit(self, name, mode='replace'):
        return self.privileged_manager_interface.ReloadOrRestartUnit(name, mode)


systemd_manager_discovery_started_signal = (
        gobject.signal_new('discovery_started', SystemDManager,
            gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []))

systemd_manager_discovery_finished_signal = (
        gobject.signal_new('discovery_finished', SystemDManager,
            gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []))

systemd_manager_discovery_failed_signal = (
        gobject.signal_new('discovery_failed', SystemDManager,
            gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []))

systemd_manager_unit_new_signal = (
        gobject.signal_new('unit_new', SystemDManager,
            gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]))

systemd_manager_unit_removed_signal = (
        gobject.signal_new('unit_removed', SystemDManager,
            gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]))

if __name__ == '__main__':
    import gobject
    import slip.dbus

    mainloop = gobject.MainLoop()
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    slip.dbus.mainloop.mainloop_class = slip.dbus.mainloop.GlibMainLoop

    system_bus = slip.dbus.SystemBus()

    systemd_manager = SystemDManager(system_bus)

    def on_discovery_finished(manager):
        print "%r: discovery finished" % manager

    def on_discovery_failed(manager):
        print "%r: discovery failed" % manager

    systemd_manager.connect('discovery_finished', on_discovery_finished)
    systemd_manager.connect('discovery_failed', on_discovery_failed)

    def on_unit_new(manager, unit):
        print "%r: new unit %r" % (manager, unit)

    def on_unit_removed(manager, unit):
        print "%r: unit %r removed" % (manager, unit)

    systemd_manager.connect('unit_new', on_unit_new)
    systemd_manager.connect('unit_removed', on_unit_removed)

    slip.dbus.service.set_mainloop(mainloop)

    try:
        mainloop.run()
    except KeyboardInterrupt:
        pass

