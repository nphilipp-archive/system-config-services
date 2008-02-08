"""The servicemethods module handles all the backend processing for the system-config-services application."""
# serviceactions.py
# Copyright (C) 2002 - 2007 Red Hat, Inc.
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
# Tim Powers <timp@redhat.com>
# Dan Walsh <dwalsh@redhat.com>
# Brent Fox <bfox@redhat.com>
# Nils Philippsen <nphilipp@redhat.com>
# Florian Festi <ffesti@redhat.com>

import re, os
from rhpl.translate import _, N_, cat
import copy

import nonblockingreader

try:
    import gamin, gobject
except ImportError:
    gamin = None

def getstatusoutput(cmd, callback):
    """Return (status, output) of executing cmd in a shell."""
    pipe = os.popen("{ %s ; } 2>&1" % (cmd), 'r')
    output = nonblockingreader.Reader ().run ([pipe], callback)
    text = output[pipe]
    status = pipe.close ()
    if status is None: status = 0

    if text[-1:] == '\n':
        text = text[:-1]
    return status, text

# ============================================================================

UNKNOWN = 0
RUNNING = 1
STOPPED = 2
ERROR = 4

status_text = {
    UNKNOWN : _('Unknown'),
    RUNNING : _('Running'),
    STOPPED : _('Stopped'),
    ERROR : _('Error'), 
    }

