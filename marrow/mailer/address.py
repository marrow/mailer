"""Marrow Mailer utility functions and support classes."""

from email.utils import formataddr, parseaddr
from email.header import Header

from .validator import EmailValidator


__all__ = ['Address', 'AddressList']


def unicode(value, encoding='utf-8', fallback='iso-8859-1'):
	if isinstance(value, str): return value
	
	try:
		return value.decode(encoding)
	except UnicodeError:
		return value.decode(fallback)


class Address:
	"""Validated electronic mail address class.
	
	This class knows how to validate and format e-mail addresses.  It uses
	Python's built-in `parseaddr` and `formataddr` helper functions and helps
	guarantee a uniform base for all e-mail address operations.
	
	The AddressList unit tests provide comprehensive testing of this class as
	well."""
	
	def __init__(self, name_or_email, email=None, encoding='utf-8'):
		self.encoding = encoding
		
		if email is None:
			if isinstance(name_or_email, AddressList):
				if not 0 < len(name_or_email) < 2:
					raise ValueError("AddressList to convert must only contain a single Address.")
				
				name_or_email = str(name_or_email[0])
			
			if isinstance(name_or_email, (tuple, list)):
				self.name = str(name_or_email[0], encoding)
				self.address = str(name_or_email[1], encoding)
			
			elif isinstance(name_or_email, bytes):
				self.name, self.address = parseaddr(str(name_or_email, encoding))
			
			elif isinstance(name_or_email, str):
				self.name, self.address = parseaddr(name_or_email)
			
			else:
				raise TypeError(f'Expected string, tuple or list, got {type(name_or_email)} instead')
		
		else:
			self.name = str(name_or_email, encoding)
			self.address = str(email, encoding)
		
		email, err = EmailValidator().validate_email(self.address)
		
		if err:
			raise ValueError(f'"{email}" is not a valid e-mail address: {err}')
	
	def __eq__(self, other):
		if isinstance(other, Address):
			return (self.name, self.address) == (other.name, other.address)
		
		elif isinstance(other, str):
			return str(self) == other
		
		elif isinstance(other, bytes):
			return bytes(self) == other
		
		elif isinstance(other, tuple):
			return (self.name, self.address) == other
		
		raise NotImplementedError(f"Can not compare an Address instance against a: {type(other)}")
	
	def __ne__(self, other):
		return not self == other
	
	def __len__(self):
		return len(str(self))
	
	def __repr__(self):
		return f"Address(\"{str(self).encode('ascii', 'backslashreplace').decode('ascii')}\")'"
	
	def __str__(self):
		return self.encode('utf8').decode('utf8')
	
	def __bytes__(self):
		return self.encode()
	
	def encode(self, encoding=None):
		name_string = None
		
		if encoding is None:
			encoding = self.encoding
		
		if encoding != 'ascii':
			try:  # This nonsense is to preserve Python 2 behaviour. Python 3 utf-8 encodes when asked for ascii!
				self.name.encode('ascii', errors='strict')
			except UnicodeError:
				pass
			else:
				name_string = self.name
		
		if name_string is None:
			name_string = Header(self.name, encoding).encode()
		
		# Encode punycode for internationalized domains.
		localpart, domain = self.address.split('@', 1)
		domain = domain.encode('idna').decode()
		address = '@'.join((localpart, domain))
		
		return formataddr((name_string, address)).replace('\n', '').encode(encoding)
	
	@property
	def valid(self):
		email, err = EmailValidator().validate_email(self.address)
		return False if err else True


class AddressList(list):
	def __init__(self, addresses=None, encoding="utf-8"):
		super().__init__()
		
		self.encoding = encoding
		
		if addresses is None:
			return
		
		if isinstance(addresses, str):
			addresses = addresses.split(',')
		
		elif isinstance(addresses, tuple):
			self.append(Address(addresses, encoding=encoding))
			return
		
		if not isinstance(addresses, list):
			raise ValueError(f"Invalid value for AddressList: {adddresses!r}")
		
		self.extend(addresses)
	
	def __repr__(self):
		if not self: return "AddressList()"
		return f"AddressList(\"{', '.join(str(i) for i in self)}\")"
	
	def __bytes__(self):
		return self.encode()
	
	def __str__(self):
		return ", ".join(str(i) for i in self)
	
	def __setitem__(self, k, value):
		if isinstance(k, slice):
			value = [Address(val) if not isinstance(val, Address) else val for val in value]
		
		elif not isinstance(value, Address):
			value = Address(value)
		
		super().__setitem__(k, value)
	
	def __setslice__(self, i, j, sequence):
		self.__setitem__(slice(i, j), sequence)
	
	def encode(self, encoding=None):
		encoding = encoding if encoding else self.encoding
		return b", ".join([a.encode(encoding) for a in self])
	
	def extend(self, sequence):
		values = [Address(val) if not isinstance(val, Address) else val for val in sequence]
		super().extend(values)
	
	def append(self, value):
		self.extend([value])
	
	@property
	def addresses(self):
		return AddressList([i.address for i in self])
	
	@property
	def string_addresses(self, encoding=None):
		"""Return a list of string representations of the addresses suitable
		for usage in an SMTP transaction."""
		
		if not encoding:
			encoding = self.encoding
		
		# We need the punycode goodness.
		return [Address(i.address).encode(encoding).decode(encoding) for i in self]


class AutoConverter:
	"""Automatically converts an assigned value to the given type."""
	
	def __init__(self, attr, cls, can=True):
		self.cls = cls
		self.can = can
		self.attr = str(attr)
	
	def __get__(self, instance, owner):
		value = getattr(instance, self.attr, None)
		
		if value is None:
			return self.cls() if self.can else None
		
		return value
	
	def __set__(self, instance, value):
		if not isinstance(value, self.cls):
			value = self.cls(value)
		
		setattr(instance, self.attr, value)
	
	def __delete__(self, instance):
		setattr(instance, self.attr, None)
