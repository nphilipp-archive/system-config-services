#!/usr/bin/python

import gamin
import gobject

import dbus
import dbus.service
import dbus.servicehelper
import dbus.mainloop.glib

import serviceherders
from serviceherders import SVC_ADDED, SVC_DELETED, SVC_CONF_UPDATING, SVC_CONF_CHANGED, SVC_STATUS_UPDATING, SVC_STATUS_CHANGED

import services
from services import SVC_STATUS_REFRESHING, SVC_STATUS_UNKNOWN, SVC_STATUS_STOPPED, SVC_STATUS_RUNNING, SVC_STATUS_DEAD
from services import SVC_ENABLED_REFRESHING, SVC_ENABLED_YES, SVC_ENABLED_NO, SVC_ENABLED_CUSTOM

class DBusService (dbus.servicehelper.TimeoutObject):
    def __init__ (self, bus, object_path, service):
        dbus.servicehelper.TimeoutObject.__init__ (self, bus, object_path)

        self.service = service

    @dbus.service.method (dbus_interface = "org.fedoraproject.Config.Services.Service", in_signature = "", out_signature = "s")
    def ping (self):
        return "pong"

class DBusServiceHerder (dbus.servicehelper.TimeoutObject):
    def __init__ (self, bus, object_path, herder):
        dbus.servicehelper.TimeoutObject.__init__ (self, bus, object_path)

        self.herder = herder
        self.herder.subscribe (self.on_services_changed)

        self.services_dbusservices = {}

    @dbus.service.method (dbus_interface = "org.fedoraproject.Config.Services.ServiceHerder", in_signature = "", out_signature = "s")
    def ping (self):
        return "pong"

    def on_services_changed (self, change, service):
        if change == SVC_ADDED:
            self.on_service_added (service)
        elif change == SVC_DELETED:
            self.on_service_deleted (service)

        self.notify (change, service.name)

    def on_service_added (self, service):
        if service in self.services_dbusservices:
            raise KeyError ("service %s added twice to %s" % (service, self))
        self.services_dbusservices[service] = DBusService (self.connection, self._service_object_path (service), service)

    def on_service_deleted (self, service):
        dbusservice = self.services_dbusservices[service]
        dbusservice.remove_from_connection (connection = self.connection, path = self._service_object_path (service))
        del self.services_dbusservices[service]

    @dbus.service.signal (dbus_interface = "org.fedoraproject.Config.Services.ServiceHerder.notify", signature = "us")
    def notify (self, change, servicename):
        pass

    def create_service (self, name):
        if name not in self.services.keys ():
            try:
                servicecls = services_dbusservices [self.service_class]
                serviceobj = servicecls (self.connection,
                        self._service_object_path (name),
                        name, self.mon, self)
                self.services[name] = serviceobj
                self.notify (SVC_ADDED, service = serviceobj)
            except services.InvalidServiceException:
                pass

    def _service_object_path (self, service):
        name = service.name.replace ('-', '_')
        return "%s/Services/%s" % (self._object_path, name)

def run_service ():
    mainloop = gobject.MainLoop()
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    system_bus = dbus.SystemBus()
    name = dbus.service.BusName("org.fedoraproject.Config.Services", system_bus)

    filemon = gamin.WatchMonitor ()
    filemon_fd = filemon.get_fd ()

    dbus_herder_objects = []

    for herder_cls in serviceherders.herder_classes:
        herder = herder_cls (filemon)
        dbus_herder_object = DBusServiceHerder (system_bus, "/org/fedoraproject/Config/Services/ServiceHerders/%s" % herder_cls.__name__, herder)
        dbus_herder_objects.append (dbus_herder_object)

    def filemon_handle_events (source, condition, data = None):
        filemon.handle_events ()
        return True

    gobject.io_add_watch (filemon_fd, gobject.IO_IN | gobject.IO_PRI, filemon_handle_events)

    dbus.servicehelper.set_mainloop (mainloop)
    print "Running system-config-services dbus service."
    mainloop.run ()

if __name__ == "__main__":
    run_service ()
