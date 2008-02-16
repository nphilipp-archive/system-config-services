# -*- coding: utf-8 -*-
# serviceherders.py: herders for services
#
# Copyright © 2007, 2008 Red Hat, Inc.
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

"""Keep track of added, deleted and changed services."""

import copy
import os
import time
import re
import gobject
import gamin

import services

SVC_ADDED = 0
SVC_DELETED = 1
SVC_CONF_UPDATING = 2
SVC_CONF_CHANGED = 3
SVC_STATUS_UPDATING = 4
SVC_STATUS_CHANGED = 5
SVC_LAST = 6

def gam_action_to_str (action):
    try:
        return {
                gamin.GAMAcknowledge: 'acknowledged',
                gamin.GAMChanged: "changed",
                gamin.GAMCreated: "created",
                gamin.GAMDeleted: "deleted",
                gamin.GAMEndExist: "endExist",
                gamin.GAMExists: "exists",
                gamin.GAMMoved: "moved",
                gamin.GAMStartExecuting: "start executing",
                gamin.GAMStopExecuting: "stop executing"
                }[action]
    except KeyError:
        return "unknown(%d)" % action

def on_dir_changed (path, action, data):
    (self, dir) = data
    self.on_dir_changed (path, action, dir)

def on_file_changed (path, action, self):
    self.on_file_changed (path, action)

class ServiceHerder (object):
    """abstract service herder"""

    service_class = services.Service

    watch_directories = []
    watch_files = []

    def __new__ (cls, *p, **k):
        #print "%s.__new__ ()" % cls
        if not '_the_instance' in cls.__dict__:
            cls._the_instance = object.__new__ (cls)
            cls._the_instance.__initialize__ (*p, **k)
        return cls._the_instance

    def __initialize__ (self, mon):
        """mon: a gamin WatchMonitor instance"""
        #print "%s.__initialize__ ()" % self
        super (ServiceHerder, self).__init__ ()

        self.services = {}
        self.subscribers = set ()

        self.mon = mon
        self.start_watching ()

    def start_watching (self):
        #print "%s.start_watching ()" % self
        for dir in self.watch_directories:
            #print "    dir:", dir
            self.mon.watch_directory (dir, on_dir_changed, (self, dir))
        for file in self.watch_files:
            #print "    file:", file
            self.mon.watch_file (file, on_file_changed, self)

    def create_service (self, name):
        #print "%s.create_service (%s)" % (self, name)
        if name not in self.services.keys ():
            try:
                serviceobj = self.service_class (name, self.mon)
                self.services[name] = serviceobj
                self.notify (SVC_ADDED, service = serviceobj)
            except services.InvalidServiceException:
                pass

    def delete_service (self, name):
        if name in self.services.keys ():
            serviceobj = self.services[name]
            self.notify (SVC_DELETED, service = serviceobj)
            del self.services[name]

    def on_dir_changed (self, path, action, dir):
        raise NotImplementedError
        #print "on_dir_changed (%s, %s, %s, %s)" % (self, path, gam_action_to_str (action), dir)

    def on_file_changed (self, path, action):
        raise NotImplementedError
        #print "on_file_changed (%s, %s, %s)" % (self, path, gam_action_to_str (action))

    class _Subscriber (object):
        def __init__ (self, remote_method_or_function, p, k):
            self.remote_method_or_function = remote_method_or_function
            self.p = p
            self.k = k

    def subscribe (self, remote_method_or_function, *p, **k):
        self.subscribers.add (self._Subscriber (remote_method_or_function, p, k))
        for service in self.services.itervalues ():
            remote_method_or_function (change = SVC_ADDED, service = service)

    def notify (self, change, service):
        for subscriber in self.subscribers:
            k = copy.copy (subscriber.k)
            k['service'] = service
            subscriber.remote_method_or_function (change = change,
                                                  *subscriber.p, **k)

class ChkconfigServiceHerder (ServiceHerder):
    """abstract service herder for services manageable by chkconfig"""
    
    service_class = services.ChkconfigService

    rpmbak_re = re.compile (r'.*\.rpm(?:orig|save|new)$')
    rpmtmp_re = re.compile (r'.*\;[0-9A-Fa-f]{8}$')

    def async_load_finished (self, service):
        self.notify (SVC_CONF_CHANGED, service = service)

