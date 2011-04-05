# encoding: utf-8


__all__ = ['AmazonTransport']

log = __import__('logging').getLogger(__name__)



class AmazonTransport(object):
    def __init__(self, config):
        pass
    
    def startup(self):
        pass
    
    def deliver(self, message):
        pass # Deliver the message.
    
    def shutdown(self):
        pass
