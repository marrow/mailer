# encoding: utf-8

from __future__ import unicode_literals

import os
import sys
import socket
import logging
import smtplib

from unittest import TestCase
from nose.tools import ok_, eq_, raises
from nose.plugins.skip import Skip, SkipTest

try:
    from pymta.api import IMTAPolicy, PolicyDecision, IAuthenticator
    from pymta.test_util import BlackholeDeliverer, DebuggingMTA, MTAThread
except ImportError: # pragma: no cover
    raise SkipTest("PyMTA not installed; skipping SMTP tests.")

from marrow.mailer import Message
from marrow.mailer.exc import TransportException, TransportExhaustedException, MessageFailedException
from marrow.mailer.transport.smtp import SMTPTransport


log = logging.getLogger('tests')


class SMTPTestCase(TestCase):
    server = None
    Policy = IMTAPolicy
    
    class Authenticator(IAuthenticator):
        def authenticate(self, username, password, peer):
            return True
    
    @classmethod
    def setUpClass(cls):
        assert not cls.server, "Server already running?"
        
        cls.port = __import__('random').randint(9000, 40000)
        cls.collector = BlackholeDeliverer
        cls.host = DebuggingMTA('127.0.0.1', cls.port, cls.collector, policy_class=cls.Policy,
                authenticator_class=cls.Authenticator)
        cls.server = MTAThread(cls.host)
        cls.server.start()
    
    @classmethod
    def tearDownClass(cls):
        if cls.server:
            cls.server.stop()
            cls.server = None


class TestSMTPTransportBase(SMTPTestCase):
    def test_basic_config(self):
        transport = SMTPTransport(dict(port=self.port, timeout="10", tls=False, pipeline="10"))
        
        self.assertEqual(transport.sent, 0)
        self.assertEqual(transport.host, '127.0.0.1')
        self.assertEqual(transport.port, self.port)
        self.assertEqual(transport.timeout, 10)
        self.assertEqual(transport.pipeline, 10)
        self.assertEqual(transport.debug, False)
        
        self.assertEqual(transport.connected, False)
    
    def test_startup_shutdown(self):
        transport = SMTPTransport(dict(port=self.port))
        
        transport.startup()
        self.assertTrue(transport.connected)
        
        transport.shutdown()
        self.assertFalse(transport.connected)
    
    def test_authentication(self):
        transport = SMTPTransport(dict(port=self.port, username='bob', password='dole'))
        
        transport.startup()
        self.assertTrue(transport.connected)
        
        transport.shutdown()
        self.assertFalse(transport.connected)
    
    def test_bad_tls(self):
        transport = SMTPTransport(dict(port=self.port, tls='required'))
        self.assertRaises(TransportException, transport.startup)


class TransportTestCase(SMTPTestCase):
    pipeline = None
    
    def setUp(self):
        self.transport = SMTPTransport(dict(port=self.port, pipeline=self.pipeline))
        self.transport.startup()
        self.msg = self.message
    
    def tearDown(self):
        self.transport.shutdown()
        self.transport = None
        self.msg = None
    
    @property
    def message(self):
        return Message('from@example.com', 'to@example.com', 'Test subject.', plain="Test body.")


class TestSMTPTransport(TransportTestCase):
    def test_send_simple_message(self):
        self.assertRaises(TransportExhaustedException, self.transport.deliver, self.msg)
        self.assertEqual(self.collector.received_messages.qsize(), 1)
        
        message = self.collector.received_messages.get()
        self.assertEqual(message.msg_data, str(self.msg))
        self.assertEqual(message.smtp_from, self.msg.envelope)
        self.assertEqual(message.smtp_to, self.msg.recipients)
    
    def test_send_after_shutdown(self):
        self.transport.shutdown()
        
        self.assertRaises(TransportExhaustedException, self.transport.deliver, self.msg)
        self.assertEqual(self.collector.received_messages.qsize(), 1)
        
        message = self.collector.received_messages.get()
        self.assertEqual(message.msg_data, str(self.msg))
        self.assertEqual(message.smtp_from, self.msg.envelope)
        self.assertEqual(message.smtp_to, self.msg.recipients)
    
    def test_sender(self):
        self.msg.sender = "sender@example.com"
        self.assertEqual(self.msg.envelope, self.msg.sender)
        
        self.assertRaises(TransportExhaustedException, self.transport.deliver, self.msg)
        self.assertEqual(self.collector.received_messages.qsize(), 1)
        
        message = self.collector.received_messages.get()
        self.assertEqual(message.msg_data, str(self.msg))
        self.assertEqual(message.smtp_from, self.msg.envelope)
    
    def test_many_recipients(self):
        self.msg.cc = 'cc@example.com'
        self.msg.bcc = 'bcc@example.com'
        
        self.assertRaises(TransportExhaustedException, self.transport.deliver, self.msg)
        self.assertEqual(self.collector.received_messages.qsize(), 1)
        
        message = self.collector.received_messages.get()
        self.assertEqual(message.msg_data, str(self.msg))
        self.assertEqual(message.smtp_from, self.msg.envelope)
        self.assertEqual(message.smtp_to, self.msg.recipients)


