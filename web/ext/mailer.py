from os import getcwd, getenv, getlogin
from socket import getfqdn
from urllib.parse import unquote

from marrow.mailer import Mailer
from uri.typing import URILike


class MailerExtension:
	"""A WebCore web framework adapter to populate a mailer instance as global context.
	
	Configuration is entirely derived from the URI passed through to this extension's constructor. This facilitates
	control over the transport (URI scheme), credentials and host+port for networked transports, "directory" for disk-
	backed transports, and utilizes the query string to populate the remaining Marrow Mailer configuration directives.
	
	The `manager.use` option defaults to `immediate` when run without optimizations and `dynamic` when run with. Some
	arguments are special-cased for the sake of brevity, saving repeated `message.` key prefixing:
	
	* `author` -- the default author to use when factory constructing new Message instances.
	* `organization` -- the default Organization header to use when factory constructing Messages.
	
	Additional query string arguments are assumed to be transport configuration options. Query string arguments that
	are valueless are treated as boolean flags, `True` if present. For improved security, password credentials may be
	supplied external to the URI itself by way of the `MAIL_PASSWORD` environment variable.
	
	Examples:
	
		maildir://localhost/{here}/var/mail?create&author=Alice+Bevan-McGregor+%3Camcgregor%40cegid.com%3E
	
		smtp://user:pass@smtp.mailgun.org:465?tls=ssl&author=CEGID+Inc.+RITA+%3Crita%40...%3E&organization=CEGID+Inc.
	"""
	
	provides = ('mail', 'email', 'mailer')
	
	def __init__(self, uri:URILike):
		self.__uri = uri = URI(str(uri).format(cwd=getcwd().lstrip('/')))
		
		self.configuration = {  # Mailer already includes mechanisms to resolve and instantiate the plugins.
				'manager.use': uri.query.pop('manager', 'immediate' if __debug__ else 'dynamic'),
				'transport.use': str(uri.scheme),  # smtp://, maildir://, ...
				'transport.directory': str(uri.path) if str(uri.path) != '.' else '',
				'transport.host': uri.host,
				'transport.port': uri.port,
				'transport.username': unquote(uri.username or ''),
				'transport.password': unquote(getenv('MAIL_PASSWORD', uri.password)),
			}
		
		# Potentially sensitive default, emit a warning when used.
		if 'author' in uri.query: self.configuration['message.author': uri.query.pop('author')]
		else:
			__import__('warnings').warn("Utilizing active user's name and hostname as default message author.", UserWarning, 2)
			self.configuration['message.author'] = f"{getlogin()}@{getfqdn()}"
		
		if 'organization' in uri.query: self.configuration['message.organization'] = uri.query.pop('organization')
		
		# Remaining arguments are additional configuration.
		for n for n in uri.query.items(): self.configuration[n[0]] = True if len(n) == 1 else n[1]
		
		# Remove empty configuration directives.
		for k, v in list(self.configuration.items()):
			if v == '': del self.configuration[k]
	
	def start(self, context):
		safe = self.configuration.copy()
		if 'transport.password' in safe:
			safe['transport.password'] = '***'
		
		log.info(f"Preparing mail delivery infrastructure: {self.__uri.safe_uri}", extra=safe)
		
		context.mailer = MailerInterface(self.configuration)
		context.mailer.start()
	
	def stop(self, context):
		context.mailer.stop()

