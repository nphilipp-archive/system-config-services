# -*- coding: utf-8 -*-

# servicesinfo.py: information about services
#
# Copyright © 2008 Red Hat, Inc.
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
import re


class __struct__(object):

    pass


__allrunlevels__ = set(xrange(0, 7))


class InvalidServiceInfoException(Exception):

    pass


class ServiceInfo(object):

    dir = None

    attrs = ()

    def __init__(self, name):
        self.name = name

        self.valid = False
        self.filename = os.path.join(self.dir, self.name)

        if not self.load():
            raise InvalidServiceInfoException

    def __str__(self):
        s = "%s (%s):" % (self.__class__.__name__, self.name)

        x = map(lambda x: "\t%s: %s" % (x, getattr(self, x)),
                filter(lambda y: hasattr(self, y), self.attrs))

        return "\n".join([s] + x)

    def load(self):
        try:

            # open in text mode

            fd = open(self.filename, "r")
        except IOError:
            return

        self.parse(fd)
        return self.valid

    def parse(self, fd):
        raise NotImplementedError

    def _superimpose(self, obj):
        for attr in self.attrs:
            try:
                v = getattr(obj, attr)
                setattr(self, attr, v)
            except AttributeError:
                pass


class SysVServiceInfo(ServiceInfo):

    dir = "/etc/init.d"

    TYPE_NONE = 0
    TYPE_CHKCONFIG = 1
    TYPE_LSB = 2

    info_line_re = re.compile(r"^#\s+(?P<key>[^\s:]+):\s*(?P<value>.*\S)\s*$")
    chkconfig_runlevels_re = re.compile(r"^\s*(?P<runlevels>\d+|-)\s+"
                                         "(?P<start>\d+)\s+(?P<stop>\d+)\s*$")
    chkconfig_desc_cont_re = re.compile(r"^#\s*(?P<descline>.*)$")
    lsb_begin_re = re.compile(r"^### BEGIN INIT INFO\s*$")
    lsb_end_re = re.compile(r"^### END INIT INFO\s*$")
    lsb_desc_cont_re = re.compile(r"^#(\t|  )\s*(?P<descline>.*)$")

    attrs = ("configfiles", "description", "hide", "pidfiles", "probe",
             "processnames", "shortdescription", "startprio", "startrunlevels",
             "stopprio", "stoprunlevels")

    def __init__(self, name):
        super(SysVServiceInfo, self).__init__(name)

        self.type = None

    def _parse_lsb(self, fd):
        lsb = __struct__()
        lsb.description = None
        lsb.pidfiles = None
        lsb.startrunlevels = set()
        lsb.stoprunlevels = set()
        lsb.shortdescription = None

        in_description = False

        for line in fd:
            if self.lsb_end_re.match(line):
                if lsb.startrunlevels.intersection(lsb.stoprunlevels):

                    # one or more runlevels in both start and stop

                    return None
                else:
                    if lsb.description:
                        lsb.description = lsb.description.strip()
                    if len(lsb.stoprunlevels) == 0:
                        lsb.stoprunlevels = \
                            __allrunlevels__.difference(lsb.startrunlevels)
                    return lsb

            if in_description:
                m = self.lsb_desc_cont_re.match(line)
                if m:
                    if lsb.description != None:
                        descline = m.group("descline")
                        if len(descline.strip()) == 0:
                            lsb.description += "\n\n" 
                        else:
                            lsb.description += " " + descline.strip()
                    else:
                        raise AssertionError("lsb.description != None")
                    continue
                else:
                    in_description = False
                    lsb.description = lsb.description.strip()

            m = self.info_line_re.match(line)
            if m:
                key = m.group("key")
                value = m.group("value")

                if key == "Description":
                    in_description = True
                    lsb.description = value.strip()
                elif key == "Short-Description":
                    lsb.shortdescription = value.strip()
                elif key == "Default-Start":
                    try:
                        lsb.startrunlevels = set(map(lambda x: int(x),
                                value.split()))
                    except ValueError:
                        return None
                elif key == "Default-Stop":
                    try:
                        lsb.stoprunlevels = set(map(lambda x: int(x),
                                value.split()))
                    except ValueError:
                        return None
                elif key == "X-Fedora-Pidfile":
                    lsb.pidfiles = set(value.split())
                else:

                    # ignore other keywords for now

                    pass

    def parse(self, fd):
        self.valid = False

        self.description = None
        self.processnames = set()
        self.pidfiles = set()
        self.shortdescription = None
        self.startprio = None
        self.startrunlevels = set()
        self.stopprio = None
        self.stoprunlevels = __allrunlevels__.difference(self.startrunlevels)

        seen_chkconfig = False
        seen_lsb = False
        in_description = False

        chkconfig = __struct__()

        chkconfig.configfiles = {}
        chkconfig.description = None
        chkconfig.hide = False
        chkconfig.pidfiles = None
        chkconfig.probe = False
        chkconfig.processnames = set()
        chkconfig.shortdescription = None
        chkconfig.startprio = None
        chkconfig.startrunlevels = None
        chkconfig.stopprio = None
        chkconfig.stoprunlevels = None

        lsb = None

        for line in fd:
            if line[0:1] != "#" and line.strip() != "":
                break
            if not seen_lsb and self.lsb_begin_re.match(line):
                seen_lsb = True
                lsb = self._parse_lsb(fd)
                continue
            elif in_description:
                m = self.chkconfig_desc_cont_re.match(line)
                if m:
                    if chkconfig.description != None:
                        descline = m.group("descline")
                        if descline.endswith("\\"):
                            descline = descline[:-1]
                        else:
                            in_description = False
                        if len(descline.strip()) == 0:
                            chkconfig.description += """

"""
                        else:
                            chkconfig.description += " " + descline.strip()
            else:
                m = self.info_line_re.match(line)
                if m:
                    key = m.group("key")
                    value = m.group("value")

                    if key == "chkconfig":
                        m = self.chkconfig_runlevels_re.match(value)
                        if m:
                            seen_chkconfig = True
                            rl = m.group("runlevels")
                            chkconfig.startrunlevels = set()
                            if rl != "-":
                                for l in rl:
                                    chkconfig.startrunlevels.add(int(l))
                            chkconfig.stoprunlevels = __allrunlevels__.\
                                    difference(chkconfig.startrunlevels)
                            chkconfig.startprio = int(m.group("start"))
                            chkconfig.stopprio = int(m.group("stop"))
                    elif key == "description":
                        if value.endswith("\\"):
                            in_description = True
                            value = value[:-1]
                        chkconfig.description = value.strip()
                    elif key == "pidfile":
                        chkconfig.pidfiles = set(value.split())
                    elif key == "processname":
                        chkconfig.processnames.add(value.strip())
                    elif key == "probe" and value.strip() == "true":
                        chkconfig.probe = True
                    elif key == "configfile":
                        cfinfo = value.split()
                        if len(cfinfo) > 1 and cfinfo[1] == "autoreload":
                            chkconfig.configfiles[cfinfo[0]] = True
                        elif len(cfinfo) == 1:
                            chkconfig.configfiles[cfinfo[0]] = False
                    elif key == "hide" and value.strip() == "true":
                        chkconfig.hide = True

        if not seen_chkconfig:
            chkconfig = None

        self._chkconfig = chkconfig
        self._lsb = lsb

        if chkconfig:
            self._superimpose(chkconfig)
        if lsb:
            self._superimpose(lsb)

        if chkconfig or lsb:
            self.valid = True

        return self.valid


