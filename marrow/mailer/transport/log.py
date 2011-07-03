# encoding: utf-8


__all__ = ['LoggingTransport']

log = __import__('logging').getLogger(__name__)



class LoggingTransport(object):
    def __init__(self, config):
        self.log = log if 'name' not in config else __import__('logging').getLogger(config.name)
    
    def startup(self):
        self.log.debug("Logging transport starting.")
    
    def deliver(self, message):
        msg = str(message)
        self.log.info("DELIVER %s %s %d %r %r", message.id, message.date.isoformat(),
            len(msg), message.author, message.recipients)
        self.log.critical(str(message))
    
    def shutdown(self):
        self.log.debug("Logging transport stopping.")
