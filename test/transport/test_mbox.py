# encoding: utf-8

from __future__ import unicode_literals

import os
import sys
import logging
import mailbox
import tempfile

from unittest import TestCase
from nose.tools import ok_, eq_, raises
from nose.plugins.skip import Skip, SkipTest

from marrow.mailer import Message
from marrow.mailer.transport.mbox import MailboxTransport


log = logging.getLogger('tests')



class TestMailboxTransport(TestCase):
    def setUp(self):
        _, self.filename = tempfile.mkstemp('.mbox')
        os.close(_)
        
        self.transport = MailboxTransport(dict(file=self.filename))
    
    def tearDown(self):
        self.transport.shutdown()
        os.unlink(self.filename)
    
    def test_bad_config(self):
        self.assertRaises(ValueError, MailboxTransport, dict())
    
    def test_startup(self):
        self.transport.startup()
        self.assertTrue(isinstance(self.transport.box, mailbox.mbox))
    
    def test_shutdown(self):
        self.transport.startup()
        self.transport.shutdown()
        self.assertTrue(self.transport.box is None)
    
    def test_delivery(self):
        message = Message('from@example.com', 'to@example.com', "Test subject.")
        message.plain = "Test message."
        
        self.transport.startup()
        self.transport.deliver(message)
        
        with open(self.filename, 'rb') as fh:
            self.assertEqual(str(message), b"\n".join(fh.read().splitlines()[1:]))
