# encoding: utf-8

import atexit
import threading
import weakref
import sys
import math

from functools import partial

from marrow.mailer.manager.futures import worker
from marrow.mailer.manager.util import TransportPool

try:
    import queue
except ImportError:
    import Queue as queue

try:
    from concurrent import futures
except ImportError: # pragma: no cover
    raise ImportError("You must install the futures package to use background delivery.")


__all__ = ['DynamicManager']

log = __import__('logging').getLogger(__name__)



def thread_worker(executor, jobs, timeout, maximum):
    i = maximum + 1
    
    try:
        while i:
            i -= 1
            
            try:
                work = jobs.get(True, timeout)
                
                if work is None:
                    runner = executor()
                    
                    if runner is None or runner._shutdown:
                        log.debug("Worker instructed to shut down.")
                        break
                    
                    # Can't think of a test case for this; best to be safe.
                    del runner # pragma: no cover
                    continue # pragma: no cover
            
            except queue.Empty: # pragma: no cover
                log.debug("Worker death from starvation.")
                break
            
            else:
                work.run()
        
        else: # pragma: no cover
            log.debug("Worker death from exhaustion.")
    
    except: # pragma: no cover
        log.critical("Unhandled exception in worker.", exc_info=True)
    
    runner = executor()
    if runner:
        runner._threads.discard(threading.current_thread())


class WorkItem(object):
    __slots__ = ('future', 'fn', 'args', 'kwargs')
    
    def __init__(self, future, fn, args, kwargs):
        self.future = future
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        if not self.future.set_running_or_notify_cancel():
            return
        
        try:
            result = self.fn(*self.args, **self.kwargs)
        
        except:
            e = sys.exc_info()[1]
            self.future.set_exception(e)
        
        else:
            self.future.set_result(result)


class ScalingPoolExecutor(futures.ThreadPoolExecutor):
    def __init__(self, workers, divisor, timeout):
        self._max_workers = workers
        self.divisor = divisor
        self.timeout = timeout
        
        self._work_queue = queue.Queue()
        
        self._threads = set()
        self._shutdown = False
        self._shutdown_lock = threading.Lock()
        self._management_lock = threading.Lock()
        
        atexit.register(self._atexit)
    
    def shutdown(self, wait=True):
        with self._shutdown_lock:
            self._shutdown = True
            
            for i in range(len(self._threads)):
                self._work_queue.put(None)
        
        if wait:
            for thread in list(self._threads):
                thread.join()
    
    def _atexit(self): # pragma: no cover
        self.shutdown(True)
    
    def _spawn(self):
        t = threading.Thread(target=thread_worker, args=(weakref.ref(self), self._work_queue, self.divisor, self.timeout))
        t.daemon = True
        t.start()
        
        with self._management_lock:
            self._threads.add(t)
    
    def _adjust_thread_count(self):
        pool = len(self._threads)
        
        if pool < self._optimum_workers:
            tospawn = int(self._optimum_workers - pool)
            log.debug("Spawning %d thread%s." % (tospawn, tospawn != 1 and "s" or ""))
            
            for i in range(tospawn):
                self._spawn()
    
    @property
    def _optimum_workers(self):
        return min(self._max_workers, math.ceil(self._work_queue.qsize() / float(self.divisor)))


class DynamicManager(object):
    __slots__ = ('workers', 'divisor', 'timeout', 'executor', 'transport')
    
    name = "Dynamic"
    Executor = ScalingPoolExecutor
    
    def __init__(self, config, transport):
        self.workers = config.get('workers', 10) # Maximum number of threads to create.
        self.divisor = config.get('divisor', 10) # Estimate the number of required threads by dividing the queue size by this.
        self.timeout = config.get('timeout', 60) # Seconds before starvation.
        
        self.executor = None
        self.transport = TransportPool(transport)
        
        super(DynamicManager, self).__init__()
    
    def startup(self):
        log.info("%s manager starting up.", self.name)
        
        log.debug("Initializing transport queue.")
        self.transport.startup()
        
        workers = self.workers
        log.debug("Starting thread pool with %d workers." % (workers, ))
        self.executor = self.Executor(workers, self.divisor, self.timeout)
        
        log.info("%s manager ready.", self.name)
    
    def deliver(self, message):
        # Return the Future object so the application can register callbacks.
        # We pass the message so the executor can do what it needs to to make
        # the message thread-local.
        return self.executor.submit(partial(worker, self.transport), message)
    
    def shutdown(self, wait=True):
        log.info("%s manager stopping.", self.name)
        
        log.debug("Stopping thread pool.")
        self.executor.shutdown(wait=wait)
        
        log.debug("Draining transport queue.")
        self.transport.shutdown()
        
        log.info("%s manager stopped.", self.name)
