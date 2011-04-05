# encoding: utf-8


__all__ = ['AppEngineTransport']

log = __import__('logging').getLogger(__name__)



class AppEngineTransport(object):
    # TODO: Translate between our Message object and http://code.google.com/appengine/docs/python/mail/emailmessagefields.html
    # Deliver using http://code.google.com/appengine/docs/python/mail/sendingmail.html
    
    def __init__(self, config):
        pass
    
    def startup(self):
        pass
    
    def deliver(self, message):
        pass # Deliver the message.
    
    def shutdown(self):
        pass
