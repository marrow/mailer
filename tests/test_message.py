# encoding: utf-8
"""Test the TurboMail Message class."""

from __future__ import unicode_literals

import calendar
from datetime import datetime, timedelta
import email
import logging
import re
import time
import unittest

from email.header import Header
from email.mime.text import MIMEText
from email.utils import formatdate, parsedate_tz

from marrow.mailer import Message
from marrow.mailer.address import AddressList

from nose.tools import raises

# logging.disable(logging.WARNING)


class TestBasicMessage(unittest.TestCase):
    """Test the basic output of the Message class."""
    
    gif = b'47494638396101000100910000000000000000fe010200000021f904041400ff002c00000000010001000002024401003b'
    
    def build_message(self, **kw):
        return Message(
                    author=('Author', 'author@example.com'),
                    to=('Recipient', 'recipient@example.com'),
                    subject='Test message subject.',
                    plain='This is a test message plain text body.',
                    **kw
                )
    
    def test_missing_values(self):
        message = Message()
        self.assertRaises(ValueError, str, message)
        
        message.author = "bob.dole@whitehouse.gov"
        self.assertRaises(ValueError, str, message)
        
        message.subject = "Attn: Bob Dole"
        self.assertRaises(ValueError, str, message)
        
        message.to = "user@example.com"
        self.assertRaises(ValueError, str, message)
        
        message.plain = "Testing!"
        
        try:
            str(message)
        except ValueError:
            self.fail("Message should be valid.")
    
    def test_message_id(self):
        msg = self.build_message()
        
        self.assertEquals(msg._id, None)
        
        id_ = msg.id
        self.assertEquals(msg._id, id_)
        
        self.assertEquals(msg.id, id_)
    
    def test_missing_author(self):
        message = self.build_message()
        message.author = []
        
        self.assertRaises(ValueError, lambda: message.envelope)
    
    def test_message_properties(self):
        message = self.build_message()
        self.assertEqual(message.author, [("Author", "author@example.com")])
        self.assertEqual(str(message.author), "Author <author@example.com>")
        self.failUnless(isinstance(message.mime, MIMEText))
    
    def test_message_string_with_basic(self):
        msg = email.message_from_string(str(self.build_message(encoding="iso-8859-1")))
        
        self.assertEqual('Author <author@example.com>', msg['From'])
        self.assertEqual('Recipient <recipient@example.com>', msg['To'])
        self.assertEqual('Test message subject.', msg['Subject'])
        self.assertEqual('This is a test message plain text body.', msg.get_payload())
    
    def test_message_recipients_and_addresses(self):
        message = self.build_message()
        
        message.cc = 'cc@example.com'
        message.bcc = 'bcc@example.com'
        message.sender = 'sender@example.com'
        message.reply = 'replyto@example.com'
        message.notify = 'disposition@example.com'
        
        msg = email.message_from_string(str(message))
        
        self.assertEqual('cc@example.com', msg['cc'])
        self.assertEqual(None, msg['bcc'])
        self.assertEqual('sender@example.com', msg['sender'])
        self.assertEqual('replyto@example.com', msg['reply-to'])
        self.assertEqual('disposition@example.com', msg['disposition-notification-to'])
    
    def test_mime_generation_plain(self):
        message = self.build_message()
        mime = message.mime
        
        self.failUnless(message.mime is mime)
        message.subject = "Test message subject."
        self.failIf(message.mime is mime)
    
    def test_mime_generation_rich(self):
        message = self.build_message()
        message.plain = "Hello world."
        message.rich = "Farewell cruel world."
        
        self.failUnless('Hello world.' in str(message))
        self.failUnless('Farewell cruel world.' in str(message))
    
    def test_mime_generation_rich_embedded(self):
        message = self.build_message()
        message.plain = "Hello world."
        message.rich = "Farewell cruel world."
        
        message.attach("hello.txt", b"Fnord.", "text", "plain", True)
        
        self.failUnless('Hello world.' in str(message))
        self.failUnless('Farewell cruel world.' in str(message))
        self.failUnless('hello.txt' in str(message))
        self.failUnless('Fnord.' in str(message))
    
    def test_mime_attachments(self):
        message = self.build_message()
        message.plain = "Hello world."
        message.rich = "Farewell cruel world."
        
        message.attach("hello.txt", b"Fnord.")
        
        self.failUnless('Hello world.' in str(message))
        self.failUnless('Farewell cruel world.' in str(message))
        self.failUnless('hello.txt' in str(message))
        self.failUnless('Fnord.' in str(message))
        self.failUnless('text/plain\n' in str(message))
    
    def test_mime_attachments_unknown(self):
        message = self.build_message()
        message.plain = "Hello world."
        message.rich = "Farewell cruel world."
        message.attach('test.xbin', b"Word.")
        self.failUnless('test.xbin' in str(message))
        self.failUnless('application/octet-stream' in str(message))
        
        self.assertRaises(TypeError, message.attach, 'foo', object())
    
    def test_mime_attachments_file(self):
        import tempfile
        
        message = self.build_message()
        message.plain = "Hello world."
        message.rich = "Farewell cruel world."
        
        with tempfile.NamedTemporaryFile() as fh:
            fh.write("foo")
            fh.flush()
            
            message.attach(fh.name)
            self.failUnless('application/octet-stream' in str(message))
            self.failUnless('foo' in str(message))
    
    def test_mime_attachments_filelike(self):
        class Mock(object):
            def read(self):
                return b'foo'
        
        message = self.build_message()
        message.plain = "Hello world."
        message.rich = "Farewell cruel world."
        message.attach('test.xbin', Mock())
        self.failUnless('test.xbin' in str(message))
        self.failUnless('application/octet-stream' in str(message))
        self.failUnless('foo' in str(message))
    
    def test_mime_embed_gif_file(self):
        import tempfile
        import codecs
        
        message = self.build_message()
        message.plain = "Hello world."
        message.rich = "Farewell cruel world."
        
        with tempfile.NamedTemporaryFile() as fh:
            fh.write(codecs.decode(self.gif, 'hex'))
            fh.flush()
            
            message.embed(fh.name)
            
            result = bytes(message)
            
            self.failUnless(b'image/gif' in result)
            self.failUnless(b'GIF89a' in result)
    
    def test_mime_embed_gif_bytes(self):
        import codecs
        
        message = self.build_message()
        message.plain = "Hello world."
        message.rich = "Farewell cruel world."
        message.embed('test.gif', bytes(codecs.decode(self.gif, 'hex')))
        
        result = bytes(message)
        
        self.failUnless(b'image/gif' in result)
        self.failUnless(b'GIF89a' in result)
        
        class Mock(object):
            def read(s):
                return codecs.decode(self.gif, 'hex')
        
        message = self.build_message()
        message.plain = "Hello world."
        message.rich = "Farewell cruel world."
        message.embed('test.gif', Mock())
        
        result = bytes(message)
        
        self.failUnless(b'image/gif' in result)
        self.failUnless(b'GIF89a' in result)
    
    def test_mime_embed_failures(self):
        message = self.build_message()
        message.plain = "Hello world."
        message.rich = "Farewell cruel world."
        
        self.assertRaises(TypeError, message.embed, 'test.gif', object())
    
    def test_recipients_collection(self):
        message = self.build_message()
        message.cc.append("copied@example.com")
        self.assertEqual(["recipient@example.com", "copied@example.com"], message.recipients.addresses)
    
    def test_smtp_from_as_envelope(self):
        message = self.build_message()
        message.sender = 'devnull@example.com'
        self.assertEqual('devnull@example.com', str(message.envelope))
    
    def test_subject_with_umlaut(self):
        message = self.build_message()
        
        subject_string = "Test with äöü"
        message.subject = subject_string
        message.encoding = "UTF-8"
        
        msg = email.message_from_string(str(message))
        encoded_subject = str(Header(subject_string, "UTF-8"))
        self.assertEqual(encoded_subject, msg['Subject'])
    
    def test_from_with_umlaut(self):
        message = self.build_message()
        
        from_name = "Karl Müller"
        from_email = "karl.mueller@example.com"
        
        message.author = [(from_name, from_email)]
        message.encoding = "ISO-8859-1"
        
        msg = email.message_from_string(str(message))
        encoded_name = "%s <%s>" % (str(Header(from_name, "ISO-8859-1")), from_email)
        self.assertEqual(encoded_name, msg['From'])
    
    def test_multiple_authors(self):
        message = self.build_message()
        
        message.authors = 'authors@example.com'
        self.assertEqual(message.authors, message.author)
        
        message.authors = ['bar@example.com', 'baz@example.com']
        message.sender = 'foo@example.com'
        msg = email.message_from_string(str(message))
        from_addresses = re.split(r",\n?\s+", msg['From'])
        self.assertEqual(['bar@example.com', 'baz@example.com'], from_addresses)
    
    # def test_multiple_authors_require_sender(self):
    #     message = self.build_message()
    #     
    #     message.authors = ['bar@example.com', 'baz@example.com']
    #     self.assertRaises(ValueError, str, message)
    #     
    #     message.sender = 'bar@example.com'
    #     str(message)
    
    @raises(ValueError)
    def test_permit_one_sender_at_most(self):
        message = self.build_message()
        message.sender = AddressList(['bar@example.com', 'baz@example.com'])
    
    def test_raise_error_for_unknown_kwargs_at_class_instantiation(self):
        self.assertRaises(TypeError, Message, invalid_argument=True)
    
    def test_add_custom_headers_dict(self):
        message = self.build_message()
        message.headers = {'Precedence': 'bulk', 'X-User': 'Alice'}
        msg = email.message_from_string(str(message))
        
        self.assertEqual('bulk', msg['Precedence'])
        self.assertEqual('Alice', msg['X-User'])
    
    def test_add_custom_headers_tuple(self):
        message = self.build_message()
        message.headers = (('Precedence', 'bulk'), ('X-User', 'Alice'))
        
        msg = email.message_from_string(str(message))
        self.assertEqual('bulk', msg['Precedence'])
        self.assertEqual('Alice', msg['X-User'])

    def test_add_custom_headers_list(self):
        "Test that a custom header (list type) can be attached."
        message = self.build_message()
        message.headers = [('Precedence', 'bulk'), ('X-User', 'Alice')]
        
        msg = email.message_from_string(str(message))
        self.assertEqual('bulk', msg['Precedence'])
        self.assertEqual('Alice', msg['X-User'])
    
    def test_no_sender_header_if_no_sender_required(self):
        message = self.build_message()
        msg = email.message_from_string(str(message))
        self.assertEqual(None, msg['sender'])
    
    def _date_header_to_utc_datetime(self, date_string):
        """Converts a date_string from the Date header into a naive datetime
        object in UTC."""
        # There is pytz which could solve whole isssue but it is not in Fedora
        # EPEL 4 currently so I don't want to depend on out-of-distro modules - 
        # hopefully I'll get it right anyway...
        assert date_string != None
        tztime_struct = parsedate_tz(date_string)
        time_tuple, tz_offset = (tztime_struct[:9], tztime_struct[9])
        epoch_utc_seconds = calendar.timegm(time_tuple)
        if tz_offset is not None:
            epoch_utc_seconds -= tz_offset
        datetime_obj = datetime.utcfromtimestamp(epoch_utc_seconds)
        return datetime_obj
    
    def _almost_now(self, date_string):
        """Returns True if the date_string represents a time which is 'almost 
        now'."""
        utc_date = self._date_header_to_utc_datetime(date_string)
        delta = abs(datetime.utcnow() - utc_date)
        return (delta < timedelta(seconds=1))
    
    def test_date_header_added_even_if_date_not_set_explicitely(self):
        message = self.build_message()
        msg = email.message_from_string(str(message))
        self.failUnless(self._almost_now(msg['Date']))
    
    def test_date_can_be_set_as_string(self):
        message = self.build_message()
        date_string = 'Fri, 26 Dec 2008 11:19:42 +0530'
        message.date = date_string
        msg = email.message_from_string(str(message))
        self.assertEqual(date_string, msg['Date'])
    
    def test_date_can_be_set_as_float(self):
        message = self.build_message()
        expected_date = datetime(2008, 12, 26, 12, 55)
        expected_time = time.mktime(expected_date.timetuple())
        message.date = expected_time
        msg = email.message_from_string(str(message))
        header_string = msg['Date']
        header_date = self._date_header_to_utc_datetime(header_string)
        self.assertEqual(self.localdate_to_utc(expected_date), header_date)
        expected_datestring = formatdate(expected_time, localtime=True)
        self.assertEqual(expected_datestring, header_string)
    
    def localdate_to_utc(self, localdate):
        local_epoch_seconds = time.mktime(localdate.timetuple())
        date_string = formatdate(local_epoch_seconds, localtime=True)
        return self._date_header_to_utc_datetime(date_string)
    
    def test_date_can_be_set_as_datetime(self):
        message = self.build_message()
        expected_date = datetime(2008, 12, 26, 12, 55)
        message.date = expected_date
        msg = email.message_from_string(str(message))
        header_date = self._date_header_to_utc_datetime(msg['Date'])
        self.assertEqual(self.localdate_to_utc(expected_date), header_date)
    
    def test_date_header_is_set_even_if_reset_to_none(self):
        message = self.build_message()
        message.date = None
        msg = email.message_from_string(str(message))
        self.failUnless(self._almost_now(msg['Date']))
    
    def test_recipients_property_includes_cc_and_bcc(self):
        message = self.build_message()
        message.cc = 'cc@example.com'
        message.bcc = 'bcc@example.com'
        expected_recipients = ['recipient@example.com', 'cc@example.com', 
                               'bcc@example.com']
        recipients = map(str, list(message.recipients.addresses))
        self.assertEqual(expected_recipients, recipients)
    
    def test_can_set_encoding_for_message_explicitely(self):
        message = self.build_message()
        self.failIf('iso-8859-1' in str(message).lower())
        message.encoding = 'ISO-8859-1'
        msg = email.message_from_string(str(message))
        self.assertEqual('text/plain; charset="iso-8859-1"', msg['Content-Type'])
        self.assertEqual('quoted-printable', msg['Content-Transfer-Encoding'])
    
    # def test_message_encoding_can_be_set_in_config_file(self):
    #     interface.config['mail.message.encoding'] = 'ISO-8859-1'
    #     message = self.build_message()
    #     msg = email.message_from_string(str(message))
    #     self.assertEqual('text/plain; charset="iso-8859-1"', msg['Content-Type'])
    #     self.assertEqual('quoted-printable', msg['Content-Transfer-Encoding'])
    
    def test_plain_utf8_encoding_uses_qp(self):
        message = self.build_message()
        msg = email.message_from_string(str(message))
        self.assertEqual('text/plain; charset="utf-8"', msg['Content-Type'])
        self.assertEqual('quoted-printable', msg['Content-Transfer-Encoding'])
    
    def test_callable_bodies(self):
        message = self.build_message()
        message.plain = lambda: "plain text"
        message.rich = lambda: "rich text"
        
        self.assertTrue('plain text' in str(message))
        self.assertTrue('rich text' in str(message))
