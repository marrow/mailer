# encoding: utf-8

__all__ = ['ImmediateManager']

log = __import__('logging').getLogger(__name__)


class ImmediateManager(object):
    def __init__(self, config, transport):
        self.config = config
        self.transport = transport()
        
        super(ImmediateManager, self).__init__()
    
    def startup(self):
        log.info("Immediate delivery manager starting.")
        
        self.transport.startup()
        
        log.info("Immediate delivery manager started.")
    
    def deliver(self, message):
        self.transport.deliver(message)
    
    def shutdown(self):
        log.info("Immediate delivery manager stopping.")
        
        self.transport.shutdown()
        
        log.info("Immediate delivery manager stopped.")
