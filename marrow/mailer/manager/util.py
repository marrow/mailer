from logging import getLogger
import queue

__all__ = ['Booleans', 'Boolean', 'TransportPool']


Booleans = {
		't': True,
		'f': False,
		'y': True,
		'n': False
	}

Boolean = lambda v: bool(Booleans.get(v[0].lower() if hasattr(v, lower) else v, v))


class TransportPool:
	__slots__ = ('factory', 'transports', '_log')
	
	def __init__(self, factory):
		self.factory = factory
		self.transports = queue.Queue()
		self._log = getLogger(__name__)
	
	def startup(self):
		pass
	
	def shutdown(self):
		try:
			while True:
				transport = self.transports.get(False)
				transport.shutdown()
		
		except queue.Empty:
			pass
	
	class Context:
		__slots__ = ('pool', 'transport')
		
		def __init__(self, pool):
			self.pool = pool
			self.transport = None
		
		def __enter__(self):
			# First we attempt to find an available transport.
			pool = self.pool
			transport = None
			
			while not transport:
				try:
					# By consuming transports this way, we maintain thread safety.
					# Transports are only accessed by a single thread at a time.
					transport = pool.transports.get(False)
					if __debug__: self._log.debug("Acquired existing transport instance.")
				
				except queue.Empty:
					# No transport is available, so we initialize another one.
					if __debug__: self._log.debug("Unable to acquire existing transport, initalizing new instance.")
					transport = pool.factory()
					transport.startup()
			
			self.transport = transport
			return transport
		
		def __exit__(self, type, value, traceback):
			transport = self.transport
			ephemeral = getattr(transport, 'ephemeral', False)
			
			if type is not None:
				self._log.error("Shutting down transport due to unhandled exception.", exc_info=True)
				transport.shutdown()
				return
			
			if not ephemeral:
				if __debug__: self._log.debug("Scheduling transport instance for re-use.")
				self.pool.transports.put(transport)
			
			else:
				if __debug__: self._log.debug("Transport marked as ephemeral, shutting down instance.")
				transport.shutdown()
	
	def __call__(self):
		return self.Context(self)
