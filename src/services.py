# -*- coding: utf-8 -*-
# services.py: services
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

import os
import copy
import re
import time
import gobject
import gamin

from util import getstatusoutput
from asynccmd import *

from servicesinfo import *
import serviceherders

SVC_STATUS_REFRESHING = 0
SVC_STATUS_UNKNOWN = 1
SVC_STATUS_STOPPED = 2
SVC_STATUS_RUNNING = 3
SVC_STATUS_DEAD = 4

SVC_ENABLED_REFRESHING = 0
SVC_ENABLED_YES = 1
SVC_ENABLED_NO = 2
SVC_ENABLED_CUSTOM = 3

##############################################################################

class InvalidServiceException (Exception):
    pass

##############################################################################

class Service (object):
    """Represents an abstract service."""
    def __init__ (self, name, mon, herder):
        super (Service, self).__init__ ()
        self.name = name
        self.mon = mon
        self.herder = herder
        self._asynccmdqueue = AsyncCmdQueue ()
        self.conf_updates_running = 0

    def __repr__ (self):
        return '<%s.%s object at %s: "%s">' % (self.__class__.__module__, self.__class__.__name__, hex (id (self)), self.name)

    def notify_herder (self, change):
        """Notify the herder of a change."""
        if self.herder:
            self.herder.notify (change, self)

    def load (self):
        """Load configuration from disk synchronously."""
        mainloop = gobject.MainLoop ()
        self._async_load (self._sync_load_finished, mainloop)
        mainloop.run ()

    def _sync_load_finished (self, mainloop, __exception__ = None):
        mainloop.quit ()
        if __exception__ == None:
            self.valid = True
        else:
            self.valid = False

    def async_load (self):
        """Load configuration from disk asynchronously, notify herder on completion."""
        self.notify_herder (serviceherders.SVC_CONF_UPDATING)
        return self._async_load (self._async_load_finished)

    def _async_load_finished (self, __exception__ = None):
        self.notify_herder (serviceherders.SVC_CONF_CHANGED)

    def _async_load_ready (self, cmd, callback, *p, **k):
        try:
            self._async_load_process (cmd)
        except Exception, e:
            k['__exception__'] = e
        self.conf_updates_running -= 1
        callback (*p, **k)

    def _async_load (self, callback, *p, **k):
        """Load configuration from disk asynchronously."""
        raise NotImplementedError

    def _async_load_process (self, cmd):
        """Process asynchronously loaded configuration."""
        raise NotImplementedError

    def save (self):
        """Save configuration to disk."""
        raise NotImplementedError

    def is_dirty (self):
        """Check if a service is dirty, i.e. changed and not saved."""
        raise NotImplementedError

##############################################################################

class ChkconfigService (Service):
    """Represents an abstract service handled with chkconfig."""

    def _change_enablement (self, change):
        # no callback, we let the herder handle that
        self._asynccmdqueue.queue ('env LC_ALL=C /sbin/chkconfig "%s" "%s"' % (self.name, change))

    def enable (self):
        """Enable this service."""
        self._change_enablement ('on')

    def disable (self):
        """Disable this service."""
        self._change_enablement ('off')

##############################################################################

