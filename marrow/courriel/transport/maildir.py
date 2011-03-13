# encoding: utf-8

__all__ = ['MailDirTransport']

log = __import__('logging').getLogger(__name__)


class MailDirTransport(object):
	def __init__(self, **kw):
		self.config = kw
	
	def startup(self):
		pass
	
	def __call__(self, message):
		pass # Deliver the message.
	
	def shutdown(self):
		pass
