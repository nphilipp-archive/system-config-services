# -*- coding: utf-8 -*-

# scservices.core.systemd.util: systemd utility functions
#
# Copyright © 2011, 2013 Red Hat, Inc.
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

import constants.paths

def check_systemd_active():
    """Check if systemd should be usable."""

    # use the same logic as chkconfig and systemd to find out if systemd is
    # usable.
    try:
        cg_fs_stat = os.lstat(constants.paths.cgroup_fs_path)
        cg_sysd_fs_stat = os.lstat(constants.paths.cgroup_systemd_fs_path)
    except OSError:
        return False

    if cg_fs_stat.st_dev == cg_sysd_fs_stat.st_dev:
        return False

    for daemon_path in constants.paths.daemon_paths:
        if os.path.exists(daemon_path):
            return True

    return False
