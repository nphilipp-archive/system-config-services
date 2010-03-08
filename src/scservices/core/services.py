# -*- coding: utf-8 -*-

# services.py: services
#
# Copyright © 2007 - 2009 Red Hat, Inc.
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

import os
import sys
import re
import gobject
import gamin

from util import getstatusoutput
from asynccmd import AsyncCmdQueue

from servicesinfo import SysVServiceInfo, XinetdServiceInfo, InvalidServiceInfoException

# make pydoc work by working around cyclic dependency

try:
    import serviceherders
except AttributeError:
    pass

from slip.util.hookable import HookableSet

SVC_STATUS_REFRESHING = 0
SVC_STATUS_UNKNOWN = 1
SVC_STATUS_STOPPED = 2
SVC_STATUS_RUNNING = 3
SVC_STATUS_DEAD = 4

SVC_ENABLED_REFRESHING = 0
SVC_ENABLED_ERROR = 1
SVC_ENABLED_YES = 2
SVC_ENABLED_NO = 3
SVC_ENABLED_CUSTOM = 4


class InvalidServiceException(Exception):

    pass


class Service(object):

    """Represents an abstract service."""

    def __init__(self, name, mon, herder):

        super(Service, self).__init__()
        self.name = name
        self.mon = mon
        self.herder = herder
        self._asynccmdqueue = AsyncCmdQueue()
        self.conf_updates_running = 0

    def __repr__(self):
        return "<%s.%s object at %s: \"%s\">" % (self.__class__.__module__,
                self.__class__.__name__, hex(id(self)), self.name)

    def notify_herder(self, change):
        """Notify the herder of a change."""

        if self.herder:
            self.herder.notify(change, self)

    def load(self):
        """Load configuration from disk synchronously."""

        mainloop = gobject.MainLoop()
        self._async_load(self._sync_load_finished, mainloop)
        mainloop.run()

    def _sync_load_finished(self, mainloop, __exception__=None):
        mainloop.quit()
        if __exception__ == None:
            self.valid = True
        else:
            self.valid = False

    def async_load(self):
        """Load configuration from disk asynchronously, notify herder on completion."""

        self.notify_herder(serviceherders.SVC_CONF_UPDATING)
        return self._async_load(self._async_load_finished)

    def _async_load_finished(self, __exception__=None):
        self.notify_herder(serviceherders.SVC_CONF_CHANGED)

    def _async_load_ready(self, cmd, callback, *p, **k):
        try:
            self._async_load_process(cmd)
        except Exception, e:
            k["__exception__"] = e
        self.conf_updates_running -= 1
        callback(*p, **k)

    def _async_load(self, callback, *p, **k):
        """Load configuration from disk asynchronously."""

        raise NotImplementedError

    def _async_load_process(self, cmd):
        """Process asynchronously loaded configuration."""

        raise NotImplementedError


class ChkconfigService(Service):

    """Represents an abstract service handled with chkconfig."""

    _chkconfig_invocation = "LC_ALL=C /sbin/chkconfig"
    _chkconfig_version_re = \
        re.compile(r"^chkconfig\s+version\s+(?P<version>[\d\.]+)\s*$",
                   re.IGNORECASE)

    def __init__(self, name, mon, herder):

        super(ChkconfigService, self).__init__(name, mon, herder)
        self._chkconfig_running = 0

        if not hasattr(ChkconfigService, "chkconfig_version"):

            # determine chkconfig version, we only want to use some features
            # from certain versions on

            ckver_pipe = os.popen("%s -v" %
                                   ChkconfigService._chkconfig_invocation)
            for line in ckver_pipe:
                line = line.strip()
                m = ChkconfigService._chkconfig_version_re.match(line)
                if m:
                    version = m.group("version")
                    ChkconfigService.chkconfig_version = \
                            tuple(map(lambda x: int(x), version.split(".")))
                    break

            ckver_pipe.close()

    @property
    def chkconfig_invocation(self):
        if not hasattr(self.__class__, "_chkconfig_actual_invocation"):
            invoke = [ChkconfigService._chkconfig_invocation]

            # --type <sysv|xinetd> exists in 1.3.40 and later

            if ChkconfigService.chkconfig_version >= (1, 3, 40):
                invoke.append("--type %s" % self.chkconfig_type)

            self.__class__._chkconfig_actual_invocation = " ".join(invoke)

        return self.__class__._chkconfig_actual_invocation

    def is_chkconfig_running(self):
        return self._chkconfig_running > 0

    def _change_enablement_ready(self, cmd):
        self._chkconfig_running = max((0, self._chkconfig_running - 1))

    def _change_enablement(self, change):
        self._chkconfig_running += 1
        self._asynccmdqueue.queue("%s \"%s\" \"%s\""
                                   % (self.chkconfig_invocation, self.name,
                                  change), ready_cb=self._change_enablement_ready)

    def enable(self):
        """Enable this service."""

        self._change_enablement("on")

    def disable(self):
        """Disable this service."""

        self._change_enablement("off")

    def get_enabled(self):
        raise NotImplementedError


