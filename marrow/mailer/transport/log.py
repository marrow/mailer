# encoding: utf-8


__all__ = ['LoggingTransport']

log = __import__('logging').getLogger(__name__)



class LoggingTransport(object):
    def __init__(self, config):
        pass
    
    def startup(self):
        pass
    
    def deliver(self, message):
        pass
    
    def shutdown(self):
        pass
