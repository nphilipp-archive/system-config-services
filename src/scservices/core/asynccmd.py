# -*- coding: utf-8 -*-

# asynccmd.py: asynchronous command execution
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

import subprocess
import gobject

__all__ = ("AsyncCmd", "AsyncCmdQueue", "AsyncCmdQueueHerder")


class AsyncCmd(object):

    def __init__(self, cmd, combined_stdout=False,
        priority=gobject.PRIORITY_DEFAULT_IDLE,
        ready_cb=None, ready_args=(), ready_kwargs={}):

        self.cmd = cmd
        self.combined_stdout = combined_stdout
        self.priority = priority
        self.ready_cb = ready_cb
        self.ready_args = ready_args
        self.ready_kwargs = ready_kwargs

        self.pipe = None
        self.fileobjs = None
        self.exitcode = None
        self.output = ""

        if self.combined_stdout:
            self.stderr_output = None
        else:
            self.stderr_output = ""

    def __repr__(self):
        return "<%s.%s object at %s: cmd: %s exitcode: %s fileobjs: %s " \
               "output: %s>" % \
                       (self.__class__.__module__, self.__class__.__name__,
                        hex(id(self)), self.cmd, self.exitcode,
                        self.fileobjs, self.output)

    def run(self):

        # print "%s.run ()" % self

        if self.combined_stdout:
            stderr_arg = subprocess.STDOUT
        else:
            stderr_arg = subprocess.PIPE

        if isinstance(self.cmd, (str, unicode)):
            shell = True
        elif isinstance(self.cmd, (list, tuple)):
            shell = False
        else:
            raise TypeError("cmd: %s" % self.cmd)

        self.pipe = subprocess.Popen(args=self.cmd, stdout=subprocess.PIPE,
                                     stderr=stderr_arg, close_fds=True,
                                     shell=shell)

        self.fileobjs = [self.pipe.stdout]
        if not self.combined_stdout:
            self.fileobjs.append(self.pipe.stderr)

        # print "fileobjs:", self.fileobjs

        for fd in self.fileobjs:
            gobject.io_add_watch(fd, gobject.IO_IN | gobject.IO_PRI |
                                  gobject.IO_HUP,
                                 self.on_fd, priority=self.priority)

    def on_fd(self, fd, condition):
        if condition & (gobject.IO_IN | gobject.IO_PRI):

            # print "%s.read_fd (%s, %s)" % (self, fd, condition)
            # print "reading incoming...",

            incoming = fd.read()

            # print "done"
            # print "incoming: '%s'" % incoming

            if fd == self.pipe.stdout:
                self.output += incoming
            elif fd == self.pipe.stderr:
                self.stderr_output += incoming
            else:
                raise AssertionError

        if condition & gobject.IO_HUP:

            # print "%s.on_hup_fd (%s, %s)" % (self, fd, condition)

            self.fileobjs.remove(fd)
            if len(self.fileobjs) == 0:
                self._finish()
            return False

        return True

    def _finish(self):

        # print "%s._finish ()" % self

        self.pipe.wait()
        self.exitcode = self.pipe.returncode
        self.pipe = None
        if self.ready_cb:

            # print "%s (%s, %s, %s)" % (self.ready_cb, self, self.ready_args, self.ready_kwargs)

            self.ready_cb(self, *self.ready_args, **self.ready_kwargs)