class TestSMTPTransportRefusedSender(TransportTestCase):
    pipeline = 10
    
    class Policy(IMTAPolicy):
        def accept_from(self, sender, message):
            return False
    
    def test_refused_sender(self):
        self.assertRaises(MessageFailedException, self.transport.deliver, self.msg)
        self.assertEquals(self.collector.received_messages.qsize(), 0)


class TestSMTPTransportRefusedRecipients(TransportTestCase):
    pipeline = True
    
    class Policy(IMTAPolicy):
        def accept_rcpt_to(self, sender, message):
            return False
    
    def test_refused_recipients(self):
        self.assertRaises(MessageFailedException, self.transport.deliver, self.msg)
        self.assertEquals(self.collector.received_messages.qsize(), 0)


'''
    def get_connection(self):
        # We can not use the id of transport.connection because sometimes Python
        # returns the same id for new, but two different instances of the same
        # object (Fedora 10, Python 2.5):
        # class Bar: pass
        # id(Bar()) == id(Bar())  -> True
        sock = getattr(interface.manager.transport.connection, 'sock', None)
        return sock
    
    def get_transport(self):
        return interface.manager.transport
    
    def test_close_connection_when_max_messages_per_connection_was_reached(self):
        self.config['mail.smtp.max_messages_per_connection'] = 2
        self.init_mta()
        self.msg.send()
        first_connection = self.get_connection()
        self.msg.send()
        second_connection = self.get_connection()
        
        queue = self.get_received_messages()
        self.assertEqual(2, queue.qsize())
        self.assertNotEqual(first_connection, second_connection)
    
    def test_close_connection_when_max_messages_per_connection_was_reached_even_on_errors(self):
        self.config['mail.smtp.max_messages_per_connection'] = 1
        class RejectHeloPolicy(IMTAPolicy):
            def accept_helo(self, sender, message):
                return False
        self.init_mta(policy_class=RejectHeloPolicy)
        
        self.msg.send()
        self.assertEqual(False, self.get_transport().is_connected())
    
    def test_reopen_connection_when_server_closed_connection(self):
        self.config['mail.smtp.max_messages_per_connection'] = 2
        class DropEverySecondConnectionPolicy(IMTAPolicy):
            def accept_msgdata(self, sender, message):
                if not hasattr(self, 'nr_connections'):
                    self.nr_connections = 0
                self.nr_connections = (self.nr_connections + 1) % 2
                decision = PolicyDecision(True)
                drop_this_connection = (self.nr_connections == 1)
                decision._close_connection_after_response = drop_this_connection
                return decision
        self.init_mta(policy_class=DropEverySecondConnectionPolicy)
        
        self.msg.send()
        first_connection = self.get_connection()
        self.msg.send()
        second_connection = self.get_connection()
        
        queue = self.get_received_messages()
        self.assertEqual(2, queue.qsize())
        opened_new_connection = (first_connection != second_connection)
        self.assertEqual(True, opened_new_connection)
    
    def test_smtp_shutdown_ignores_socket_errors(self):
        self.config['mail.smtp.max_messages_per_connection'] = 2
        class CloseConnectionAfterDeliveryPolicy(IMTAPolicy):
            def accept_msgdata(self, sender, message):
                decision = PolicyDecision(True)
                decision._close_connection_after_response = True
                return decision
        self.init_mta(policy_class=CloseConnectionAfterDeliveryPolicy)
        
        self.msg.send()
        smtp_transport = self.get_transport()
        interface.stop(force=True)
        
        queue = self.get_received_messages()
        self.assertEqual(1, queue.qsize())
        self.assertEqual(False, smtp_transport.is_connected())
    
    def test_handle_server_which_rejects_all_connections(self):
        class RejectAllConnectionsPolicy(IMTAPolicy):
            def accept_new_connection(self, peer):
                return False
        self.init_mta(policy_class=RejectAllConnectionsPolicy)
        
        self.assertRaises(smtplib.SMTPServerDisconnected, self.msg.send)
    
    def test_handle_error_when_server_is_not_running_at_all(self):
        self.init_mta()
        self.assertEqual(None, self.get_transport())
        interface.config['mail.smtp.server'] = 'localhost:47115'
        
        self.assertRaises(socket.error, self.msg.send)
    
    def test_can_retry_failed_connection(self):
        self.config['mail.message.nr_retries'] = 4
        class DropFirstFourConnectionsPolicy(IMTAPolicy):
            def accept_msgdata(self, sender, message):
                if not hasattr(self, 'nr_connections'):
                    self.nr_connections = 0
                self.nr_connections += 1
                return (self.nr_connections > 4)
        self.init_mta(policy_class=DropFirstFourConnectionsPolicy)
        
        msg = self.build_message()
        self.assertEqual(4, msg.nr_retries)
        msg.send()
        
        queue = self.get_received_messages()
        self.assertEqual(1, queue.qsize())

'''