class Service:
    """Represents a service with start script in /etc/init.d
    """
    
    def __init__(self, name, runlevels, services):
        self.name = name
        self._runlevels = runlevels
        if runlevels:
            self._runlevels_old = runlevels[:]
        self.services = services
        self.uicallback = services.uicallback

        self.startprio = None
        self.stopprio = None
        self.defaultrunlevels = []
        
        self.hide = False
        self.description = ""
        self.processnames = []
        self.configfiles = []
        self.pidfiles = []
        self.probe = False
        self._read_script_file()
        if not self.defaultrunlevels:
            self.defaultrunlevels = [2, 3, 4, 5]

        self._dirty = False
        self._callbacks = []

        if gamin:
            self.services._file_monitor.watch_file('/var/lock/subsys/' + name, self._lock_status_changed)

    def __getattr__(self, name):
        # sloppy evaluate the status as it takes some time 
        if name in ("status", "status_message"):
            self.status, self.status_message = self.get_status()
            if name == "status":
                return self.status
            else:
                return self.status_message
        else:
            raise AttributeError, name

    def is_xinetd_service(self):
        return False

    def exists(self):
        return self._runlevels is not None

    # ----

    def update(self, runlevels):
        self._runlevels = runlevels
        if runlevels is not None:
            self._runlevels_old = runlevels[:]
        self._callback()

    # ----

    def get_runlevels(self):
        return self._runlevels[:]

    def get_active_runlevels(self):
        result = []
        for nr, on in enumerate(self._runlevels):
            if on:
                result.append(nr)
        return result

    def get_active_runlevels_text(self):
        return ', '.join(map(str, self.get_active_runlevels()))

    # ----

    def get_default_runlevels(self):
        return self.defaultrunlevels[:]

    def get_default_runlevels_text(self):
        return ', '.join(map(str, self.get_default_runlevels()))

    # ----

    def is_default(self):
        """return if service is configured as suggested with defaultsrunlevels
        This is either service is off in all runlevels or on on exatctly
        the defaultrunlevels
        """
        if not self.defaultrunlevels:
            return False
        on = self._runlevels[self.defaultrunlevels[0]]
        for runlevel in xrange(len(self._runlevels)):
            if runlevel not in self.defaultrunlevels:
                if self._runlevels[runlevel]: # non default switched on
                    return False
            elif self._runlevels[runlevel] != on:
                # default runlevel != the others
                return False
        return True

    # ----

    def is_default_on(self):
        """
        Return if service is enabled in the default runlevels
        Assumes .is_default() == True!!!"""
        return self._runlevels[self.defaultrunlevels[0]]

    # ----

    def get_status(self):
        """Execute /sbin/service name status
        return (status of the service, the output of the command)
        """
        status = UNKNOWN
        try:
            message = getstatusoutput("LC_ALL=C /sbin/service " + self.name + " status", self.uicallback)[1]
        except:
            return (UNKNOWN, "")

        if message.find("running")!=-1:
            status = RUNNING
        if message.find("stopped")!=-1:
            status = STOPPED
        return (status, message)

    # ----

    def get_script_file(self):
        return "/etc/init.d/" + self.name
        
    # ====

    def set_dirty(self):
        """Tell that a config file got changed"""
        if self.state != STOPPED:
            self._callback()
            self._dirty = True

    # ----
    
    def is_dirty(self):
        """Are there still changes not realized by the service yet"""
        return self._dirty

    # =====

    def set_in_runlevels(self, on, editing_runlevels=0):
        """changed if service is started in the given runlevels
        runlevels may be an int or sequence of ints
        changes are not written to disk. Use .save_changes()"""
        
        if isinstance(editing_runlevels, int):
            editing_runlevels = [editing_runlevels]
        for runlevel in editing_runlevels:
            self._runlevels[runlevel] = on
        self._callback()
        self.services._service_changed(self)

    # ----
        
    def _set_in_runlevels(self, on, editing_runlevels):
        """calls chkconfig --level editing_runlevel on if on, off if not on"""
        chkconfig_action = ("on", "off")[not on]
        try:
            getstatusoutput("LC_ALL=C /sbin/chkconfig --level %s %s %s" % (editing_runlevels, self.name, chkconfig_action), self.uicallback)
        except IOError:
            pass

    # ----

    def set(self, on):
        """Change is service is started in the default runlevels"""
        for runlevel in self.defaultrunlevels:
            self._runlevels[runlevel] = on
        self._callback()
        self.services._service_changed(self)

    # ----

    def is_changed(self):
        """Are there any changes to runlevel behaviour that
        are not yet written to disk"""
        
        for new, old in zip(self._runlevels, self._runlevels_old):
            if new != old:
                return True
        return False

    # ----

    def save_changes(self):
        """when this method is used it saves the change to disk"""

        changed = False
        runlevel = 0
        for new, old in zip(self._runlevels, self._runlevels_old):
            if new ^ old:
                self._set_in_runlevels(new, runlevel)
                changed = True
            runlevel += 1

        self._runlevels_old = self._runlevels[:]
        self._callback()
        return changed
    
    # ----

    def action(self, action):
        """Execute /sbin/service servicename action.
        return (errorcode, message)"""
        
        status, message = getstatusoutput("/sbin/service %s %s" %
                                          (self.name, action),
                                          self.uicallback)

        if status != 0:
            if action in ('start', 'restart', 'reload',  'condrestart'):
                self.status =  ERROR
                self.message = message
            self._callback()
            return (1, _("%s failed. The error was: %s") %
                    (self.name, message))
        else:
            self.status, self.status_message = self.get_status()
            self._dirty = False
            self._callback()
            return (0,"%s %s" % (self.name, action) +
                    _(" successful"))
    # ----
                
    def _read_script_file(self):
        """Gets the description for the given initscript or xinet.d script"""


        try:
            fd = open(self.get_script_file())
        except IOError:
            return

        tag_names = ["chkconfig", "description", "processname", "config",
                     "pidfile", "probe", "hide",
                     "default"] # xinetd
                    # "description[ln]" still missing

        data = []
        tag = None
        for line in fd:
            if len(line) > 0 and line[0]!="#" and not re.match(r"^\s*$",line):
                break
            line = line[1:].strip()

            if not tag:
                match = re.match(r"^\s*(\w+):", line)
                if match and match.group(1) in tag_names:
                    tag = match.group(1)                    
                    line = line[match.end():]

            if tag:
                if line.endswith("\\"):
                    data.append(line[:-1].strip())
                else:
                    data.append(line.strip())
                    self._process_initscript_tag(tag, " ".join(data))
                    tag = None
                    data = []

    def _process_initscript_tag(self, name, value):
        """used by _read_script_file only"""
        if name == "chkconfig":
            match = re.match(r"\s*(\d+|-)\s*(\d+)\s*(\d+)", value)
            if match:
                if match.group(1) != "-":
                    for char in match.group(1):
                        self.defaultrunlevels.append(int(char))
                self.startprio = int(match.group(2))
                self.stopprio = int(match.group(3))
        elif name == "default":
            if value.find("on") != -1:
                self.defaultrunlevels.append(0)
        elif name == "description":
            self.description = value
        elif name == "processname":
            self.processnames.append(value)
        elif name == "config":
            self.configfiles.append(value)
        elif name == "pidfile":
            self.pidfiles.append(value)
        elif name == "probe":
            self.probe = value.find("true") != -1
        elif name == "hide":
            self.hide = value.find("true") != -1

    def revert (self):
        self._runlevels = copy.copy (self._runlevels_old)

    # ----

    def subscribe(self, callback, userdata=None):
        self._callbacks.append((callback, userdata))

    def unsubscribe(self, callback):
        self._callbacks = filter(lambda x: x[0]!=callback, self.callbacks)

    def _callback(self):
        for callback, userdata in self._callbacks:
            callback(self, userdata)
    
    # ----

    def _lock_status_changed(self, file, change):
        if change in (gamin.GAMCreated, gamin.GAMDeleted):
            self.status, self.status_message = self.get_status()
            self._callback()

# ============================================================================

