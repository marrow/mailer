# encoding: utf-8

"""MIME-encoded electronic mail message classes."""

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.header import Header
from email.utils import make_msgid, formatdate
from mimetypes import guess_type
from datetime import datetime
import imghdr
import os
import time
import warnings

from marrow.mailer.address import Address, AddressList, AutoConverter
from marrow.util.compat import basestring

__all__ = ['Message']


class Message(object):
    """Represents an e-mail message."""

    def __init__(self, author=None, to=None, subject=None, **kw):
        """Instantiate a new Message object.

        No arguments are required, as everything can be set using class
        properties.  Alternatively, __everything__ can be set using the
        constructor, using named arguments.  The first three positional
        arguments can be used to quickly prepare a simple message.
        """
        self.sender = kw.pop('sender', None)
        self.author = kw.pop('author', None)
        self.to = kw.pop('to', None)
        self.cc = kw.pop('cc', None)
        self.bcc = kw.pop('bcc', None)
        self.reply = kw.pop('reply', None)
        self.notify = kw.pop('disposition', None)

        self.subject = kw.pop('subject', None)
        self.date = kw.pop('date', None)

        self.encoding = kw.pop('encoding', 'utf-8')

        self.organization = kw.pop('organization')
        self.priority = kw.pop('priority')

        self.plain = kw.pop('plain', None)
        self.rich = kw.pop('rich', None)
        self.attachments = kw.pop('attachments', [])
        self.embedded = kw.pop('embedded', [])
        self.headers = kw.pop('headers', [])
        self.nr_retries = kw.pop('nr_retries', 3)

        self._id = kw.get('id', None)

        self._processed = False
        self._dirty = False
        if len(kw) > 0:
            parameter_name = kw.keys()[0]
            error_msg = "__init__() got an unexpected keyword argument '%s'"
            raise TypeError(error_msg % parameter_name)

    sender = AutoConverter(Address)
    author = AutoConverter(Address)
    to = AutoConverter(AddressList)
    bcc = AutoConverter(AddressList)
    cc = AutoConverter(AddressList)
    reply = AutoConverter(AddressList)
    notify = AutoConverter(AddressList)

    def __setattr__(self, name, value):
        """Set the dirty flag as properties are updated."""
        object.__setattr__(self, name, value)
        if name not in ('bcc', '_id', '_dirty', '_processed'):
            object.__setattr__(self, '_dirty', True)

    def __str__(self):
        return self.mime.as_string()

    @property
    def id(self):
        if not self._id or (self._processed and self._dirty):
            self._id = make_msgid()
            self._processed = False
        return self._id

    @property
    def envelope_sender(self):
        """Returns the address of the envelope sender address (SMTP from, if
        not set the sender, if this one isn't set too, the author)."""
        return self.sender or self.author

    @property
    def recipients(self):
        return AddressList(self.to + self.cc + self.bcc)

    def mime_document(self, plain, rich=None):
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
        """Gets the date_value (may be None, basestring, float or
        datetime.datetime instance) and returns a valid date string as per
        RFC 2822."""
        if isinstance(date_value, datetime):
            date_value = time.mktime(date_value.timetuple())
        if not isinstance(date_value, basestring):
            date_value = formatdate(date_value, localtime=True)
        return date_value

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
                ('Disposition-Notification-To', self.disposition),
                ('Organization', self.organization),
                ('X-Priority', self.priority),
            ]

        if isinstance(self.headers, dict):
            for key in self.headers:
                headers.append((key, self.headers[key]))
        else:
            headers.extend(self.headers)
        return headers

    def _add_headers_to_message(self, message, headers):
        for header in headers:
            if isinstance(header, (tuple, list)):
                if header[1] is None or (isinstance(header[1], list) and not header[1]):
                    continue
                header = list(header)
                if isinstance(header[1], AddressList):
                    header[1] = Header(header[1].encode(self.encoding))
                elif isinstance(header[1], unicode):
                    header[1] = Header(header[1], self.encoding)
                else:
                    header[1] = Header(header[1])
                message[header[0]] = header[1]
            elif isinstance(header, dict):
                message.add_header(**header)

    @property
    def mime(self):
        """Produce the final MIME message."""
        author = self.author
        sender = self.sender
        if not author and sender:
            msg = 'Please specify the author using the "author" property. ' + \
                  'Using "sender" for the From header is deprecated!'
            warnings.warn(msg, category=DeprecationWarning)
            author = sender
            sender = []
        if not author:
            raise ValueError('You must specify an author.')

        assert self.subject, "You must specify a subject."
        assert len(self.recipients) > 0, "You must specify at least one recipient."
        assert self.plain, "You must provide plain text content."

        if len(author) > 1 and len(sender) == 0:
            raise ValueError('If there are multiple authors of message, you must specify a sender!')
        if len(sender) > 1:
            raise ValueError('You must not specify more than one sender!')

        if not self._dirty and self._processed:
            return self._mime

        self._processed = False

        plain = MIMEText(self._callable(self.plain), 'plain', self.encoding)

        rich = None
        if self.rich:
            rich = MIMEText(self._callable(self.rich), 'html', self.encoding)

        message = self.mime_document(plain, rich)
        headers = self._build_header_list(author, sender)
        self._add_headers_to_message(message, headers)

        self._mime = message
        self._processed = True
        self._dirty = False

        return message

    def attach(self, name, data=None, maintype=None, subtype=None, inline=False):
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
        """
        if not maintype:
            maintype, subtype = guess_type(name)
            if not maintype:
                maintype, subtype = 'application', 'octet-stream'

        part = MIMENonMultipart(maintype, subtype)

        if data is None:
            with open(name, 'rb') as fp:
                part.set_payload(fp.read())
            name = os.path.basename(name)
        elif isinstance(data, bytes):
            part.set_payload(data)
        elif hasattr(data, 'read'):
            part.set_payload(data.read())
        else:
            raise TypeError("Unable to read attachment contents")

        if inline:
            part.add_header('Content-Disposition', 'inline', filename=name)
            part.add_header('Content-ID', '<%s>' % name)
            self.embedded.append(part)
        else:
            part.add_header('Content-Disposition', 'attachment', filename=name)
            self.attachments.append(part)

    def embed_image(self, name, data=None):
        """Attach an image file and prepare for HTML embedding.

        This method should only be used to embed images.

        :param name: Path to the image to embed if data is None, or the name
                     of the file if the ``data`` argument is given
        :param data: Contents of the image to embed, or None if the data is to
                     be read from the file pointed to by the ``name`` argument
        """
        if data is None:
            name = os.path.basename(name)
            with open(file, 'rb') as fp:
                data = fp.read()
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
        if callable(var):
            return var()
        return var
