#!/usr/bin/python

# nonblockingreader.py -- read from file objects without blocking UIs
#
# Copyright (C) 2004 Red Hat, Inc.
# Copyright (C) 2004 Nils Philippsen <nphilipp@redhat.com>
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

import time
import select

class Reader:
    def run (self, fileobjs, callback=None, serviceinterval=0.1, readmax=128):
        outputs = {}
        for fileobj in fileobjs:
            outputs[fileobj] = ""
        while len (fileobjs):
            if callback:
                callback ()
            available = select.select (fileobjs, [], [], serviceinterval)
            for fileobj in available[0]:
                text = fileobj.read (readmax)
                if len (text) != 0:
                    outputs[fileobj] += text
                else:
                    #EOF
                    fileobjs.remove (fileobj)

        return outputs

if __name__ == "__main__":
    import sys
    import string
    import os

    if len (sys.argv) <= 1:
        print "Usage: nonblockingreader.py command [options...]"
        sys.exit (1)
    cmd = string.join (sys.argv[1:])
    def callback ():
        print "callback called"
    stdin, stdout, stderr = os.popen3 (cmd)
    stdin.close ()
    print Reader ().run ([stdout, stderr], callback, 0.1)
    stdout.close ()
    stderr.close ()