class AsyncCmdQueue(object):

    def __init__(self, max_cmds_running=3, herder=None,
        default_priority=gobject.PRIORITY_DEFAULT_IDLE):

        self.max_cmds_running = max_cmds_running
        self.default_priority = default_priority

        if not herder:
            global defaultAsyncCmdQueueHerder
            if not defaultAsyncCmdQueueHerder:
                defaultAsyncCmdQueueHerder = AsyncCmdQueueHerder()
            herder = defaultAsyncCmdQueueHerder

        self.herder = herder
        self.herder.queues.add(self)

        self.cmds_running = set()
        self.cmds_waiting = []

    def __del__(self):
        self.herder.queues.remove(self)

    def __repr__(self):
        return "<%s.%s object at %s: max: %d run: %d wait: %d>" % \
            (self.__class__.__module__, self.__class__.__name__,
            hex(id(self)), self.max_cmds_running, len(self.cmds_running),
            len(self.cmds_waiting))

    def queue(self, async_cmd, combined_stdout=False, priority=None,
        ready_cb=None, ready_args=(), ready_kwargs={}):

        if not priority:
            priority = self.default_priority
        ready_args = (ready_cb, ) + ready_args
        if isinstance(async_cmd, (str, unicode)):
            cmd_obj = AsyncCmd(async_cmd, combined_stdout=combined_stdout,
                priority=priority, ready_cb=self._ready_cb,
                ready_args=ready_args, ready_kwargs=ready_kwargs)
        elif isinstance(async_cmd, AsyncCmd):
            cmd_obj = async_cmd
        else:
            raise TypeError("async_cmd: %s" % async_cmd)

        self.cmds_waiting.append(cmd_obj)
        self.herder.try_run()

    def _ready_cb(self, cmd, ready_cb, *p, **k):

        # print "%s.ready_cb (%s, %s, %s, %s)" % (self, cmd, ready_cb, p, k)

        if ready_cb:
            ready_cb(cmd, *p, **k)
        self.cmds_running.remove(cmd)
        self.herder.cmd_ready(cmd)
        self.herder.try_run()

    def _can_run(self):
        return len(self.cmds_running) <= self.max_cmds_running

    def waiting(self):
        return len(self.cmds_waiting) > 0

    def run_one(self):

        # print "%s.run_one ()" % self

        if self._can_run() and self.waiting():
            cmd = self.cmds_waiting.pop(0)
            self.cmds_running.add(cmd)

            # print "cmd:", cmd

            cmd.run()
            return cmd
        else:
            return None


class AsyncCmdQueueHerder(object):

    def __init__(self, max_cmds_running=10):
        self.max_cmds_running = max_cmds_running
        self.cmds_running = set()
        self.queues = set()

    def __repr__(self):
        return "<%s.%s object at %s: max: %d run: %d queues: %d>" % \
            (self.__class__.__module__, self.__class__.__name__,
            hex(id(self)), self.max_cmds_running, len(self.cmds_running),
            len(self.queues))

    def try_run(self):

        # print "%s.try_run ()" % self

        waiting = True
        while waiting and len(self.cmds_running) <= self.max_cmds_running:
            waiting = False
            for q in self.queues:
                if q.waiting():
                    waiting = True

                # print "q:", q

                while q.waiting():
                    cmd = q.run_one()

                    # print "cmd:", cmd

                    if cmd:
                        self.cmds_running.add(cmd)
                    else:
                        break

    def cmd_ready(self, cmd):

        # print "%s.cmd_ready (%s)" % (self, cmd)

        self.cmds_running.remove(cmd)


defaultAsyncCmdQueueHerder = None

# Test #

if __name__ == "__main__":
    mainloop = gobject.MainLoop()

    import sys
    sys.setrecursionlimit(19)

    cmds_running = 0


    def ready_cb(cmd, *p, **k):
        global mainloop, cmds_running
        print "cmd finished:"
        print "    cmd:", cmd.cmd
        print "    output:", cmd.output
        cmds_running -= 1
        if cmds_running < 1:
            mainloop.quit()


    for i in xrange(200):
        queue = AsyncCmdQueue()

        queue.queue("sleep 5; echo \"hello (%d)\"" % i, ready_cb=ready_cb,
                    combined_stdout=True)
        queue.queue("sleep 3; echo \"good day (%d)\"" % i, ready_cb=ready_cb,
                    combined_stdout=True)
        cmds_running += 2

    mainloop.run()
