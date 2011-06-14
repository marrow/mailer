# encoding: utf-8

# TODO: Port: https://github.com/pankratiev/python-amazon-ses-api/blob/master/amazon_ses.py


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
