# encoding: utf-8

from marrow.mail.exc import TransportExhaustedException


__all__ = ['ImmediateManager']

log = __import__('logging').getLogger(__name__)



class ImmediateManager(object):
    def __init__(self, config, transport):
        self.config = config
        self._Transport = transport
        self._transport = None
        
        super(ImmediateManager, self).__init__()
    
    @property
    def transport(self):
        if not self._transport:
            self._transport = self._Transport()
            self._transport.startup()
        
        return self._transport
    
    def startup(self):
        log.info("Immediate delivery manager starting.")
        
        self.transport # This will trigger startup automatically.
        
        log.info("Immediate delivery manager started.")
    
    def deliver(self, message):
        try:
            result = self.transport.deliver(message)
        
        except TransportExhaustedException:
            log.debug("Transport exhausted, retrying.")
            self.transport.shutdown()
            self.deliver(message)
        
        return result
    
    def shutdown(self):
        log.info("Immediate delivery manager stopping.")
        
        self.transport.shutdown()
        
        log.info("Immediate delivery manager stopped.")
