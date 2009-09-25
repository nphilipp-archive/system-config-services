# -*- coding: utf-8 -*-

# util.py: utility functions
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
# Nils Philippsen <nils@redhat.com>

import os


def getstatusoutput(cmd):
    """Return (status, output) of executing cmd in a shell."""

    pipe = os.popen("{ %s ; } 2>&1" % cmd, "r")
    text = pipe.read()
    status = pipe.close()
    if status is None:
        status = 0

    if text[-1:] == "\n":
        text = text[:-1]

    return (status, text)


