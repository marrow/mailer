# encoding: utf-8

from __future__ import unicode_literals

import os
import sys
import shutil
import logging
import mailbox
import tempfile

from unittest import TestCase
from nose.tools import ok_, eq_, raises
from nose.plugins.skip import Skip, SkipTest

from marrow.mailer import Message
from marrow.mailer.transport.maildir import MaildirTransport


log = logging.getLogger('tests')



class TestMailDirectoryTransport(TestCase):
    def setUp(self):
        self.path = tempfile.mkdtemp()
        
        for i in ('cur', 'new', 'tmp'):
            os.mkdir(os.path.join(self.path, i))
        
        self.transport = MaildirTransport(dict(directory=self.path, create=True))
    
    def tearDown(self):
        self.transport.shutdown()
        shutil.rmtree(self.path)
    
    def test_bad_config(self):
        self.assertRaises(ValueError, MaildirTransport, dict())
    
    def test_startup(self):
        self.transport.startup()
        self.assertTrue(isinstance(self.transport.box, mailbox.Maildir))
    
    def test_child_folder_startup(self):
        self.transport.folder = 'test'
        self.transport.startup()
        self.assertTrue(os.path.exists(os.path.join(self.path, '.test')))
    
    def test_shutdown(self):
        self.transport.startup()
        self.transport.shutdown()
        self.assertTrue(self.transport.box is None)
    
    def test_delivery(self):
        message = Message('from@example.com', 'to@example.com', "Test subject.")
        message.plain = "Test message."
        
        self.transport.startup()
        self.transport.deliver(message)
        
        filename = os.listdir(os.path.join(self.path, 'new'))[0]
        
        with open(os.path.join(self.path, 'new', filename), 'rb') as fh:
            self.assertEqual(str(message), fh.read())