class SysVService(ChkconfigService):

    """Represents a service handled by SysVinit."""

    chkconfig_type = "sysv"

    init_list_re = \
        re.compile(r"^(?P<name>\S+)\s+0:(?P<r0>off|on)\s+1:(?P<r1>off|on)\s+"
                    "2:(?P<r2>off|on)\s+3:(?P<r3>off|on)\s+4:(?P<r4>off|on)\s+"
                    "5:(?P<r5>off|on)\s+6:(?P<r6>off|on)\s*$")

    no_chkconfig_re = \
        re.compile(r"^service (?P<name>.*) does not support chkconfig$")
    chkconfig_error_re = \
        re.compile(r"^error reading information on service (?P<name>.*):.*$")
    chkconfig_unconfigured_re = \
        re.compile(r"^service (?P<name>.*) supports chkconfig, but is not "
                    "referenced in any runlevel "
                    "\(run 'chkconfig --add (?P=name)'\)$")

    _fallback_default_runlevels = set((2, 3, 4, 5))

    def __init__(self, name, mon, herder):
        super(SysVService, self).__init__(name, mon, herder)

        try:
            self.info = SysVServiceInfo(name)
        except InvalidServiceInfoException:
            raise InvalidServiceException

        # property: self.runlevels = HookableSet ()

        self.configured = False

        self.status_updates_running = 0
        self.status = SVC_STATUS_UNKNOWN
        self.status_output = None

        self.valid = False

        self._status_asynccmdqueue = AsyncCmdQueue()

        if self.info.pidfiles:
            self.pidfiles = set(self.info.pidfiles)
            self.pids = set()
            self.pids_pidfiles = {}

            for file in self.info.pidfiles:
                self.mon.watch_file(file, self._pidfile_changed)
        else:

            # no pidfile(s), watch /var/lock/subsys/...

            self.mon.watch_file("/var/lock/subsys/%s" % self.name,
                                self._var_lock_subsys_changed)

    def _async_load(self, callback, *p, **k):
        """Load configuration from disk asynchronously."""

        p = (callback, ) + p
        self._asynccmdqueue.queue("%s --list \"%s\"" %
                                   (self.chkconfig_invocation, self.name),
                                  combined_stdout=True,
                                  ready_cb=self._async_load_ready,
                                  ready_args=p, ready_kwargs=k)
        self.conf_updates_running += 1

    def _async_load_process(self, cmd):
        """Process asynchronously loaded configuration."""

        exitcode = cmd.exitcode
        output = cmd.output

        if exitcode != 0:
            if self.no_chkconfig_re.match(output)\
                 or self.chkconfig_error_re.match(output):
                raise InvalidServiceException(output)
            elif self.chkconfig_unconfigured_re.match(output):
                self.configured = False
                return
            else:

                # the service might have been deleted, let the herder take care
                # of it

                return

        m = self.init_list_re.match(output)
        if not m or m.group("name") != self.name:
            raise output
        runlevels = set()
        for runlevel in xrange(1, 6):
            if m.group("r%d" % runlevel) == "on":
                runlevels.add(runlevel)

        # disable save hook temporarily to avoid endless loops

        self.runlevels.hooks_enabled = False
        self.runlevels.clear()
        self.runlevels.update(runlevels)
        self.runlevels.hooks_enabled = True

        self.configured = True
        self.conf_updates_running -= 1

    def _runlevels_save_hook(self):
        """Save runlevel configuration to disk."""

        runlevel_changes = {"on": [], "off": []}

        for i in xrange(0, 7):
            runlevel_changes[i in self._runlevels and "on" or "off"
                             ].append(str(i))

        for what in ("on", "off"):
            if not len(runlevel_changes[what]):
                continue
            (status, output) = getstatusoutput("%s --level %s %s %s 2>&1"
                     % (self.chkconfig_invocation,
                    "".join(runlevel_changes[what]), self.name, what))
            if status != 0:
                raise OSError("Saving service '%s' failed, command was "
                              "'%s --level %s %s %s'.\n"
                              "Output was:\n"
                              "%s" % (self.name, self.chkconfig_invocation,
                                      "".join(runlevel_changes[what]),
                                      self.name, what, output))

        self.configured = True

    def _get_runlevels(self):
        if not hasattr(self, "_runlevels"):
            self._runlevels = HookableSet()
            self._runlevels.add_hook(self._runlevels_save_hook)
        return self._runlevels

    def _set_runlevels(self, runlevels):
        self.runlevels
        if self._runlevels != runlevels:
            self._runlevels.freeze_hooks()
            self._runlevels.clear()
            self._runlevels.update(runlevels)
            self._runlevels.thaw_hooks()

    runlevels = property(_get_runlevels, _set_runlevels)

    def _var_lock_subsys_changed(self, path, action, *p):
        if action != gamin.GAMEndExist:
            self.async_status_update()

    def _pidfile_changed(self, path, action, *p):
        if action in (gamin.GAMCreated, gamin.GAMChanged, gamin.GAMExists):
            self._watch_pidfile(path)
        elif action == gamin.GAMDeleted:
            if len(self.pids) == 0:
                self.async_status_update()
            self._unwatch_pidfile(path)

    def _watch_pidfile(self, path):
        self._unwatch_pidfile(path)
        try:
            pidfile = open(path, "r")
        except IOError:
            return

        for line in pidfile:
            for _pid in line.split():
                try:
                    pid = int(_pid)
                    self._watch_pid(pid, path)
                except ValueError:
                    pass

        pidfile.close()

    def _unwatch_pidfile(self, path):
        unwatch_pids = set()
        for pid in self.pids:
            if path in self.pids_pidfiles[pid]:
                unwatch_pids.add(pid)
        for pid in unwatch_pids:
            self._unwatch_pid(pid, path)

    def _proc_pid_changed(self, path, action, *p):
        if action != gamin.GAMEndExist:
            self.async_status_update()

    def _watch_pid(self, pid, pidfile):
        if pid not in self.pids:
            self.pids.add(pid)
            self.mon.watch_file("/proc/%d" % pid, self._proc_pid_changed)
        if not self.pids_pidfiles.has_key(pid):
            self.pids_pidfiles[pid] = set()
        self.pids_pidfiles[pid].add(pidfile)

    def _unwatch_pid(self, pid, pidfile):
        self.pids_pidfiles[pid].discard(pidfile)
        if len(self.pids_pidfiles[pid]) == 0:
            del self.pids_pidfiles[pid]
            self.pids.discard(pid)
            self.mon.stop_watch("/proc/%d" % pid)

    def async_status_update(self):
        """Determine service status asynchronously."""

        return self._async_status_update(self._async_status_update_finished)

    def _async_status_update_finished(self):
        self.notify_herder(serviceherders.SVC_STATUS_CHANGED)

    def _async_status_update(self, callback, *p, **k):
        p = (callback, ) + p
        self._status_asynccmdqueue.queue("env LC_ALL=C /sbin/service "
                                          "\"%s\" status" % self.name,
                                         combined_stdout=True,
                                         ready_cb=self._status_update_ready,
                                         ready_args=p, ready_kwargs=k)
        self.status_updates_running += 1
        self.status = SVC_STATUS_REFRESHING

    def _status_update_ready(self, cmd, callback, *p, **k):
        self.status_updates_running -= 1
        if self.status_updates_running <= 0:
            self.status_updates_running = 0
            self.status = SVC_STATUS_UNKNOWN
        self._status_update_process(cmd)
        callback(*p, **k)

    def _status_update_process(self, cmd):
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

        # print "%s: %s: %d" % (cmd, self.name, self.status)

        self.status_output = cmd.output

    def get_enabled(self):
        """Determines the enablement state of a service."""

        if self.conf_updates_running > 0:
            return SVC_ENABLED_REFRESHING
        if len(self.runlevels) == 0:
            return SVC_ENABLED_NO

        # if len (self.info.startrunlevels) > 0 \
        #        and self.runlevels == self.info.startrunlevels \
        #        or self.runlevels == self._fallback_default_runlevels:

        if self.runlevels == self._fallback_default_runlevels:
            return SVC_ENABLED_YES
        else:
            return SVC_ENABLED_CUSTOM

    def _change_status(self, change):
        if change in ("start", "stop", "restart"):
            self.status = SVC_STATUS_REFRESHING

        # no callback, we let the herder handle that

        self._asynccmdqueue.queue("env LC_ALL=C /sbin/service \"%s\" \"%s\"" %
                                   (self.name, change))

    def start(self):
        """Start this service."""

        self._change_status("start")

    def stop(self):
        """Stop this service."""

        self._change_status("stop")

    def restart(self):
        """Restart this service."""

        self._change_status("restart")

    def reload(self):
        """Reload this service."""

        self._change_status("reload")


