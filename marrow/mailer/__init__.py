"""marrow.mailer mail delivery framework and MIME message abstraction."""

from email import charset
from functools import partial

from ..package import load, name
from .exc import MailerNotRunning
from .message import Message


__all__ = ['Mailer', 'Delivery', 'Message']

log = __import__('logging').getLogger(__name__)

subset = lambda pre, D: {key[len(pre)+1:]: D[key] for key in D if key.startswith(pre + '.')}


class Mailer:
	"""The primary marrow.mailer interface.
	
	Instantiate and configure marrow.mailer, then use the instance to initiate mail delivery.
	
	Where managers and transports are defined in the configuration you may pass in the class,
	an entrypoint name (simple string), or package-object notation ('foo.bar:baz').
	"""
	
	def __repr__(self):
		return f"Mailer(manager={name(self.Manager)}, transport={name(self.Transport)})"
	
	def __init__(self, config, prefix=None):
		self.manager, self.Manager = None, None
		self.Transport = None
		self.running = False
		self.config = subset(prefix, config) if prefix else config
		self.manager_config = manager_config = config.get('manager', subset('manager', config))
		self.transport_config = transport_config = config.get('transport', subset('transport', config))
		self.message_config = config.get('message', subset('message', config))
		self.Manager = Manager = load(manager_config.get('use', 'immediate'), 'marrow.mailer.manager')
		self.Transport = Transport = load(transport_config['use'], 'marrow.mailer.transport')
		
		if not Manager:
			raise LookupError(f"Unable to determine manager from specification: {manager_config['use']}")
		
		if not Transport:
			raise LookupError(f"Unable to determine transport from specification: {transport_config['use']}")
		
		self.manager = Manager(manager_config, partial(Transport, transport_config))
	
	def start(self):
		if self.running:
			log.warning("Attempt made to start an already running Mailer service.")
			return
		
		log.info("Mail delivery service starting.")
		
		self.manager.startup()
		self.running = True
		
		log.info("Mail delivery service started.")
		
		return self
	
	def stop(self):
		if not self.running:
			log.warning("Attempt made to stop an already stopped Mailer service.")
			return
		
		log.info("Mail delivery service stopping.")
		
		self.manager.shutdown()
		self.running = False
		
		log.info("Mail delivery service stopped.")
		
		return self
	
	def send(self, message):
		if not self.running:
			raise MailerNotRunning("Mail service not running.")
		
		log.info(f"Attempting delivery of message: {message.id}")
		
		try:
			result = self.manager.deliver(message)
		
		except:
			log.error(f"Delivery failed for message: {message.id}")
			raise
		
		if __debug__: log.debug(f"Delivery success for message: {message.id}")
		return result
	
	def new(self, author=None, to=None, subject=None, **kw):
		data = dict(self.message_config)
		data['mailer'] = self
		
		if author:
			kw['author'] = author
		if to:
			kw['to'] = to
		if subject:
			kw['subject'] = subject
		
		data.update(kw)
		
		return Message(**data)


# Import-time side-effect: un-fscking the default use of base-64 encoding for UTF-8 e-mail.
charset.add_charset('utf-8', charset.SHORTEST, charset.QP, 'utf-8')
charset.add_charset('utf8', charset.SHORTEST, charset.QP, 'utf8')
