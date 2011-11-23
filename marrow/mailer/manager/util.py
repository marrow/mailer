# encoding: utf-8

try:
    import queue
except ImportError:
    import Queue as queue


__all__ = ['TransportPool']

log = __import__('logging').getLogger(__name__)



class TransportPool(object):
    __slots__ = ('factory', 'transports')
    
    def __init__(self, factory):
        self.factory = factory
        self.transports = queue.Queue()
    
    def startup(self):
        pass
    
    def shutdown(self):
        try:
            while True:
                transport = self.transports.get(False)
                transport.shutdown()
        
        except queue.Empty:
            pass
    
    class Context(object):
        __slots__ = ('pool', 'transport')
        
        def __init__(self, pool):
            self.pool = pool
            self.transport = None
        
        def __enter__(self):
            # First we attempt to find an available transport.
            pool = self.pool
            transport = None
            
            while not transport:
                try:
                    # By consuming transports this way, we maintain thread safety.
                    # Transports are only accessed by a single thread at a time.
                    transport = pool.transports.get(False)
                    log.debug("Acquired existing transport instance.")
                
                except queue.Empty:
                    # No transport is available, so we initialize another one.
                    log.debug("Unable to acquire existing transport, initalizing new instance.")
                    transport = pool.factory()
                    transport.startup()
            
            self.transport = transport
            return transport
        
        def __exit__(self, type, value, traceback):
            transport = self.transport
            ephemeral = getattr(transport, 'ephemeral', False)
            
            if type is not None:
                log.error("Shutting down transport due to unhandled exception.", exc_info=True)
                transport.shutdown()
                return
            
            if not ephemeral:
                log.debug("Scheduling transport instance for re-use.")
                self.pool.transports.put(transport)
            
            else:
                log.debug("Transport marked as ephemeral, shutting down instance.")
                transport.shutdown()
    
    def __call__(self):
        return self.Context(self)
