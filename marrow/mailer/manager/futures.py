# encoding: utf-8

from concurrent import futures
from Queue import Queue, Empty

from marrow.mailer.exc import (ManagerException, TransportFailedException,
        MessageFailedException, TransportExhaustedException)

from marrow.mailer.manager.util import TransportPool

from marrow.util.bunch import Bunch


__all__ = ['FuturesManager']

log = __import__('logging').getLogger(__name__)



class FuturesManager(object):
    def __init__(self, config, transport):
        base = dict(workers=10)
        base.update(dict(config))
        self.config = Bunch(base)
        
        self.executor = None
        self.transport = TransportPool(transport)
        
        super(FuturesManager, self).__init__()
    
    def startup(self):
        log.info("Futures delivery manager starting.")
        
        log.debug("Initializing transport queue.")
        self.transport.startup()
        
        workers = self.config.workers
        log.debug("Starting thread pool with %d workers." % (workers, ))
        self.executor = futures.ThreadPoolExecutor(workers)
        
        log.info("Futures delivery manager started.")
    
    def deliver(self, message):
        def inner(message):
            success = False
            
            # This may be non-obvious, but there are several conditions which
            # we trap later that require us to retry the entire delivery.
            while True:
                with self.transport() as transport:
                    try:
                        success = transport.deliver(message)
                    
                    except TransportFailedException:
                        # The transport likely timed out waiting for work, so we
                        # toss out the current transport and retry.
                        transport.ephemeral = True
                        continue
                    
                    except TransportExhaustedException:
                        # The transport sent the message, but pre-emptively
                        # informed us that future attempts will not be successful.
                        transport.ephemeral = True
                
                break
            
            return success
        
        # Return the Future object so the application can register callbacks.
        # We pass the message so the executor can do what it needs to to make
        # the message thread-local.
        return self.executor.submit(inner, message)
    
    def shutdown(self, wait=True):
        log.info("Futures delivery manager stopping.")
        
        log.debug("Stopping thread pool.")
        self.executor.shutdown(wait=wait)
        
        log.debug("Draining transport queue.")
        self.transport.shutdown()
        
        log.info("Futures delivery manager stopped.")
