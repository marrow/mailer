# encoding: utf-8

from Queue import Queue, Empty


__all__ = ['TransportPool']

log = __import__('logging').getLogger(__name__)



class TransportPool(object):
    def __init__(self, factory):
        self.factory = factory
        self.transports = Queue()
    
    def startup(self):
        pass
    
    def shutdown(self):
        try:
            while True:
                transport = self.transports.get(False)
                transport.shutdown()
        
        except Empty:
            pass
    
    class Context(object):
        def __init__(self, pool):
            self.pool = pool
            self.transport = None
            self.ephemeral = False
        
        def __enter__(self):
            # First we attempt to find an available transport.
            pool = self.pool
            transport = None
            
            while not transport:
                try:
                    # By consuming transports this way, we maintain thread safety.
                    # Transports are only accessed by a single thread at a time.
                    transport = pool.transports.get(False)
                
                except Empty:
                    # No transport is available, so we initialize another one.
                    transport = pool.factory()
                    transport.startup()
            
            self.transport = transport
            return transport
        
        def __exit__(self, type, value, traceback):
            transport = self.transport
            
            if type is not None:
                transport.shutdown()
                return
            
            if not self.ephemeral:
                self.pool.transports.put(transport)
            
            else:
                transport.shutdown()
    
    def __call__(self):
        return self.Context(self)