class SysVService (ChkconfigService):
    """Represents a service handled by SysVinit."""

    init_list_re = re.compile (r'^(?P<name>\S+)\s+0:(?P<r0>off|on)\s+1:(?P<r1>off|on)\s+2:(?P<r2>off|on)\s+3:(?P<r3>off|on)\s+4:(?P<r4>off|on)\s+5:(?P<r5>off|on)\s+6:(?P<r6>off|on)\s*$')

    no_chkconfig_re = re.compile (r'^service (?P<name>.*) does not support chkconfig$')
    chkconfig_error_re = re.compile (r'^error reading information on service (?P<name>.*):.*$')
    chkconfig_unconfigured_re = re.compile (r"^service (?P<name>.*) supports chkconfig, but is not referenced in any runlevel \(run 'chkconfig --add (?P=name)'\)$")

    _fallback_default_runlevels = set ((2, 3, 4, 5))

    def __init__ (self, name, mon, herder):
        super (SysVService, self).__init__ (name, mon, herder)

        try:
            self.info = SysVServiceInfo (name)
        except InvalidServiceInfoException:
            raise InvalidServiceException

        self.runlevels = set ()
        self.runlevels_ondisk = set ()
        self.configured = False

        self.status_updates_running = 0
        self.status = SVC_STATUS_UNKNOWN
        self.status_output = None

        self.valid = False

        self._status_asynccmdqueue = AsyncCmdQueue ()

        if self.info.pidfiles:
            self.pidfiles = set (self.info.pidfiles)
            self.pids = set ()
            self.pids_pidfiles = {}

            for file in self.info.pidfiles:
                self.mon.watch_file (file, self._pidfile_changed)
        else:
            # no pidfile(s), watch /var/lock/subsys/...
            self.mon.watch_file ("/var/lock/subsys/%s" % self.name, self._var_lock_subsys_changed)

    def _async_load (self, callback, *p, **k):
        """Load configuration from disk asynchronously."""
        p = (callback, ) + p
        self._asynccmdqueue.queue ('env LC_ALL=C /sbin/chkconfig --list "%s"' % self.name, combined_stdout = True, ready_cb = self._async_load_ready, ready_args = p, ready_kwargs = k)
        self.conf_updates_running += 1

    def _async_load_process (self, cmd):
        """Process asynchronously loaded configuration."""
        exitcode = cmd.exitcode
        output = cmd.output

        if exitcode != 0:
            if self.no_chkconfig_re.match (output) \
                or self.chkconfig_error_re.match (output):
                raise InvalidServiceException (output)
            elif self.chkconfig_unconfigured_re.match (output):
                self.configured = False
                return
            else:
                # service might have been deleted, let the herder take care of it
                return

        m = self.init_list_re.match (output)
        if not m or m.group ('name') != self.name:
            raise output
        self.runlevels = set ()
        for runlevel in xrange (1, 6):
            if m.group ("r%d" % runlevel) == 'on':
                self.runlevels.add (runlevel)
        self.runlevels_ondisk = copy.copy (self.runlevels)
        self.configured = True
        self.conf_updates_running -= 1

    def save (self):
        """Save configuration to disk."""
        runlevel_changes = { 'on': [], 'off': [] }

        for i in xrange (0, 7):
            if (i in self.runlevels) != (i in self.runlevels_ondisk):
                runlevel_changes[(i in self.runlevels) and 'on' or 'off'].append (i)

        for what in ('on', 'off'):
            if not len (runlevel_changes[what]):
                continue
            (status, output) = getstatusoutput ('env LC_ALL=C /sbin/chkconfig --level %s %s %s 2>&1' % (''.join (runlevel_changes[what]), self.name, what))
            if status != 0:
                raise OSError ("Saving service '%s' failed, command was 'LC_ALL=C /sbin/chkconfig --level %s %s %s'.\nOutput was:\n%s" % (self.name, ''.join (runlevel_changes[what]), self.name, what, output))

        self.runlevels_ondisk = copy.copy (self.runlevels)
        self.configured = True

    def _var_lock_subsys_changed (self, path, action, *p):
        if action != gamin.GAMEndExist:
            self.async_status_update ()

    def _pidfile_changed (self, path, action, *p):
        if action in (gamin.GAMCreated, gamin.GAMChanged, gamin.GAMExists):
            self._watch_pidfile (path)
        elif action == gamin.GAMDeleted:
            self._unwatch_pidfile (path)

    def _watch_pidfile (self, path):
        self._unwatch_pidfile (path)
        try:
            pidfile = open (path, "r")
        except IOError:
            return

        for line in pidfile:
            for _pid in line.split ():
                try:
                    pid = int (_pid)
                    self._watch_pid (pid, path)
                except ValueError:
                    pass

        pidfile.close ()

    def _unwatch_pidfile (self, path):
        unwatch_pids = set ()
        for pid in self.pids:
            if path in self.pids_pidfiles[pid]:
                unwatch_pids.add (pid)
        for pid in unwatch_pids:
            self._unwatch_pid (pid, path)

    def _proc_pid_changed (self, path, action, *p):
        if action != gamin.GAMEndExist:
            self.async_status_update ()
        
    def _watch_pid (self, pid, pidfile):
        if pid not in self.pids:
            self.pids.add (pid)
            self.mon.watch_file ("/proc/%d" % pid, self._proc_pid_changed)
        if not self.pids_pidfiles.has_key (pid):
            self.pids_pidfiles[pid] = set ()
        self.pids_pidfiles[pid].add (pidfile)

    def _unwatch_pid (self, pid, pidfile):
        self.pids_pidfiles[pid].discard (pidfile)
        if len (self.pids_pidfiles[pid]) == 0:
            del self.pids_pidfiles[pid]
            self.pids.discard (pid)
            self.mon.stop_watch ("/proc/%d" % pid)

    def async_status_update (self):
        """Determine service status asynchronously."""
        return self._async_status_update (self._async_status_update_finished)

    def _async_status_update_finished (self):
        self.notify_herder (serviceherders.SVC_STATUS_CHANGED)

    def _async_status_update (self, callback, *p, **k):
        p = (callback, ) + p
        self._status_asynccmdqueue.queue ('env LC_ALL=C /sbin/service \"%s\" status' % self.name, combined_stdout = True, ready_cb = self._status_update_ready, ready_args = p, ready_kwargs = k)
        self.status_updates_running += 1
        self.status = SVC_STATUS_REFRESHING

    def _status_update_ready (self, cmd, callback, *p, **k):
        self.status_updates_running -= 1
        if self.status_updates_running <= 0:
            self.status_updates_running = 0
            self.status = SVC_STATUS_UNKNOWN
        self._status_update_process (cmd)
        callback (*p, **k)

    def _status_update_process (self, cmd):
        """Process asynchronously determined service status."""
        exitcode = cmd.exitcode

        if exitcode == 0:
            self.status = SVC_STATUS_RUNNING
        elif exitcode == 1 or exitcode == 2:
            self.status = SVC_STATUS_DEAD
        elif exitcode == 3:
            self.status = SVC_STATUS_STOPPED
        else:
            self.status = SVC_STATUS_UNKNOWN

        #print "%s: %s: %d" % (cmd, self.name, self.status)
        self.status_output = cmd.output

    def is_dirty (self):
        """Determines if the configuration of a service is saved or not."""
        return self.runlevels != self.runlevels_ondisk

    def is_enabled (self):
        """Determines the enablement state of a service."""
        if self.conf_updates_running > 0:
            return SVC_ENABLED_REFRESHING
        if len (self.runlevels) == 0:
            return SVC_ENABLED_NO
        #if len (self.info.startrunlevels) > 0 \
        #        and self.runlevels == self.info.startrunlevels \
        #        or self.runlevels == self._fallback_default_runlevels:
        if self.runlevels == self._fallback_default_runlevels:
            return SVC_ENABLED_YES
        else:
            return SVC_ENABLED_CUSTOM

    def _change_status (self, change):
        self.status = SVC_STATUS_REFRESHING

        # no callback, we let the herder handle that
        self._asynccmdqueue.queue ('env LC_ALL=C /sbin/service "%s" "%s"' % (self.name, change))

    def start (self):
        """Start this service."""
        self._change_status ('start')

    def stop (self):
        """Stop this service."""
        self._change_status ('stop')

    def restart (self):
        """Restart this service."""
        self._change_status ('restart')

