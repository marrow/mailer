from concurrent import futures
from functools import partial

from .util import TransportPool
from ..exc import TransportFailedException, TransportExhaustedException, MessageFailedException, DeliveryFailedException


__all__ = ['FuturesManager']

log = __import__('logging').getLogger(__name__)


def worker(pool, message):
	# This may be non-obvious, but there are several conditions which
	# we trap later that require us to retry the entire delivery.
	result = None
	
	while True:
		with pool() as transport:
			try:
				result = transport.deliver(message)
			
			except MessageFailedException as e:
				raise DeliveryFailedException(message, e.args[0] if e.args else "No reason given.")
			
			except TransportFailedException:
				# The transport has suffered an internal error or has otherwise
				# requested to not be recycled. Delivery should be attempted
				# again.
				transport.ephemeral = True
				continue
			
			except TransportExhaustedException:
				# The transport sent the message, but pre-emptively
				# informed us that future attempts will not be successful.
				transport.ephemeral = True
		
		break
	
	return message, result


class FuturesManager:
	__slots__ = ('workers', 'executor', 'transport')
	
	def __init__(self, config, transport):
		self.workers = config.get('workers', 1)
		
		self.executor = None
		self.transport = TransportPool(transport)
		
		super().__init__()
	
	def startup(self):
		log.info("Futures delivery manager starting.")
		
		if __debug__: log.debug("Initializing transport queue.")
		self.transport.startup()
		
		workers = self.workers
		if __debug__: log.debug("Starting thread pool with %d workers." % (workers, ))
		self.executor = futures.ThreadPoolExecutor(workers)
		
		log.info("Futures delivery manager ready.")
	
	def deliver(self, message):
		# Return the Future object so the application can register callbacks.
		# We pass the message so the executor can do what it needs to to make
		# the message thread-local.
		return self.executor.submit(partial(worker, self.transport), message)
	
	def shutdown(self, wait=True):
		log.info("Futures delivery manager stopping.")
		
		if __debug__: log.debug("Stopping thread pool.")
		self.executor.shutdown(wait=wait)
		
		if __debug__: log.debug("Draining transport queue.")
		self.transport.shutdown()
		
		log.info("Futures delivery manager stopped.")
