# -*- coding: utf-8 -*-

import json
import base64

try:
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError
except ImportError:  # Python 2
    from urllib2 import Request, urlopen, HTTPError, URLError

from marrow.mailer.exc import DeliveryFailedException, MessageFailedException

__all__ = ['PostmarkTransport']

log = __import__('logging').getLogger(__name__)


def _encode(value, encoding):
    """Encode a value for the JSON payload: bytes on Python 2, text on Python 3."""
    value = value.encode(encoding)
    return value if str is bytes else value.decode(encoding)


class PostmarkTransport(object):
    __slots__ = ('ephemeral', 'key', 'messages')
    
    def __init__(self, config):
        self.key = config.get('key')
        self.messages = []
    
    def _mapmessage(self, message):
        args = dict({
            'From': _encode(message.author, message.encoding),
            'To': _encode(message.to, message.encoding),
            'Subject': _encode(message.subject, message.encoding),
            'TextBody': _encode(message.plain, message.encoding),
        })
            
        if message.cc:
            args['Cc'] = _encode(message.cc, message.encoding)

        if message.bcc:
            args['Bcc'] = _encode(message.bcc, message.encoding)
        
        if message.reply:
            args['ReplyTo'] = _encode(message.reply, message.encoding)
        
        if message.rich:
            args['HtmlBody'] = _encode(message.rich, message.encoding)
        
        if message.attachments:
            args['Attachments'] = []
            
            for attachment in message.attachments:
                args['Attachments'].append(
                    {
                        "Name": attachment.get_filename(),
                        "Content": base64.b64encode(attachment.get_payload(decode=True)).decode('ascii'),
                        "ContentType": attachment.get_content_type()
                    }
                )

        return args

    def _batchsend(self):
        request = Request(
            "https://api.postmarkapp.com/email/batch",
            json.dumps(self.messages).encode('utf-8'),
            {
                'Accept': "application/json",
                'Content-Type': "application/json",
                'X-Postmark-Server-Token': self.key,
            }
        )

        try:
            response = urlopen(request)
        except (HTTPError, URLError) as e:
            raise DeliveryFailedException(e, "Could not connect to Postmark.")
        else:
            respcode = response.getcode()
            if respcode >= 400 and respcode <= 499:
                raise MessageFailedException(response.read())
            elif respcode >= 500 and respcode <= 599:
                raise DeliveryFailedException(self.messages[0], "Postmark service unavailable. Just diplaying first message of batch")

        del self.messages[:]

    def startup(self):
        self.messages = []
    
    def deliver(self, message):
        if len(self.messages) >= 500:
            # Postmark allows to send a maximum of 500 emails over its batch API
            self._batchsend()
        
        args = self._mapmessage(message)
        self.messages.append(args)
    
    def shutdown(self):
        self._batchsend()
