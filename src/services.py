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

import nonblockingreader

def getstatusoutput (cmd, callbacks = None):
    """Return (status, output) of executing cmd in a shell."""
    pipe = os.popen("{ %s ; } 2>&1" % (cmd), 'r')
    output = nonblockingreader.Reader ().run ([pipe], callbacks)
    text = output[pipe]
    status = pipe.close ()
    if status is None: status = 0

    if text[-1:] == '\n':
        text = text[:-1]
    return status, text

class InvalidServiceException (Exception):
    pass

class Service (object):
    """Represents an abstract service"""
    def __init__ (self, name, mon):
        super (Service, self).__init__ ()
        self.name = name
        self.mon = mon

class ChkconfigService (Service):
    """Represents an abstract service handled with chkconfig"""

    def __init__ (self, name, mon):
        super (ChkconfigService, self).__init__ (name, mon)
        self.settled = False

    def load (self):
        """Load configuration from disk"""
        raise NotImplementedError

    def save (self):
        """Save configuration to disk"""
        raise NotImplementedError

    def is_dirty (self):
        """Check if a service is dirty, i.e. changed and not saved"""
        raise NotImplementedError

class SysVService (ChkconfigService):
    """Represents a service handled by SysVinit"""

    init_list_re = re.compile (r'^(?P<name>\S+)\s+0:(?P<r0>off|on)\s+1:(?P<r1>off|on)\s+2:(?P<r2>off|on)\s+3:(?P<r3>off|on)\s+4:(?P<r4>off|on)\s+5:(?P<r5>off|on)\s+6:(?P<r6>off|on)\s*$')

    no_chkconfig_re = re.compile (r'^service (?P<name>.*) does not support chkconfig$')
    chkconfig_unconfigured_re = re.compile (r"^service (?P<name>.*) supports chkconfig, but is not referenced in any runlevel \(run 'chkconfig --add (?P=name)'\)$")

    def __init__ (self, name, mon):
        super (SysVService, self).__init__ (name, mon)
        #print "SysVService (%s, %s)" % (name, mon)
        self.runlevels = [False, False, False, False, False, False, False]
        self.runlevels_ondisk = [False, False, False, False, False, False, False]
        self.configured = False
        self.load ()

    def __del__ (self):
        #print "del (%s)" % self
        pass

    def load (self):
        """Load configuration from disk"""
        (status, output) = getstatusoutput ('LC_ALL=C /sbin/chkconfig --list %s 2>&1' % self.name, None)
        if status != 0:
            if self.no_chkconfig_re.match (output):
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
        """Save configuration to disk"""
        runlevel_changes = { 'on': [], 'off': [] }

        for i in xrange (len (self.runlevels)):
            if self.runlevels[i] != self.runlevels_ondisk[i]:
                runlevel_changes[self.runlevels[i] and 'on' or 'off'].append (i)

        for what in ('on', 'off'):
            if not len (runlevel_changes[what]):
                continue
            (status, output) = getstatusoutput ('LC_ALL=C /sbin/chkconfig --level %s %s %s 2>&1' % (''.join (runlevel_changes[what]), self.name, what), None)
            if status != 0:
                raise OSError ("Saving service '%s' failed, command was 'LC_ALL=C /sbin/chkconfig --level %s %s %s'.\nOutput was:\n%s" % (self.name, ''.join (runlevel_changes[what]), self.name, what, output))

        self.runlevels_ondisk = copy.copy (self.runlevels)
        self.configured = True

    def is_dirty (self):
        return self.runlevels != self.runlevels_ondisk

class XinetdService (ChkconfigService):
    """Represents a service handled by xinetd"""

    xinetd_list_re = re.compile (r'^(?P<name>\S+)\s+(?P<enabled>off|on)\s*$')

    def __init__ (self, name, mon):
        super (XinetdService, self).__init__ (name, mon)
        self.enabled = False
        self.enabled_ondisk = False

        self.load ()

    def load (self):
        """Load configuration from disk"""

        (status, output) = getstatusoutput ('LC_ALL=C /sbin/chkconfig --list %s 2>/dev/null' % self.name, None)
        if status != 0:
            raise OSError ("Loading service '%s' failed, command was 'LC_ALL=C /sbin/chkconfig --list %s 2>/dev/null'." % self.name)
        m = self.xinetd_list_re.match (output)
        if not m or m.group ('name') != self.name:
            raise output
        self.enabled = m.group ('enabled') == "on"
        self.enabled_ondisk = self.enabled

    def save (self):
        """Save configuration to disk"""
        (status, output) = getstatusoutput ('LC_ALL=C /sbin/chkconfig %s %s 2>/dev/null' % (self.name, self.enabled and 'on' or 'off'), None)
        if status != 0:
            raise OSError ("Saving service '%s' failed, command was 'LC_ALL=C /sbin/chkconfig %s %s 2>/dev/null'." % (self.name, self.name, self.enabled and 'on' or 'off'))
        self.enabled_ondisk = self.enabled

    def is_dirty (self):
        return self.enabled != self.enabled_ondisk

service_classes = [ SysVService, XinetdService ]

__all__ = service_classes + [ getstatusoutput ]
