# -*- coding: utf-8 -*-
# async.py: run methods asynchronously in threads and execute callbacks on
# completion
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
# Nils Philippsen <nphilipp@redhat.com>

from __future__ import with_statement

import os
import signal
import threading

##############################################################################

class AsyncRunnable (object):
    def __init__ (self, start_fn_meth, start_args = None, start_kwargs = None,
            ready_fn_meth = None, ready_args = None, ready_kwargs = None):
        self.start_fn_meth = start_fn_meth
        self.start_args = start_args
        self.start_kwargs = start_kwargs
        self.ready_fn_meth = ready_fn_meth
        self.ready_args = ready_args
        self.ready_kwargs = ready_kwargs

##############################################################################

class AsyncQueue (object):
    def __init__ (self):
        self._queue = []
        self._queue_lock = threading.Lock ()

        self._thread = None
        self._thread_pid = None
        self._thread_lock = threading.Lock ()

        self._run_lock = threading.Lock ()

    def __len__ (self):
        with self._queue_lock:
            return len (self._queue)

    def reap (self):
        with self._thread_lock:
            if self._thread_pid:
                os.kill (self._thread_pid, signal.SIGKILL)
            self._thread_pid = None

    def _run (self):
        with self._thread_lock:
            self._thread_pid = os.getpid ()
        while len (self) > 0:
            with self._queue_lock:
                r = self._queue[0]
            with self._run_lock:
                args = (r.start_args != None) and r.start_args or []
                kwargs = (r.start_kwargs != None) and r.start_kwargs or {}
                r.start_fn_meth (*args, **kwargs)
            if r.ready_fn_meth:
                args = (r.ready_args != None) and r.ready_args or []
                kwargs = (r.ready_kwargs != None) and r.ready_kwargs or {}
                r.ready_fn_meth (*args, **kwargs)
            with self._queue_lock:
                self._queue.pop (0)
        with self._thread_lock:
            #self._thread.join ()
            self._thread = None
            self._thread_pid = None
            if len (self) > 0:
                self._thread = threading.Thread (target = self._run)

    def add (self, runnable):
        with self._queue_lock:
            self._queue.append (runnable)
        with self._thread_lock:
            if not self._thread:
                self._thread = threading.Thread (target = self._run)
                self._thread.start ()

##############################################################################

class AsyncRunner (object):
    def __init__ (self, purposes):
        self._queues = {}

        if isinstance (purposes, str) or '__iter__' not in dir (purposes):
            purposes = (purposes, )

        for p in purposes:
            self._queues[p] = AsyncQueue ()

    def __del__ (self):
        for q in self._queues.itervalues ():
            del q

    def reap (self):
        for q in self._queues.itervalues ():
            q.reap ()
    
    def start (self, purpose, start_fn_meth, start_args = None, start_kwargs = None, ready_fn_meth = None, ready_args = None, ready_kwargs = None):
        queue = self._queues[purpose]
        runnable = AsyncRunnable (start_fn_meth, start_args = start_args,
                start_kwargs = start_kwargs, ready_fn_meth = ready_fn_meth,
                ready_args = ready_args, ready_kwargs = ready_kwargs)
        queue.add (runnable)

    def running (self):
        x = 0
        for q in self._queues.itervalues ():
            x += len (q)
        return (x > 0)

##############################################################################

# Test

if __name__ == '__main__':
    import time
    class Foo:
        def long_method (self, num):
            print "long_method(%d): begin" % num
            for i in range (5):
                print "  long_method(%d): %d" % (num, i)
                time.sleep (1)
            print "long_method(%d): end" % num

        def __init__ (self):
            self.async_runner = AsyncRunner (range (5))

        def __del__ (self):
            del self.async_runner 

        def run (self):
            for num in xrange (5):
                self.async_runner.start (num, self.long_method, start_args = [num])
            i = 0
            while self.async_runner.running ():
                print "base:", i
                i += 1
                time.sleep (1)

        def reap (self):
            self.async_runner.reap ()


    f = Foo ()
    try:
        f.run ()
    except KeyboardInterrupt:
        f.reap ()
