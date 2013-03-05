#!/usr/bin/python
# -*- coding: utf-8 -*-

# gui.py
# Copyright © 2013 Red Hat, Inc.
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
# Authors: Nils Philippsen <nils@redhat.com>

import sys

import locale
locale.setlocale(locale.LC_ALL, '')

import gettext
_ = lambda x: gettext.ldgettext("system-config-services", x)

if __name__ == "__main__":
    if "--no-dbus" in sys.argv[1:]:
        use_dbus = False
    elif "--dbus" in sys.argv[1:]:
        use_dbus = True
    else:
        use_dbus = None

    try:
        __import__("gtk")
    except RuntimeError, e:
        raise SystemExit(_("Error while initializing GUI toolkit: %(error)s\n"
            "This program must be run in a graphical environment.") %
            dict(error=str(e)))
        sys.exit(1)

    from scservices.gui import UIController

    UIController(use_dbus=use_dbus).run()
