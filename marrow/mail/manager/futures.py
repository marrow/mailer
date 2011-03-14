# encoding: utf-8

from concurrent import futures
from Queue import Queue, Empty

from marrow.mail.exc import ManagerException, TransportFailedException, TransportExhaustedException


__all__ = ['FuturesManager']

log = __import__('logging').getLogger(__name__)


class FuturesManager(object):
    def __init__(self, config, transport):
        base = dict(workers=10)
        base.update(dict(config))
        self.config = Bunch(base)
        
        self._Transport = transport
        self.transports = Queue()
        self.executor = None
        
        super(FuturesManager, self).__init__()
    
    def startup(self):
        log.info("Futures delivery manager starting.")
        
        self.executor = ThreadPoolExecutor(self.config.workers)
        
        log.info("Futures delivery manager started.")
    
    def deliver(self, message):
        def inner(message):
            success = False
            
            # This may be non-obvious, but there are several conditions which
            # we trap later that require us to retry the entire delivery.
            while True:
                # First we attempt to find an available transport.
                transport = None
                while not transport:
                    try:
                        # By consuming transports this way, we maintain thread safety.
                        # Transports are only accessed by a single thread at a time.
                        transport = self.transports.get(False)
                    
                    except Empty:
                        # No transport is available, so we initialize another one.
                        transport = self._Transport()
                        transport.startup()
                
                try:
                    success = transport.deliver(message)
                
                except TransportFailedException:
                    # The transport likely timed out waiting for work, so we retry.
                    continue
                
                except TransportExhaustedException:
                    # The transport sent the message, but pre-emptively informed us
                    # that future attempts will not be successful.
                    pass
                
                else:
                    # (Re-)Store the transport for use later.
                    self.transports.put(transport)
                
                break
            
            return success
    
    def shutdown(self, wait=True):
        log.info("Futures delivery manager stopping.")
        
        self.executor.shutdown(wait=wait)
        
        try:
            while True:
                transport = self.transports.get(False)
                transport.shutdown()
        
        except Empty:
            pass
        
        log.info("Futures delivery manager stopped.")
