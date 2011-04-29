# -*- coding: utf-8 -*-

# scservices.core.systemd.unit: DBUS wrapper for systemd units
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

import re
from collections import defaultdict
from warnings import warn

import gobject

import dbus
#import slip.dbus.polkit as polkit

import gettext
_ = lambda x: gettext.ldgettext('system-config-services', x)

import constants.dbus

class SystemDUnitTypelessError(ValueError):
    pass


class SystemDUnitUnknownTypeWarning(RuntimeWarning):
    pass


class SystemDUnitBase(gobject.GObject):
    pass


class SystemDUnitMeta(gobject.GObjectMeta):

    unit_type_to_class = {}

    def __new__(meta, name, bases, dct):
        unit_type = dct['unit_type']
        cls = gobject.GObjectMeta.__new__(meta, name, bases, dct)
        SystemDUnitMeta.unit_type_to_class[unit_type] = cls
        return cls


class SystemDUnit(gobject.GObject):

    __metaclass__ = SystemDUnitMeta

    unit_type = 'unit'

    __bus_instances = defaultdict(dict)
    __bus_signal_matches = {}

    unit_id_encoding_re = re.compile(r'\\x(?P<hexenc>[0-9A-Fa-f][0-9A-Fa-f])')

    def __new__(cls, manager, unit_id, bus_path):
        try:
            unit_type = unit_id.rsplit(".", 1)[1]
        except IndexError:
            raise SystemDUnitTypelessError("Unit id '%s' is typeless" % unit_id)

        try:
            unit_cls = SystemDUnitMeta.unit_type_to_class[unit_type]
        except KeyError:
            warn("Unit id '%s' is of unknown type '%s'" % (unit_id, unit_type),
                    SystemDUnitUnknownTypeWarning, 2)
            unit_cls = SystemDUnit

        return super(SystemDUnit, cls).__new__(unit_cls)

    def __init__(self, manager, unit_id, bus_path):
        super(SystemDUnit, self).__init__()
        self.manager = manager
        self.bus = manager.bus

        self.unit_id = unit_id

        # the name is the unit_id without the unit type, unquoted
        unit_name_encoded = unit_id.rsplit(".", 1)[0]
        self.name = self.unit_id_encoding_re.sub(
                lambda x: chr(int(x.group('hexenc'), 16)), unit_name_encoded)

        self.bus_path = bus_path
        self.bus_object = self.bus.get_object(constants.dbus.service_name,
                self.bus_path)

        self.unit_interface = dbus.Interface(self.bus_object,
                constants.dbus.unit_interface)

        self.properties_interface = dbus.Interface(self.bus_object,
                constants.dbus.properties_interface)

        if SystemDUnit.__bus_instances[self.bus].has_key(bus_path):
            raise ValueError("duplicate bus path: %s" % bus_path)

        SystemDUnit.__bus_instances[self.bus][bus_path] = self

        # connecting to signals on each unit object would result in a
        # org.freedesktop.DBus.Error.LimitsExceeded error, so we won't do this:
        #
        # self.properties_interface.connect_to_signal('PropertiesChanged',
        #         self.on_properties_changed)
        #
        # but rather that instead (once for each bus):

        if self.bus not in SystemDUnit.__bus_signal_matches:
            def on_properties_changed_for_bus(interface, changed_properties,
                    invalidated_properties, unit_path):
                SystemDUnit.on_properties_changed(self.bus, interface,
                        changed_properties, invalidated_properties, unit_path)

            SystemDUnit.__bus_signal_matches[self.bus] = (
                    self.bus.add_signal_receiver(
                        on_properties_changed_for_bus,
                        path_keyword='unit_path',
                        signal_name='PropertiesChanged',
                        dbus_interface=constants.dbus.properties_interface,
                        bus_name=constants.dbus.service_name))

    def __del__(self):
        # deal with exceptions raised in __init__()
        if self.bus_path not in SystemDUnit.__bus_instances[self.bus]:
            return

        del SystemDUnit.__bus_instances[self.bus][self.bus_path]
        if not len(SystemDUnit.__bus_instances[self.bus]):
            SystemDUnit.__bus_signal_matches[self.bus].remove()
            del SystemDUnit.__bus_signal_matches[self.bus]

    def __repr__(self):
        _repr = super(SystemDUnit, self).__repr__()
        return "%s '%s'%s" % (_repr[:-1], self.unit_id, _repr[-1:])

    @classmethod
    def on_properties_changed(cls, bus, interface, changed_properties,
            invalidated_properties, unit_path):
        if interface != constants.dbus.unit_interface:
            return
        unit = SystemDUnit.__bus_instances[bus][unit_path]
        unit.emit('properties_changed', interface, changed_properties,
                invalidated_properties)

    @property
    def ActiveState(self):
        try:
            return self.properties_interface.Get(constants.dbus.unit_interface,
                    'ActiveState')
        except dbus.DBusException, e:
            if e.get_dbus_name() == 'org.freedesktop.DBus.Error.UnknownObject':
                return 'unknown'
            else:
                raise

    @property
    def LoadState(self):
        try:
            return self.properties_interface.Get(constants.dbus.unit_interface,
                    'LoadState')
        except dbus.DBusException, e:
            if e.get_dbus_name() == 'org.freedesktop.DBus.Error.UnknownObject':
                return 'unknown'
            else:
                raise

    @property
    def SubState(self):
        try:
            return self.properties_interface.Get(constants.dbus.unit_interface,
                    'SubState')
        except dbus.DBusException, e:
            if e.get_dbus_name() == 'org.freedesktop.DBus.Error.UnknownObject':
                return 'unknown'
            else:
                raise

    @property
    def Description(self):
        try:
            return self.properties_interface.Get(constants.dbus.unit_interface,
                    'Description')
        except dbus.DBusException, e:
            if e.get_dbus_name() == 'org.freedesktop.DBus.Error.UnknownObject':
                return _("Error while getting description.")
            else:
                raise

systemd_unit_properties_changed_signal = (
        gobject.signal_new('properties_changed', SystemDUnit,
            gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            [gobject.TYPE_STRING, gobject.TYPE_PYOBJECT,
                gobject.TYPE_PYOBJECT]))


class SystemDAutomount(SystemDUnit):
    unit_type = 'automount'


class SystemDDevice(SystemDUnit):
    unit_type = 'device'


class SystemDMount(SystemDUnit):
    unit_type = 'mount'


class SystemDPath(SystemDUnit):
    unit_type = 'path'


class SystemDService(SystemDUnit):
    unit_type = 'service'


class SystemDSocket(SystemDUnit):
    unit_type = 'socket'


class SystemDSwap(SystemDUnit):
    unit_type = 'swap'


class SystemDTarget(SystemDUnit):
    unit_type = 'target'


class SystemDTimer(SystemDUnit):
    unit_type = 'timer'


if __name__ == '__main__':
    import gobject
    import slip.dbus

    from manager import SystemDManager

    mainloop = gobject.MainLoop()
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    slip.dbus.mainloop.mainloop_class = slip.dbus.mainloop.GlibMainLoop

    system_bus = slip.dbus.SystemBus()

    systemd_manager = SystemDManager(system_bus)

    slip.dbus.service.set_mainloop(mainloop)

    mainloop.run()

