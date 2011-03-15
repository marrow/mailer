# encoding: utf-8

"""Test the primary configurator interface, Delivery."""

import logging

from unittest import TestCase

from marrow.mail import Delivery
from marrow.mail.manager.immediate import ImmediateManager
from marrow.mail.transport.mock import MockTransport


log = logging.getLogger('tests')



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
    
    def test_transport_failure(self):
        pass
