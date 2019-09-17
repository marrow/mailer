"""MIME-encoded electronic mail message class."""

import imghdr
import os
import sys
import time
import base64

from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.utils import make_msgid, formatdate
from mimetypes import guess_type
from typing import Optional

from . import release
from .address import Address, AddressList, AutoConverter


__all__ = ['Message']


class Message:
	"""Represents an e-mail message."""
	
	_id: Optional[str] = None  # Message-Id
	_processed: bool = False  # Has the MIME generation process been completed?
	_dirty: bool = False  # Has some aspect of the message changed since generation?
	mailer: Optional[object] = None  # The mailer instance the message is "bound" to.
	
	sender = AutoConverter('_sender', Address, False)
	author = AutoConverter('_author', AddressList)
	authors = author
	to = AutoConverter('_to', AddressList)
	cc = AutoConverter('_cc', AddressList)
	bcc = AutoConverter('_bcc', AddressList)
	reply = AutoConverter('_reply', AddressList)
	notify = AutoConverter('_notify', AddressList)
	
	def __init__(self, author=None, to=None, subject=None, **kw):
		"""Instantiate a new Message object.
		
		No arguments are required, as everything can be set using class
		properties.  Alternatively, __everything__ can be set using the
		constructor, using named arguments.  The first three positional
		arguments can be used to quickly prepare a simple message.
		"""
		
		# Default values
		self.subject = None
		self.date = datetime.now()
		self.encoding = 'utf-8'
		self.organization = None
		self.priority = None
		self.plain = None
		self.rich = None
		self.attachments = []
		self.embedded = []
		self.headers = []
		self.retries = 3
		self.brand = True
		
		self._sender = None
		self._author = AddressList()
		self._to = AddressList()
		self._cc = AddressList()
		self._bcc = AddressList()
		self._reply = AddressList()
		self._notify = AddressList()
		
		# Overrides at initialization time
		if author is not None:
			self.author = author
		
		if to is not None:
			self.to = to
		
		if subject is not None:
			self.subject = subject
		
		for k in kw:
			if not hasattr(self, k):
				raise TypeError("Unexpected keyword argument: %s" % k)
			
			setattr(self, k, kw[k])
	
	def __setattr__(self, name, value):
		"""Set the dirty flag as properties are updated."""
		object.__setattr__(self, name, value)
		if name not in ('bcc', '_id', '_dirty', '_processed'):
			object.__setattr__(self, '_dirty', True)
	
	def __str__(self):
		"""Generate the MIME representation of this message to cast to a textual string."""
		return self.mime.as_string()
	
	def __bytes__(self):
		"""Generate the ASCII MIME representation of this message as a binary string."""
		return self.mime.as_string().encode('ascii')
	
	@property
	def id(self):
		"""Access the ID of the message.
		
		If no ID is currently assigned, or if the message has already been "sent", but has modifications, a new ID
		will be generated automatically.
		"""
		
		if not self._id or (self._processed and self._dirty):
			self._id = make_msgid()
			self._processed = False
		
		return self._id
	
	@property
	def envelope(self):
		"""The address of the "envelope sender", explicitly defined or defaulting to the message author."""
		
		if not self.sender and not self.author:
			raise ValueError("Unable to determine message sender; no author or sender defined.")
		
		return self.sender or self.author[0]
	
	@property
	def recipients(self):
		"""The AddressList representing all recipients of this message, regardless of method of address."""
		
		return AddressList(self.to + self.cc + self.bcc)
	
	def _mime_document(self, plain, rich=None):
		"""Generate a MIMEMultipart message if needed."""
		
		if not rich:
			message = plain
		
		else:
			message = MIMEMultipart('alternative')
			message.attach(plain)
			
			if not self.embedded:
				message.attach(rich)
			
			else:
				embedded = MIMEMultipart('related')
				embedded.attach(rich)
				for attachment in self.embedded:
					embedded.attach(attachment)
				message.attach(embedded)
		
		if self.attachments:
			attachments = MIMEMultipart()
			attachments.attach(message)
			for attachment in self.attachments:
				attachments.attach(attachment)
			message = attachments
		
		return message
	
	def _build_date_header_string(self, date_value):
		"""Gets the date_value (may be None, str, float or datetime.datetime instance) and returns a valid date
		string as per RFC 2822."""
		
		if isinstance(date_value, datetime):
			date_value = time.mktime(date_value.timetuple())
		if not isinstance(date_value, str):
			date_value = formatdate(date_value, localtime=True)
		
		# Encode it here to avoid this:
		# Date: =?utf-8?q?Sat=2C_01_Sep_2012_13=3A08=3A29_-0300?=
		
		return str(date_value)
	
	def _build_header_list(self, author, sender):
		date_value = self._build_date_header_string(self.date)
		
		headers = [
				('Sender', sender),
				('From', author),
				('Reply-To', self.reply),
				('Subject', self.subject),
				('Date', date_value),
				('To', self.to),
				('Cc', self.cc),
				('Disposition-Notification-To', self.notify),
				('Organization', self.organization),
				('X-Priority', self.priority),
			]
		
		if self.brand:
			headers.extend([
					('X-Mailer', "marrow.mailer {0}".format(release.version))
				])
		
		if isinstance(self.headers, dict):
			for key in self.headers:
				headers.append((key, self.headers[key]))
		
		else:
			headers.extend(self.headers)
		
		if 'message-id' not in (header[0].lower() for header in headers):
			headers.append(('Message-Id', self.id))
		
		return headers
	
	def _add_headers_to_message(self, message, headers):
		for header in headers:
			if header[1] is None or (isinstance(header[1], list) and not header[1]):
				continue
			
			name, value = header
			
			if isinstance(value, (Address, AddressList)):
				value = str(value)
			
			message[name] = value
	
	@property
	def mime(self):
		"""Produce the final MIME message."""
		
		author = self.author
		sender = self.sender
		
		if not author:
			raise ValueError("You must specify an author.")
		
		if not self.subject:
			raise ValueError("You must specify a subject.")
		
		if len(self.recipients) == 0:
			raise ValueError("You must specify at least one recipient.")
		
		if not self.plain:
			raise ValueError("You must provide plain text content.")
		
		# DISCUSS: Take the first author, or raise this error?
		# if len(author) > 1 and len(sender) == 0:
		#	 raise ValueError('If there are multiple authors of message, you must specify a sender!')
		
		# if len(sender) > 1:
		#	 raise ValueError('You must not specify more than one sender!')
		
		if not self._dirty and self._processed:
			return self._mime
		
		self._processed = False
		
		plain = MIMEText(self._callable(self.plain), 'plain', self.encoding)
		
		rich = None
		if self.rich:
			rich = MIMEText(self._callable(self.rich), 'html', self.encoding)
		
		message = self._mime_document(plain, rich)
		headers = self._build_header_list(author, sender)
		self._add_headers_to_message(message, headers)
		
		self._mime = message
		self._processed = True
		self._dirty = False
		
		return message
	
	def attach(self, name, data=None, maintype=None, subtype=None,
		inline=False, filename=None, filename_charset='', filename_language='',
		encoding=None):
		"""Attach a file to this message.
		
		:param name: Path to the file to attach if data is None, or the name
					 of the file if the ``data`` argument is given
		:param data: Contents of the file to attach, or None if the data is to
					 be read from the file pointed to by the ``name`` argument
		:type data: bytes or a file-like object
		:param maintype: First part of the MIME type of the file -- will be
						 automatically guessed if not given
		:param subtype: Second part of the MIME type of the file -- will be
						automatically guessed if not given
		:param inline: Whether to set the Content-Disposition for the file to
					   "inline" (True) or "attachment" (False)
		:param filename: The file name of the attached file as seen
									by the user in his/her mail client.
		:param filename_charset: Charset used for the filename paramenter. Allows for 
						attachment names with characters from UTF-8 or Latin 1. See RFC 2231.
		:param filename_language: Used to specify what language the filename is in. See RFC 2231.
		:param encoding: Value of the Content-Encoding MIME header (e.g. "gzip"
						 in case of .tar.gz, but usually empty)
		"""
		self._dirty = True
		
		if not maintype:
			maintype, guessed_encoding = guess_type(name)
			encoding = encoding or guessed_encoding
			if not maintype:
				maintype, subtype = 'application', 'octet-stream'
			else:
				maintype, _, subtype = maintype.partition('/')
		
		part = MIMENonMultipart(maintype, subtype)
		part.add_header('Content-Transfer-Encoding', 'base64')
		
		if encoding:
			part.add_header('Content-Encoding', encoding)
		
		if data is None:
			with open(name, 'rb') as fp:
				value = fp.read()
			name = os.path.basename(name)
		elif isinstance(data, bytes):
			value = data
		elif hasattr(data, 'read'):
			value = data.read()
		else:
			raise TypeError("Unable to read attachment contents")
		
		part.set_payload(base64.encodestring(value))
		
		if not filename:
			filename = name
		filename = os.path.basename(filename)
		
		if filename_charset or filename_language:
			if not filename_charset:
				filename_charset = 'utf-8'
			# See https://docs.python.org/2/library/email.message.html#email.message.Message.add_header
			# for more information.
			# add_header() in the email module expects its arguments to be ASCII strings. Go ahead and handle
			# the case where these arguments come in as str strings, since encoding ASCII strings
			# as UTF-8 can't hurt.
			if sys.version_info < (3, 0):
				filename=(filename_charset.encode('utf-8'), filename_language.encode('utf-8'), filename.encode('utf-8'))
			else:
				filename=(filename_charset, filename_language, filename)
		
		if inline:
			if sys.version_info < (3, 0):
				part.add_header('Content-Disposition'.encode('utf-8'), 'inline'.encode('utf-8'), filename=filename)
				part.add_header('Content-ID'.encode('utf-8'), '<%s>'.encode('utf-8') % filename)
			else:	
				part.add_header('Content-Disposition', 'inline', filename=filename)
				part.add_header('Content-ID', '<%s>' % filename)
			self.embedded.append(part)
		else:
			if sys.version_info < (3, 0):
				part.add_header('Content-Disposition'.encode('utf-8'), 'attachment'.encode('utf-8'), filename=filename)
			else:
				part.add_header('Content-Disposition', 'attachment', filename=filename)
			self.attachments.append(part)
	
	def embed(self, name, data=None):
		"""Attach an image file and prepare for HTML embedding.
		
		This method should only be used to embed images.
		
		:param name: Path to the image to embed if data is None, or the name
					 of the file if the ``data`` argument is given
		:param data: Contents of the image to embed, or None if the data is to
					 be read from the file pointed to by the ``name`` argument
		"""
		if data is None:
			with open(name, 'rb') as fp:
				data = fp.read()
			name = os.path.basename(name)
		elif isinstance(data, bytes):
			pass
		elif hasattr(data, 'read'):
			data = data.read()
		else:
			raise TypeError("Unable to read image contents")
		
		subtype = imghdr.what(None, data)
		self.attach(name, data, 'image', subtype, True)
	
	@staticmethod
	def _callable(var):
		if hasattr(var, '__call__'):
			return var()
		
		return var
	
	def send(self):
		"""Attempt to deliver this message using the mailer instance it is bound to."""
		
		if not self.mailer:
			raise NotImplementedError("Message instance is not bound to a Mailer. Use mailer.send() instead.")
		
		return self.mailer.send(self)