class XinetdServiceInfo(ServiceInfo):

    dir = "/etc/xinetd.d"

    info_line_re = \
        re.compile(r"^\s*(?P<key>[^\s:]+)\s*=\s*(?P<value>.*\S)\s*$")
    default_re = re.compile(r"^\s*#\s*default:\s*(?P<default>on|off)\s*$")
    description_re = \
        re.compile(r"^\s*#\s*description:\s*(?P<descline>.*?)(?P<cont>\\)?$")
    description_cont_re = \
        re.compile(r"^\s*#\s*(?P<descline>.*?)(?P<cont>\\)?$")

    attrs = ("default", "description", "enabled")

    def parse(self, fd):
        self.valid = False

        self.default = False
        self.description = None
        self.enabled = None

        in_description = False

        for line in fd:
            if in_description:
                m = self.description_cont_re.match(line)
                if m:
                    descline = m.group("descline")
                    if m.group("cont") != "\\":
                        in_description = False
                    if len(descline.strip()) == 0:
                        self.description += "\n\n"
                    else:
                        self.description += " " + descline.strip()
                    continue

            if not self.default:
                m = self.default_re.match(line)
                if m:
                    self.default = m.group("default") == "on"
                    continue

            if not self.description:
                m = self.description_re.match(line)
                if m:
                    self.description = m.group("descline").strip()
                    if m.group("cont") == "\\":
                        in_description = True
                    continue

            m = self.info_line_re.match(line)

            if m:
                key = m.group("key")
                value = m.group("value")

                if key == "disable":
                    self.enabled = value == "no"

        if self.enabled == None:
            self.enabled = True

        self.valid = True


# Test #

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        services = sys.argv[1:]
    else:
        services = os.listdir(SysVServiceInfo.dir)
        services.extend(os.listdir(XinetdServiceInfo.dir))
        services.sort()

    for servicename in services:
        try:
            service = SysVServiceInfo(servicename)
            print "\n%s:\n%s""" % (servicename, service)
        except InvalidServiceInfoException:
            try:
                service = XinetdServiceInfo(servicename)
                print "\n%s:%s""" % (servicename, service)
            except InvalidServiceInfoException:
                print "\n%s: invalid" % servicename
