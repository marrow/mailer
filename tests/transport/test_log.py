# encoding: utf-8

import logging

from unittest import TestCase

from marrow.mailer import Message
from marrow.mailer.transport.log import LoggingTransport


log = logging.getLogger('tests')



class TestLoggingTransport(TestCase):
    def setUp(self):
        self.messages = logging.getLogger().handlers[0].buffer
        del self.messages[:]
        
        self.transport = LoggingTransport(dict())
        self.transport.startup()
    
    def tearDown(self):
        self.transport.shutdown()
    
    def test_startup(self):
        self.assertEqual(len(self.messages), 1)
        self.assertEqual(self.messages[0].getMessage(), "Logging transport starting.")
        self.assertEqual(self.messages[0].levelname, 'DEBUG')
    
    def test_shutdown(self):
        self.transport.shutdown()
        
        self.assertEqual(len(self.messages), 2)
        self.assertEqual(self.messages[0].getMessage(), "Logging transport starting.")
        self.assertEqual(self.messages[1].getMessage(), "Logging transport stopping.")
        self.assertEqual(self.messages[1].levelname, 'DEBUG')
    
    def test_delivery(self):
        self.assertEqual(len(self.messages), 1)
        
        message = Message('from@example.com', 'to@example.com', 'Subject.', plain='Body.')
        msg = str(message)
        
        self.transport.deliver(message)
        self.assertEqual(len(self.messages), 3)
        
        expect = "DELIVER %s %s %d %r %r" % (message.id, message.date.isoformat(),
            len(msg), message.author, message.recipients)
        
        self.assertEqual(self.messages[0].getMessage(), "Logging transport starting.")
        self.assertEqual(self.messages[1].getMessage(), expect)
        self.assertEqual(self.messages[1].levelname, 'INFO')
        self.assertEqual(self.messages[2].getMessage(), str(message))
        self.assertEqual(self.messages[2].levelname, 'CRITICAL')
