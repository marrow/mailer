import random

from ..exc import TransportFailedException, TransportExhaustedException


__all__ = ['MockTransport']

log = __import__('logging').getLogger(__name__)



class MockTransport:
	"""A no-op dummy transport.
	
	Accepts two configuration directives:
	
	 * success - probability of successful delivery
	 * failure - probability of failure
	 * exhaustion - probability of exhaustion
	
	All are represented as percentages between 0.0 and 1.0, inclusive.
	(Setting failure or exhaustion to 1.0 means every delivery will fail
	badly; do not do this except under controlled, unit testing scenarios!)
	"""
	
	__slots__ = ('ephemeral', 'config')
	
	def __init__(self, config):
		self.config = {'success': 1.0, 'failure': 0.0, 'exhaustion': 0.0, **config}
	
	def startup(self):
		pass
	
	def deliver(self, message):
		"""Concrete message delivery."""
		
		if getattr(message, 'die', False):
			1/0
		
		chance = random.randint(0,100001) / 100000.0
		if chance < self.config['failure']:
			raise TransportFailedException("Mock failure.")
		
		chance = random.randint(0,100001) / 100000.0
		if chance < self.config['exhaustion']:
			raise TransportExhaustedException("Mock exhaustion.")
		
		chance = random.randint(0,100001) / 100000.0
		if chance <= self.config['success']:
			return True
		
		return False
	
	def shutdown(self):
		pass
