# encoding: utf-8

"""MIME-encoded electronic mail message class."""

import imghdr
import os
import time

from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.header import Header
from email.utils import make_msgid, formatdate
from mimetypes import guess_type

from marrow.mailer import release
from marrow.mailer.address import Address, AddressList, AutoConverter
from marrow.util.compat import basestring, unicode

__all__ = ['Message']


class Message(object):
    """Represents an e-mail message."""

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

        # Internally used attributes
        self._id = None
        self._processed = False
        self._dirty = False
        self.mailer = None

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
        return self.mime.as_string()

    @property
    def id(self):
        if not self._id or (self._processed and self._dirty):
            self._id = make_msgid()
            self._processed = False
        return self._id

    @property
    def envelope(self):
        """Returns the address of the envelope sender address (SMTP from, if
        not set the sender, if this one isn't set too, the author)."""
        if not self.sender and not self.author:
            raise ValueError("Unable to determine message sender; no author or sender defined.")

        return self.sender or self.author[0]

    @property
    def recipients(self):
        return AddressList(self.to + self.cc + self.bcc)

    def _mime_document(self, plain, rich=None):
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
        # Encode it here to avoid this:
        # Date: =?utf-8?q?Sat=2C_01_Sep_2012_13=3A08=3A29_-0300?=
        return date_value.encode('ascii')

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

        return headers

    def _add_headers_to_message(self, message, headers):
        for header in headers:
            if header[1] is None or (isinstance(header[1], list) and not header[1]):
                continue

            name, value = header

            if isinstance(value, Address):
                value = value.encode(self.encoding)
            elif isinstance(value, AddressList):
                value = value.encode(self.encoding)

            if isinstance(value, unicode):
                value = Header(value, self.encoding)
            else:
                value = Header(value)

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
        #     raise ValueError('If there are multiple authors of message, you must specify a sender!')

        # if len(sender) > 1:
        #     raise ValueError('You must not specify more than one sender!')

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
        inline=False):
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
        self._dirty = True

        if not maintype:
            maintype, _ = guess_type(name)
            if not maintype:
                maintype, subtype = 'application', 'octet-stream'
            else:
                maintype, _, subtype = maintype.partition('/')

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
        if not self.mailer:
            raise NotImplementedError("Message instance is not bound to " \
                "a Mailer. Use mailer.send() instead.")
        return self.mailer.send(self)
