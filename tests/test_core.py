# encoding: utf-8

"""Test the primary configurator interface, Delivery."""

import logging

from unittest import TestCase

from marrow.mail import Delivery
from marrow.mail.exc import MailerNotRunning
from marrow.mail.manager.immediate import ImmediateManager
from marrow.mail.transport.mock import MockTransport

from marrow.util.bunch import Bunch


log = logging.getLogger('tests')


base_config = {'manager': 'immediate', 'transport': 'mock'}



class TestLookup(TestCase):
    def test_load_literal(self):
        self.assertEqual(Delivery._load(ImmediateManager, None), ImmediateManager)
    
    def test_load_dotcolon(self):
        self.assertEqual(Delivery._load('marrow.mail.manager.immediate:ImmediateManager', None), ImmediateManager)
    
    def test_load_entrypoint(self):
        self.assertEqual(Delivery._load('immediate', 'marrow.mailer.manager'), ImmediateManager)


class TestInitialization(TestCase):
    def test_standard(self):
        config = {
                'manager': 'immediate',
                'transport': 'mock'
            }
        
        log.info("Testing configuration: %r", dict(config))
        a = Delivery(config)
        
        self.assertEqual(a.Manager, ImmediateManager)
        self.assertEqual(a.Transport, MockTransport)
    
    def test_prefix(self):
        config = {
                'mail.manager': 'immediate',
                'mail.transport': 'mock'
            }
        
        log.info("Testing configuration: %r", dict(config))
        a = Delivery(config, 'mail')
        
        self.assertEqual(a.Manager, ImmediateManager)
        self.assertEqual(a.Transport, MockTransport)
    
    def test_deep_prefix(self):
        config = {
                'marrow.mail.manager': 'immediate',
                'marrow.mail.transport': 'mock'
            }
        
        log.info("Testing configuration: %r", dict(config))
        a = Delivery(config, 'marrow.mail')
        
        self.assertEqual(a.Manager, ImmediateManager)
        self.assertEqual(a.Transport, MockTransport)
    
    def test_manager_entrypoint_failure(self):
        config = {
                'manager': 'immediate2',
                'transport': 'mock'
            }
        
        log.info("Testing configuration: %r", dict(config))
        self.assertRaises(LookupError, lambda: Delivery(config))
    
    def test_manager_dotcolon_failure(self):
        config = {
                'manager': 'marrow.mail.manager.foo:FooManager',
                'transport': 'mock'
            }
        
        log.info("Testing configuration: %r", dict(config))
        self.assertRaises(ImportError, lambda: Delivery(config))
        
        config['manager'] = 'marrow.mail.manager.immediate:FooManager'
        log.info("Testing configuration: %r", dict(config))
        self.assertRaises(AttributeError, lambda: Delivery(config))
    
    def test_transport_entrypoint_failure(self):
        config = {
                'manager': 'immediate',
                'transport': 'mock2'
            }
        
        log.info("Testing configuration: %r", dict(config))
        self.assertRaises(LookupError, lambda: Delivery(config))
    
    def test_transport_dotcolon_failure(self):
        config = {
                'manager': 'immediate',
                'transport': 'marrow.mail.transport.foo:FooTransport'
            }
        
        log.info("Testing configuration: %r", dict(config))
        self.assertRaises(ImportError, lambda: Delivery(config))
        
        config['manager'] = 'marrow.mail.transport.mock:FooTransport'
        log.info("Testing configuration: %r", dict(config))
        self.assertRaises(AttributeError, lambda: Delivery(config))


class TestMethods(TestCase):
    def test_startup(self):
        messages = logging.getLogger().handlers[0].buffer
        
        interface = Delivery(base_config)
        interface.start()
        
        self.assertEqual(len(messages), 4)
        self.assertEqual(messages[0].getMessage(), "Mail delivery service starting.")
        self.assertEqual(messages[-1].getMessage(), "Mail delivery service started.")
        
        interface.start()
        
        self.assertEqual(len(messages), 5)
        self.assertEqual(messages[-1].getMessage(), "Attempt made to start an already running delivery service.")
        
        interface.stop()
    
    def test_shutdown(self):
        interface = Delivery(base_config)
        interface.start()
        
        logging.getLogger().handlers[0].truncate()
        messages = logging.getLogger().handlers[0].buffer
        
        interface.stop()
        
        self.assertEqual(len(messages), 4)
        self.assertEqual(messages[0].getMessage(), "Mail delivery service stopping.")
        self.assertEqual(messages[-1].getMessage(), "Mail delivery service stopped.")
        
        interface.stop()
        
        self.assertEqual(len(messages), 5)
        self.assertEqual(messages[-1].getMessage(), "Attempt made to stop an already stopped delivery service.")
    
    def test_send(self):
        message = Bunch(id='foo')
        
        interface = Delivery(base_config)
        
        self.assertRaises(MailerNotRunning, lambda: interface.send(message))
        
        interface.start()
        
        logging.getLogger().handlers[0].truncate()
        messages = logging.getLogger().handlers[0].buffer
        
        self.assertEqual(interface.send(message), True)
        
        self.assertEqual(messages[0].getMessage(), "Attempting delivery of message foo.")
        self.assertEqual(messages[-1].getMessage(), "Message foo delivered.")
        
        message_fail = Bunch(id='bar', die=True)
        self.assertRaises(Exception, lambda: interface.send(message_fail))
        
        self.assertEqual(messages[-2].getMessage(), "Attempting delivery of message bar.")
        self.assertEqual(messages[-1].getMessage(), "Delivery of message bar failed.")
        
        interface.stop()