class XinetdService(Service):

    def __init__(self, name, runlevels, services):
        Service.__init__(self, name, runlevels, services)
        self.defaultrunlevels = [0]

    def is_xinetd_service(self):
        return True

    def get_status(self):
        xinetd = self.services.get('xinetd', None)
        if xinetd:
            return xinetd.get_status()
        else:
            return (UNKNOWN, "")

    def get_script_file(self):
        return "/etc/xinetd.d/" + self.name
        
    # ----

    def _set_in_runlevels(self, on, editing_runlevels=None):
        """calls chkconfig on/off"""
        chkconfig_action = ("on", "off")[not on]
        try:
            getstatusoutput("LC_ALL=C /sbin/chkconfig %s %s" %
                            (self.name, chkconfig_action), self.uicallback)
        except IOError:
            pass

    # ----
    
    def action(self, action):
        """starts, stops, and restarts the service. Returns the error
        if the service failed in any of the actions.
        """
        xinetd = self.services.get('xinetd', None)
    
        if xinetd:
            if xinetd.status != RUNNING: 
                return (1, _("xinetd must be enabled for %s to run") %
                        self.name)
            error, output = xinetd.action('relaod')

            if error != 0:
                return (1,_("xinetd failed to reload for ") +
                        self.name +
                        _(". The error was: ") + output)
            else:
                return (0,_("xinetd reloaded %s successfully"))
        else:
            return (1, _("xinetd must be enabled for %s to run") %
                    self.name)

# ============================================================================

