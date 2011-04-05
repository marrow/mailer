# encoding: utf-8


__all__ = ['SMSTransporrt']

log = __import__('logging').getLogger(__name__)



class SMSTransport(object):
    def __init__(self, config):
        pass
    
    def startup(self):
        pass
    
    def deliver(self, message):
        pass
    
    def shutdown(self):
        pass
