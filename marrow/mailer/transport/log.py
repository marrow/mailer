from logging import getLogger


__all__ = ['LoggingTransport']


class LoggingTransport:
	__slots__ = ('ephemeral', 'log')
	
	def __init__(self, config):
		self.log = getLogger(config.get('name', __name__))
	
	def startup(self):
		if __debug__: self.log.debug("Logging transport starting.")
	
	def deliver(self, message):
		msg = str(message)
		
		self.log.info(
				"DELIVER %s %s %d %r %r",
				message.id,
				message.date.isoformat(),
				len(msg),
				message.author,
				message.recipients
			)
		
		self.log.debug(msg)
	
	def shutdown(self):
		if __debug__: self.log.debug("Logging transport stopping.")
