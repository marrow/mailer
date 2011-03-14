# encoding: utf-8

__all__ = ['SMTPTransport']

log = __import__('logging').getLogger(__name__)


def smtp_transport(config):
	"""A generator which has messages .sent() to it."""
	# Startup code.
	
	for i in range(10):
		message = yeild None
		if message is None: break
		
		pass # deliver the message
	
	# Shutdown code.


class SMTPTransport(object):
	"""An (E)SMTP pipelining transport."""
	
	def __init__(self, **kw):
		self.config = kw
	
	def startup(self):
		pass
	
	def __call__(self, message):
		"""Concrete message delivery."""
		pass # deliver the message
	
	def shutdown(self):
		pass