class SysVServiceHerder (ChkconfigServiceHerder):
    """service herder for services started by SysVinit"""
    
    service_class = services.SysVService

    watch_directories = ['/etc/init.d', '/etc/rc0.d', '/etc/rc1.d', '/etc/rc2.d', '/etc/rc3.d', '/etc/rc4.d', '/etc/rc5.d', '/etc/rc6.d', '/var/lock/subsys']

    basename_re = re.compile (r'(?P<basename>[^/]*)$')
    runlevel_dirs_re = re.compile (r'^/etc/rc(?P<runlevel>[0-6]).d$')
    runlevel_services_re = re.compile (r'^(?P<startkill>[SK])[0-9]+(?P<name>.*)$')

    # cluster service activity for self.cluster_timeout milliseconds
    cluster_timeout = 1000

    def __init__ (self, mon):
        super (SysVServiceHerder, self).__init__ (mon)

        self.serviceClusterDelayBegins = {}
        self.serviceClusterDelayed = set ()

    def service_cluster_timeout (self, name):
        service_cluster_delayed = name in self.serviceClusterDelayed
        self.serviceClusterDelayed.discard (name)

        # A service might have been deleted in between or not supported by
        # chkconfig (halt, killall, single, local, reboot)
        try:
            service = self.services[name]
        except KeyError:
            try:
                del self.serviceClusterDelayBegins[name]
            except KeyError:
                pass
            return False

        # the service triggered an event in the meantime, tell the object to
        # synchronize itself and keep watching it
        if service_cluster_delayed:
            self.notify (SVC_CONF_UPDATING, service = service)
            service.async_load (self.async_load_finished, service)
            self.notify (SVC_STATUS_UPDATING, service = service)
            service.async_status_update (self.async_status_update_finished, service)
            return True
        
        # don't watch this particular service any longer
        del self.serviceClusterDelayBegins[name]
        return False

    def async_status_update_finished (self, service):
        self.notify (SVC_STATUS_CHANGED, service = service)

    def async_status_update (self, name):
        #print "%s.async_status_update (%s)" % (self, name)
        try:
            service = self.services[name]
        except KeyError:
            return
        self.notify (SVC_STATUS_UPDATING, service = service)
        service.async_status_update (self.async_status_update_finished, service)

    def on_dir_changed (self, path, action, dir):
        #print "%s.on_dir_changed (%s, %s, %s)" % (self, path, action, dir)
        basename = self.basename_re.search (path).group ('basename')
        if path == dir:
            # ignore state change on the directory
            return

        if self.rpmbak_re.match (path) or self.rpmtmp_re.match (path):
            # ignore RPM backup and temporary files
            return

        if dir == '/etc/init.d':
            # check for created/deleted services
            if action == gamin.GAMCreated or action == gamin.GAMExists:
                self.create_service (path)
            elif action == gamin.GAMDeleted:
                self.delete_service (path)
            return
        elif dir == '/var/lock/subsys':
            # check for lock files of services
            self.async_status_update (basename)
            return

        rlm = self.runlevel_dirs_re.match (dir)
        if rlm:
            sm = self.runlevel_services_re.match (path)
            if sm:
                runlevel = rlm.group ('runlevel')
                startkill = sm.group ('startkill')
                name = sm.group ('name')

                # A service might have been deleted in between or not supported
                # by chkconfig (halt, killall, single, local, reboot)
                try:
                    service = self.services[name]
                except KeyError:
                    return

                if not self.serviceClusterDelayBegins.has_key (name):
                    self.serviceClusterDelayBegins[name] = time.time ()
                    try:
                        gobject.timeout_add (self.cluster_timeout, self.service_cluster_timeout, name)
                        self.notify (SVC_CONF_UPDATING, service = service)
                        service.async_load (self.async_load_finished, service)
                        self.notify (SVC_STATUS_UPDATING, service = service)
                        service.async_status_update (self.async_status_update_finished, service)
                    except KeyError:
                        del self.serviceClusterDelayBegins[name]
                else:
                    self.serviceClusterDelayed.add (name)

class XinetdServiceHerder (ChkconfigServiceHerder):
    """service herder for services started by xinetd"""

    service_class = services.XinetdService

    watch_directories = ['/etc/xinetd.d']

    # delay recognition to avoid detecting temporary files
    delay_timeout = 1000

    def on_dir_changed (self, path, action, dir):
        if path == dir:
            # ignore state change on the directory
            return

        if self.rpmbak_re.match (path) or self.rpmtmp_re.match (path):
            # ignore RPM backup and temporary files
            return

        if action == gamin.GAMCreated or action == gamin.GAMExists:
            self.create_service_delayed (path)
        elif action == gamin.GAMDeleted:
            self.delete_service_delayed (path)
        elif action == gamin.GAMChanged:
            if self.services.has_key (path):
                service = self.services[name]
                self.notify (SVC_CONF_UPDATING, service = service)
                service.async_load (self.async_load_finished, service)

    def create_service_delayed (self, name):
        gobject.timeout_add (self.delay_timeout, self.create_service_cb, name)

    def create_service_cb (self, name):
        if os.access ("/etc/xinetd.d/%s" % name, os.F_OK):
            if self.services.has_key (name):
                service = self.services[name]
                self.notify (SVC_CONF_UPDATING, service = service)
                service.async_load (self.async_load_finished, service)
            else:
                self.create_service (name)
        return False

    def delete_service_delayed (self, name):
        gobject.timeout_add (self.delay_timeout, self.delete_service_cb, name)

    def delete_service_cb (self, name):
        if not os.access ("/etc/xinetd.d/%s" % name, os.F_OK):
            self.delete_service (name)
        return False

herder_classes = [ SysVServiceHerder, XinetdServiceHerder ]

__all__ = herder_classes + [ SVC_ADDED, SVC_DELETED, SVC_CONF_UPDATING, SVC_CONF_CHANGED, SVC_STATUS_UPDATING, SVC_STATUS_CHANGED ]
