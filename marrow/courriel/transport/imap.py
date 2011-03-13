# encoding: utf-8

__all__ = ['IMAPTransport']

log = __import__('logging').getLogger(__name__)


class IMAPTransport(object):
	def __init__(self, **kw):
		self.config = kw
	
	def startup(self):
		pass
	
	def __call__(self, message):
		pass # Deliver the message.
	
	def shutdown(self):
		pass
