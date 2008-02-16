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

from util import getstatusoutput
from asynccmd import *

SVC_STATUS_UNKNOWN = 0
SVC_STATUS_STOPPED = 1
SVC_STATUS_RUNNING = 2
SVC_STATUS_DEAD = 3

##############################################################################

class InvalidServiceException (Exception):
    pass

##############################################################################

class Service (object):
    """Represents an abstract service."""
    def __init__ (self, name, mon):
        super (Service, self).__init__ ()
        self.name = name
        self.mon = mon

    def __repr__ (self):
        return '<%s object at %s: "%s">' % (str (self.__class__), hex (id (self)), self.name)

##############################################################################

class ChkconfigService (Service):
    """Represents an abstract service handled with chkconfig."""

    def __init__ (self, name, mon):
        super (ChkconfigService, self).__init__ (name, mon)
        self.settled = False
        self._asynccmdqueue = AsyncCmdQueue ()
        self.conf_updates_running = 0

    def async_load (self, callback, *p, **k):
        """Load configuration from disk asynchronously."""
        raise NotImplementedError

    def save (self):
        """Save configuration to disk."""
        raise NotImplementedError

    def is_dirty (self):
        """Check if a service is dirty, i.e. changed and not saved."""
        raise NotImplementedError

##############################################################################

class SysVService (ChkconfigService):
    """Represents a service handled by SysVinit."""

    init_list_re = re.compile (r'^(?P<name>\S+)\s+0:(?P<r0>off|on)\s+1:(?P<r1>off|on)\s+2:(?P<r2>off|on)\s+3:(?P<r3>off|on)\s+4:(?P<r4>off|on)\s+5:(?P<r5>off|on)\s+6:(?P<r6>off|on)\s*$')

    no_chkconfig_re = re.compile (r'^service (?P<name>.*) does not support chkconfig$')
    chkconfig_error_re = re.compile (r'^error reading information on service (?P<name>.*):.*$')
    chkconfig_unconfigured_re = re.compile (r"^service (?P<name>.*) supports chkconfig, but is not referenced in any runlevel \(run 'chkconfig --add (?P=name)'\)$")

    def __init__ (self, name, mon):
        super (SysVService, self).__init__ (name, mon)

        self.runlevels = [False, False, False, False, False, False, False]
        self.runlevels_ondisk = [False, False, False, False, False, False, False]
        self.configured = False

        self.status_updates_running = 0
        self.status = SVC_STATUS_UNKNOWN
        self.status_output = None

        #self.async_load (None)

    def async_load (self, callback, *p, **k):
        """Load configuration from disk asynchronously."""
        p = (callback, ) + p
        self._asynccmdqueue.queue ('env LC_ALL=C /sbin/chkconfig --list "%s"' % self.name, combined_stdout = True, ready_cb = self._load_ready, ready_args = p, ready_kwargs = k)
        self.conf_updates_running += 1

    def _load_ready (self, cmd, callback, *p, **k):
        self._load_process (cmd)
        self.conf_updates_running -= 1
        callback (*p, **k)

    def _load_process (self, cmd):
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
        for runlevel in xrange (1, 6):
            self.runlevels[runlevel] = (m.group ("r%d" % runlevel) == 'on') and True or False
        self.runlevels_ondisk = copy.copy (self.runlevels)
        self.configured = True
        self.conf_updates_running -= 1

    def save (self):
        """Save configuration to disk."""
        runlevel_changes = { 'on': [], 'off': [] }

        for i in xrange (len (self.runlevels)):
            if self.runlevels[i] != self.runlevels_ondisk[i]:
                runlevel_changes[self.runlevels[i] and 'on' or 'off'].append (i)

        for what in ('on', 'off'):
            if not len (runlevel_changes[what]):
                continue
            (status, output) = getstatusoutput ('env LC_ALL=C /sbin/chkconfig --level %s %s %s 2>&1' % (''.join (runlevel_changes[what]), self.name, what))
            if status != 0:
                raise OSError ("Saving service '%s' failed, command was 'LC_ALL=C /sbin/chkconfig --level %s %s %s'.\nOutput was:\n%s" % (self.name, ''.join (runlevel_changes[what]), self.name, what, output))

        self.runlevels_ondisk = copy.copy (self.runlevels)
        self.configured = True

    def async_status_update (self, callback, *p, **k):
        """Determine service status asynchronously."""
        p = (callback, ) + p
        self._asynccmdqueue.queue ('env LC_ALL=C /sbin/service \"%s\" status' % self.name, combined_stdout = True, ready_cb = self._status_update_ready, ready_args = p, ready_kwargs = k)
        self.status_updates_running += 1

    def _status_update_ready (self, cmd, callback, *p, **k):
        self._status_update_process (cmd)
        self.status_updates_running -= 1
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

        self.status_output = cmd.output

    def is_dirty (self):
        return self.runlevels != self.runlevels_ondisk

##############################################################################

class XinetdService (ChkconfigService):
    """Represents a service handled by xinetd."""

    xinetd_list_re = re.compile (r'^(?P<name>\S+)\s+(?P<enabled>off|on)\s*$')

    def __init__ (self, name, mon):
        super (XinetdService, self).__init__ (name, mon)
        self.enabled = False
        self.enabled_ondisk = False

        self.load ()

    def load (self):
        """Load configuration from disk."""

        (status, output) = getstatusoutput ('LC_ALL=C /sbin/chkconfig --list %s 2>/dev/null' % self.name)
        if status != 0:
            raise OSError ("Loading service '%s' failed, command was 'LC_ALL=C /sbin/chkconfig --list %s 2>/dev/null'." % self.name)
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

service_classes = [ SysVService, XinetdService ]
