# encoding: utf-8


__all__ = ['LoggingTransport']

log = __import__('logging').getLogger(__name__)



class LoggingTransport(object):
    def __init__(self, config):
        self.log = log if 'name' not in config else __import__('logging').getLogger(config.name)
    
    def startup(self):
        self.log.debug("Logging transport starting.")
    
    def deliver(self, message):
        self.log.info(str(message))
    
    def shutdown(self):
        self.log.debug("Logging transport stopping.")
