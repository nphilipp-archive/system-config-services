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

from __future__ import with_statement

import os
import copy
import re
import time

from util import getstatusoutput
import async

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

        self._run_lock = async.Lock ()

    def __repr__ (self):
        return '<%s object at %s: "%s">' % (str (self.__class__), hex (id (self)), self.name)

##############################################################################

class ChkconfigService (Service):
    """Represents an abstract service handled with chkconfig."""

    def __init__ (self, name, mon):
        super (ChkconfigService, self).__init__ (name, mon)
        self.settled = False
        self._asyncrunner = async.Runner (['load', 'save'])
        self.conf_updating = False

    def _async_ready_callback (self, runnable, callback, *p, **k):
        self.conf_updating = False
        callback (runnable, *p, **k)

    def async_load (self, callback, *p, **k):
        """Kick off asynchronous loading of configuration from disk."""
        self._asyncrunner.start ('load', self.load,
            ready_fn_meth = self._async_ready_callback,
            ready_args = [callback] + list (p), ready_kwargs = k)
        self.conf_updating = True

    def async_save (self, callback, *p, **k):
        """Kick off asynchronous saving of configuration to disk."""
        raise NotImplementedError

    def load (self):
        """Load configuration from disk."""
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
        self._asyncrunner.add_queues ('status')

        self.runlevels = [False, False, False, False, False, False, False]
        self.runlevels_ondisk = [False, False, False, False, False, False, False]
        self.configured = False

        self._status_lock = async.Lock ()
        self.status_updating = False
        self.status = SVC_STATUS_UNKNOWN
        self.status_output = None

        self.load ()

    def __del__ (self):
        #print "del (%s)" % self
        pass

    def load (self):
        """Load configuration from disk."""
        with self._run_lock:
            return self._load ()

    def _load (self):
        """Load configuration from disk (without locking)."""
        (status, output) = getstatusoutput ('LC_ALL=C /sbin/chkconfig --list %s 2>&1' % self.name)
        if status != 0:
            if self.no_chkconfig_re.match (output) \
                or self.chkconfig_error_re.match (output):
                raise InvalidServiceException (output)
            elif self.chkconfig_unconfigured_re.match (output):
                self.configured = False
                return
            else:
                # service might have been deleted
                return
                #raise OSError ("Loading service '%s' failed, command was 'LC_ALL=C /sbin/chkconfig --list %s'.\nOutput was:\n%s" % (self.name, self.name, output))
        m = self.init_list_re.match (output)
        if not m or m.group ('name') != self.name:
            raise output
        for runlevel in xrange (1, 6):
            self.runlevels[runlevel] = (m.group ("r%d" % runlevel) == 'on') and True or False
        self.runlevels_ondisk = copy.copy (self.runlevels)
        self.configured = True
        #print "%s: %s" % (self.name, self.runlevels)

    def save (self):
        """Save configuration to disk."""
        with self._run_lock:
            return self._save (self)

    def _save (self):
        """Save configuration to disk (without locking)."""
        runlevel_changes = { 'on': [], 'off': [] }

        for i in xrange (len (self.runlevels)):
            if self.runlevels[i] != self.runlevels_ondisk[i]:
                runlevel_changes[self.runlevels[i] and 'on' or 'off'].append (i)

        for what in ('on', 'off'):
            if not len (runlevel_changes[what]):
                continue
            (status, output) = getstatusoutput ('LC_ALL=C /sbin/chkconfig --level %s %s %s 2>&1' % (''.join (runlevel_changes[what]), self.name, what))
            if status != 0:
                raise OSError ("Saving service '%s' failed, command was 'LC_ALL=C /sbin/chkconfig --level %s %s %s'.\nOutput was:\n%s" % (self.name, ''.join (runlevel_changes[what]), self.name, what, output))

        self.runlevels_ondisk = copy.copy (self.runlevels)
        self.configured = True

    def _async_status_ready_callback (self, runnable, callback, *p, **k):
        self.status_updating = False
        callback (runnable, *p, **k)

    def async_status_update (self, callback, *p, **k):
        """Kick off asynchronous determining of the status."""
        self._asyncrunner.start ('status', self.get_status,
            ready_fn_meth = self._async_status_ready_callback,
            ready_args = [callback] + list (p), ready_kwargs = k)
        self.status_updating = True

    def get_status (self):
        """Determine status of service."""
        with self._status_lock:
            return self._get_status ()

    def _get_status (self):
        """Determine status of service (without locking)."""
        try:
            (s, o) = getstatusoutput ("LC_ALL=C /sbin/service \"%s\" status 2>&1" % self.name)
        except:
            self.status = SVC_STATUS_UNKNOWN
            self.status_output = output
            return

        signal = s & 0xFF
        exitcode = (s >> 8) & 0xFF

        if not signal:
            if exitcode == 0:
                self.status = SVC_STATUS_RUNNING
            elif exitcode == 1 or exitcode == 2:
                self.status = SVC_STATUS_DEAD
            elif exitcode == 3:
                self.status = SVC_STATUS_STOPPED
            else:
                self.status = SVC_STATUS_UNKNOWN
        else:
            self.status = SVC_STATUS_UNKNOWN

        self.status_output = o

    def is_dirty (self):
        with self._run_lock:
            return self.is_dirty ()

    def _is_dirty (self):
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
        with self._run_lock:
            return self._load ()

    def _load (self):
        """Load configuration from disk (without locking)."""

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
        with self._run_lock:
            return self._save (self)

    def _save (self):
        """Save configuration to disk (without locking)."""
        (status, output) = getstatusoutput ('LC_ALL=C /sbin/chkconfig %s %s 2>/dev/null' % (self.name, self.enabled and 'on' or 'off'))
        if status != 0:
            raise OSError ("Saving service '%s' failed, command was 'LC_ALL=C /sbin/chkconfig %s %s 2>/dev/null'." % (self.name, self.name, self.enabled and 'on' or 'off'))
        self.enabled_ondisk = self.enabled

    def is_dirty (self):
        with self._run_lock:
            return self._is_dirty ()

    def _is_dirty (self):
        return self.enabled != self.enabled_ondisk

service_classes = [ SysVService, XinetdService ]
