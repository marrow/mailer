# encoding: utf-8

try:
	import requests

except ImportError:
	raise ImportError("You must install the requests package to deliver mail mailgun.")


__all__ = ['MailgunTransport']

log = __import__('logging').getLogger(__name__)



class MailgunTransport(object): # pragma: no cover
	__slots__ = ('ephemeral', 'keys', 'session')
	
	API_URL_TMPL = "https://api.mailgun.net/v3/{domain}/messages.mime"
	
	def __init__(self, config): 
		if 'domain' in config and 'key' in config:
			self.keys = {config['domain']: config['key']}
		else:
			self.keys = config.get('keys', {})

		if not self.keys:
			raise ValueError("Must either define a `domain` and `key` configuration, or `keys` mapping.")
		
		self.session = None
	
	def startup(self):
		self.session = requests.Session()
	
	def deliver(self, message):
		domain = message.author.address.rpartition('@')[2]
		if domain not in self.keys:
			raise Exception("No API key registered for: " + domain)
		
		uri = self.API_URL_TMPL.format(domain=domain)
		
		result = self.session.post(uri, auth=('api', self.keys[domain]),
			data = {'from': message.author, 'to': list(str(i) for i in message.recipients),
					'subject': message.subject},
			files = {"message": ('message.mime', message.mime.as_bytes())})
		
		result.raise_for_status()
	
	def shutdown(self): 
		if self.session:
			self.session.close()
		
		self.session = None