class XinetdService(ChkconfigService):

    """Represents a service handled by xinetd."""

    chkconfig_type = "xinetd"

    xinetd_list_re = re.compile(r"^(?P<name>\S+)\s+(?P<enabled>off|on)\s*$")

    def __init__(self, name, mon, herder):
        super(XinetdService, self).__init__(name, mon, herder)

        try:
            self.info = XinetdServiceInfo(name)
        except InvalidServiceInfoException:
            raise InvalidServiceException

        # property: self.enabled = None

        self.load()

    def _async_load(self, callback, *p, **k):
        """Load configuration from disk asynchronously."""

        p = (callback, ) + p

        self._asynccmdqueue.queue("%s --list %s" % 
                                   (self.chkconfig_invocation, self.name),
                                  combined_stdout=True,
                                  ready_cb=self._async_load_ready,
                                  ready_args=p, ready_kwargs=k)
        self.conf_updates_running += 1

    def _async_load_process(self, cmd):
        """Process asynchronously loaded configuration."""

        exitcode = cmd.exitcode
        output = cmd.output

        if exitcode != 0:
            if self.no_chkconfig_re.match(output)\
                 or self.chkconfig_error_re.match(output):
                raise InvalidServiceException(output)
            elif self.chkconfig_unconfigured_re.match(output):
                self.configured = False
                return
            else:

                # service might have been deleted, let the herder take care of it

                return

        m = self.xinetd_list_re.match(output)
        if not m or m.group("name") != self.name:
            print >> sys.stderr, "%s: unable to parse chkconfig output:\n" \
                                  "%s" % (self, output)
            self.enabled = None
        else:
            self.enabled = m.group("enabled") == "on"

    def _get_enabled(self):
        if not hasattr(self, "_enabled"):
            self._enabled = None
        return self._enabled

    def _set_enabled(self, enabled):
        old_enabled = getattr(self, "_enabled", None)
        self._enabled = enabled
        if old_enabled != enabled:
            (status, output) = getstatusoutput("%s %s %s 2>&1" %
                                                (self.chkconfig_invocation,
                                                 self.name, self.enabled and \
                                                  "on" or "off"))
            if status != 0:
                raise OSError("Saving service '%(name)s' failed, command was "
                               "'%(invocation)s %(name)s %(action)s 2>&1'." % \
                                    {"name": self.name,
                                     "invocation": self.chkconfig_invocation,
                                     "action": self.enabled and "on" or "off"})

    enabled = property(_get_enabled, _set_enabled)

    def get_enabled(self):
        if self.conf_updates_running > 0:
            return SVC_ENABLED_REFRESHING
        elif self.enabled == None:
            return SVC_ENABLED_ERROR
        return self.enabled and SVC_ENABLED_YES or SVC_ENABLED_NO


service_classes = [SysVService, XinetdService]