##############################################################################

class XinetdService (ChkconfigService):
    """Represents a service handled by xinetd."""

    xinetd_list_re = re.compile (r'^(?P<name>\S+)\s+(?P<enabled>off|on)\s*$')

    def __init__ (self, name, mon, herder):
        super (XinetdService, self).__init__ (name, mon, herder)

        try:
            self.info = XinetdServiceInfo (name)
        except InvalidServiceInfoException:
            raise InvalidServiceException

        self.enabled = None
        self.enabled_ondisk = None

        self.load ()

    def _async_load (self, callback, *p, **k):
        """Load configuration from disk asynchronously."""

        p = (callback, ) + p

        self._asynccmdqueue.queue ('env LC_ALL=C /sbin/chkconfig --list %s' % self.name, combined_stdout = True, ready_cb = self._async_load_ready, ready_args = p, ready_kwargs = k)
        self.conf_updates_running += 1

    def _async_load_process (self, cmd):
        """Process asynchronously loaded configuration."""
        exitcode = cmd.exitcode
        output = cmd.output

        if exitcode != 0:
            if self.no_chkconfig_re.match (output) \
                or self.chkconfig_error_re.match (output):
                raise InvalidServiceException (output)
            elif self.chkconfig_unconfigured_re.match (output):
                self.configured = False
                return
            else:
                # service might have been deleted, let the herder take care of it
                return

        m = self.xinetd_list_re.match (output)
        if not m or m.group ('name') != self.name:
            raise output
        self.enabled = m.group ('enabled') == "on"
        self.enabled_ondisk = self.enabled

    def save (self):
        """Save configuration to disk."""
        (status, output) = getstatusoutput ('LC_ALL=C /sbin/chkconfig %s %s 2>/dev/null' % (self.name, self.enabled and 'on' or 'off'))
        if status != 0:
            raise OSError ("Saving service '%s' failed, command was 'LC_ALL=C /sbin/chkconfig %s %s 2>/dev/null'." % (self.name, self.name, self.enabled and 'on' or 'off'))
        self.enabled_ondisk = self.enabled

    def is_dirty (self):
        return self.enabled != self.enabled_ondisk

    def is_enabled (self):
        if self.conf_updates_running > 0:
            return SVC_ENABLED_REFRESHING
        return self.enabled and SVC_ENABLED_YES or SVC_ENABLED_NO

##############################################################################

service_classes = [ SysVService, XinetdService ]