class _Services:
    """Includes methods used to find services, and information about them such
    as the description, whether or not it is configured etc."""
        
    def __init__(self, uicallback = None):
        self.uicallback = uicallback
        self._services = { }
        self._xinetd_services = { }
        self._changed = { }

        self._delayed_update = set()

        self._no_update = False
        
        if gamin:
            self._file_monitor = gamin.WatchMonitor()
            self._file_monitor.watch_directory('/etc/rc.d/rc1.d', self._init_status_changed, 1)
            self._file_monitor.watch_directory('/etc/rc.d/rc2.d', self._init_status_changed, 2)
            self._file_monitor.watch_directory('/etc/rc.d/rc3.d', self._init_status_changed, 3)
            self._file_monitor.watch_directory('/etc/rc.d/rc4.d', self._init_status_changed, 4)
            self._file_monitor.watch_directory('/etc/rc.d/rc5.d', self._init_status_changed, 5)
            self._file_monitor.watch_directory('/etc/xinetd.d', self._xinetd_status_changed)
            gobject.io_add_watch(self._file_monitor.get_fd(), gobject.IO_IN | gobject.IO_PRI, self._process_file_monitor)

    def _process_file_monitor(self, source, condition, data=None):
        while self._file_monitor.event_pending():
            self._file_monitor.handle_events()
        return True

    # ----

    def __getitem__(self, name):
        result = self._services.get(name, None) or self._xinetd_services.get(name, None)

        if result:
            return result

        if not self._no_update:
            self._no_update = True
            self.update(name)
            self._no_update = False
            
        result = self._services.get(name, None) or self._xinetd_services.get(name, None)

        if not result:
            result = Service(name, None, self)
            self._services[name] = result

        return result

    def get(self, key, default=None):
        return self[key] or default

    # ----

    def has_key(self, name):
        return (self._services.has_key(name) or
                self._xinetd_services.has_key(name))

    # ----

    def __iter__(self):
        """Iter over all non xinetd services"""
        keys = self._services.keys()
        keys.sort()
        for key in keys:
            yield self._services[key]

    # ----

    def xinetd_services(self):
        """return iterator over all xinetd services"""
        keys = self._xinetd_services.keys()
        keys.sort()
        for key in keys:
            yield self._xinetd_services[key]

    def get_xinetd_service(self, name):
        if not self._xinetd_services.has_key(name):
            self.update(name)
            if not self._xinetd_services.has_key(name):
                self._xinetd_services[name] = XinetdService(name, None, self)
        return self._xinetd_services[name]

    # ----

    def get_runlevel(self):
        """returns the current runlevel, uses /sbin/runlevel"""
        status, output = getstatusoutput("/sbin/runlevel", self.uicallback)
        # This is the current runlevel
        return int(output[2])

    # ----

    def add_service(self, servicename):
        """calls chkconfig --add servicename"""
        result = getstatusoutput("LC_ALL=C /sbin/chkconfig --add %s" %
                                 (servicename), self.uicallback)
        self.update(servicename)
        return result

    # ----
        
    def delete_service(self, servicename):
        """calls chkconfig --del servicename"""
        result = getstatusoutput("LC_ALL=C /sbin/chkconfig --del %s" %
                                 (servicename), self.uicallback)
        self.update(servicename)
        return result
        
    # ----

    def _service_from_chkconfig(self, line):
        """parse one line of chkconfig --list output
        return (name, runlevels as list of bools)
               or None if not a valid line"""
        line = line.strip()
        if not line: return None

        entries = line.split("\t")
        entries = [entry.strip() for entry in entries]

        if entries[0].endswith(":"):
            name = entries[0][:-1]
        else:
            name = entries[0]
                
        if name == "xinetd based services": return None

        entries = entries[1:]
        runlevels = [entry.split(":")[-1]=="on" for entry in entries]

        return name, runlevels

    # ----

    def get_service_lists (self, servicename=''):
        """read in data about services in the system. 
        if servicename is given only get data for this service
        """

        chkconfig_list = getstatusoutput(
          "LC_ALL=C /sbin/chkconfig --list %s 2>/dev/null" % servicename,
          self.uicallback)[1]

        chkconfig_list = chkconfig_list.splitlines()
        
        for line in chkconfig_list:
            service = self._service_from_chkconfig(line)
            if service is None:
                continue
            name, runlevels = service
            if len(runlevels) == 1:
                if not self._xinetd_services.has_key(name):
                    service = XinetdService(name, runlevels, self)
                    self._xinetd_services[name] = service
            else:
                if not self._services.has_key(name):
                    service = Service(name, runlevels, self)
                    self._services[name] = service

        if servicename and self._xinetd_services:
            #if only one xinetd service loaded load also xinetd
            self.update("xinetd")

    # ----

    def update(self, name, runlevels=None):
        """Read status of service from disk. If service got removed
        remove from ourselfs"""
        if runlevels is None:
            status, output = getstatusoutput("LC_ALL=C /sbin/chkconfig --list " +
                                             name, self.uicallback)
            if status == 0:
                service = self._service_from_chkconfig(output)
                if service is not None:
                    name, runlevels = service
            else:
                # service not found, remove if exists in memory
                self[name].update(None)
                return
                
        if len(runlevels) == 1:
            if not self._xinetd_services.has_key(name):
                service = XinetdService(name, runlevels, self)
                self._xinetd_services[name] = service
            else:
                self._xinetd_services[name].update(runlevels)
        else:
            if not self._services.has_key(name):
                service = Service(name, runlevels, self)
                self._services[name] = service
            else:
                self._services[name].update(runlevels)
    
    # ----

    def is_changed(self):
        """Runlevel behaviour of any service got changed
        but not yet written to disk"""
        return bool(self._changed)

    # ----

    def _service_changed(self, service):
        """Called by a service that got changed"""
        if service.is_changed():
            self._changed[service] = 1
        else:
            self._changed.pop(service, None)
            
    
    def _init_status_changed(self, file, change, level):
        if change in (gamin.GAMCreated, gamin.GAMDeleted):
            # self.update(file[3:])
            self._timed_update(file[3:])

    def _xinetd_status_changed(self, file, change):
        if change in (gamin.GAMCreated, gamin.GAMDeleted):
            # self.update(file)
            self._timed_update(file)

    def _timed_update(self, service_name):
        if service_name not in self._delayed_update:
            self.update(service_name)
            self._delayed_update.add(service_name)
            gobject.timeout_add(100, self._delayed_service_update, service_name)

    def _delayed_service_update(self, service_name):
        self.update(service_name)
        self._delayed_update.discard(service_name)

    # ----

    def save_changes(self):
        """when this method is used it saves the change to disk"""
        for service in self._services.itervalues():
            service.save_changes()

        reload_xinetd = False
        for service in self._xinetd_services.itervalues():
            changed = service.save_changes()
            reload_xinetd = reload_xinetd or changed

        if reload_xinetd:
            getstatusoutput("/sbin/service xinetd reload", self.uicallback)

        self._changed = { }

    def revert (self):
        for service in self._services.itervalues ():
            service.revert ()
        for service in self._xinetd_services.itervalues ():
            service.revert ()

_services = None
def Services(uicallback = None):
    global _services
    if _services is None:
        _services = _Services(uicallback)
    _services.uicallback = _services.uicallback or uicallback
    return  _services

"""
_default_runlevel = None
def default_runlevel():
    if _default_runlevel:
        return _default_runlevel
    regex = re.compile('^\w+:(\d):initdefault:.*')
    for line in open('/etc/inittab', 'r'):
        m = regex.match(line)
        if m:
            _default_runlevel = int(m.groups(1))
            break
    
    return _default_runlevel

def runlevel(callback=None):
    if callback is None and _services:
        callback = _service._callback
    status, text = getstatusoutput('/sbin/runlevel', callback)
    if status or (len(text) != 3):
        return -1
    else:
        return int(text[-1])
"""
