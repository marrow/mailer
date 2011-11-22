# encoding: utf-8

"""Test the primary configurator interface, Mailer."""

import logging
import warnings

from unittest import TestCase

from marrow.mailer import Mailer, Delivery
from marrow.mailer.exc import MailerNotRunning
from marrow.mailer.manager.immediate import ImmediateManager
from marrow.mailer.transport.mock import MockTransport

from marrow.util.bunch import Bunch


log = logging.getLogger('tests')


base_config = dict(manager=dict(use='immediate'), transport=dict(use='mock'))



class TestLookup(TestCase):
    def test_load_literal(self):
        self.assertEqual(Mailer._load(ImmediateManager, None), ImmediateManager)
    
    def test_load_dotcolon(self):
        self.assertEqual(Mailer._load('marrow.mailer.manager.immediate:ImmediateManager', None), ImmediateManager)
    
    def test_load_entrypoint(self):
        self.assertEqual(Mailer._load('immediate', 'marrow.mailer.manager'), ImmediateManager)


class TestInitialization(TestCase):
    def test_deprecation(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            Delivery(base_config)
            
            self.assertEqual(len(w), 1, "No, or more than one, warning issued.")
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning), "Category of warning is not DeprecationWarning.")
            self.assertIn('deprecated', str(w[-1].message), "Warning does not include 'deprecated'.")
            self.assertIn('Mailer', str(w[-1].message), "Warning does not include correct class name.")
            self.assertIn('Delivery', str(w[-1].message), "Warning does not include old class name.")
    
    def test_use_deprecation(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            Mailer(dict(manager='immediate', transport='mock'))
            
            self.assertEqual(len(w), 2, "Too few or too many warnings issued.")
            
            self.assertTrue(issubclass(w[0].category, DeprecationWarning), "Category of warning is not DeprecationWarning.")
            self.assertIn('deprecated', str(w[0].message), "Warning does not include 'deprecated'.")
            self.assertIn('manager.use', str(w[0].message), "Warning does not include correct use.")
            
            self.assertTrue(issubclass(w[1].category, DeprecationWarning), "Category of warning is not DeprecationWarning.")
            self.assertIn('deprecated', str(w[1].message), "Warning does not include 'deprecated'.")
            self.assertIn('transport.use', str(w[1].message), "Warning does not include correct use.")
    
    def test_standard(self):
        log.info("Testing configuration: %r", dict(base_config))
        a = Mailer(base_config)
        
        self.assertEqual(a.Manager, ImmediateManager)
        self.assertEqual(a.Transport, MockTransport)
    
    def test_bad_manager(self):
        config = dict(manager=dict(use=object()), transport=dict(use='mock'))
        log.info("Testing configuration: %r", dict(config))
        self.assertRaises(TypeError, Mailer, config)
    
    def test_bad_transport(self):
        config = dict(manager=dict(use='immediate'), transport=dict(use=object()))
        log.info("Testing configuration: %r", dict(config))
        self.assertRaises(TypeError, Mailer, config)
    
    def test_repr(self):
        a = Mailer(base_config)
        self.assertEqual(repr(a), "Mailer(manager=ImmediateManager, transport=MockTransport)")
    
    def test_prefix(self):
        config = {
                'mail.manager.use': 'immediate',
                'mail.transport.use': 'mock'
            }
        
        log.info("Testing configuration: %r", dict(config))
        a = Mailer(config, 'mail')
        
        self.assertEqual(a.Manager, ImmediateManager)
        self.assertEqual(a.Transport, MockTransport)
    
    def test_deep_prefix(self):
        config = {
                'marrow.mailer.manager.use': 'immediate',
                'marrow.mailer.transport.use': 'mock'
            }
        
        log.info("Testing configuration: %r", dict(config))
        a = Mailer(config, 'marrow.mailer')
        
        self.assertEqual(a.Manager, ImmediateManager)
        self.assertEqual(a.Transport, MockTransport)
    
    def test_manager_entrypoint_failure(self):
        config = {
                'manager.use': 'immediate2',
                'transport.use': 'mock'
            }
        
        log.info("Testing configuration: %r", dict(config))
        self.assertRaises(LookupError, Mailer, config)
    
    def test_manager_dotcolon_failure(self):
        config = {
                'manager.use': 'marrow.mailer.manager.foo:FooManager',
                'transport.use': 'mock'
            }
        
        log.info("Testing configuration: %r", dict(config))
        self.assertRaises(ImportError, Mailer, config)
        
        config['manager.use'] = 'marrow.mailer.manager.immediate:FooManager'
        log.info("Testing configuration: %r", dict(config))
        self.assertRaises(AttributeError, Mailer, config)
    
    def test_transport_entrypoint_failure(self):
        config = {
                'manager.use': 'immediate',
                'transport.use': 'mock2'
            }
        
        log.info("Testing configuration: %r", dict(config))
        self.assertRaises(LookupError, Mailer, config)
    
    def test_transport_dotcolon_failure(self):
        config = {
                'manager.use': 'immediate',
                'transport.use': 'marrow.mailer.transport.foo:FooTransport'
            }
        
        log.info("Testing configuration: %r", dict(config))
        self.assertRaises(ImportError, Mailer, config)
        
        config['manager.use'] = 'marrow.mailer.transport.mock:FooTransport'
        log.info("Testing configuration: %r", dict(config))
        self.assertRaises(AttributeError, Mailer, config)


class TestMethods(TestCase):
    def test_startup(self):
        messages = logging.getLogger().handlers[0].buffer
        
        interface = Mailer(base_config)
        interface.start()
        
        self.assertEqual(len(messages), 5)
        self.assertEqual(messages[0].getMessage(), "Mail delivery service starting.")
        self.assertEqual(messages[-1].getMessage(), "Mail delivery service started.")
        
        interface.start()
        
        self.assertEqual(len(messages), 6)
        self.assertEqual(messages[-1].getMessage(), "Attempt made to start an already running Mailer service.")
        
        interface.stop()
    
    def test_shutdown(self):
        interface = Mailer(base_config)
        interface.start()
        
        logging.getLogger().handlers[0].truncate()
        messages = logging.getLogger().handlers[0].buffer
        
        interface.stop()
        
        self.assertEqual(len(messages), 5)
        self.assertEqual(messages[0].getMessage(), "Mail delivery service stopping.")
        self.assertEqual(messages[-1].getMessage(), "Mail delivery service stopped.")
        
        interface.stop()
        
        self.assertEqual(len(messages), 6)
        self.assertEqual(messages[-1].getMessage(), "Attempt made to stop an already stopped Mailer service.")
    
    def test_send(self):
        message = Bunch(id='foo')
        
        interface = Mailer(base_config)
        
        self.assertRaises(MailerNotRunning, interface.send, message)
        
        interface.start()
        
        logging.getLogger().handlers[0].truncate()
        messages = logging.getLogger().handlers[0].buffer
        
        self.assertEqual(interface.send(message), (message, True))
        
        self.assertEqual(messages[0].getMessage(), "Attempting delivery of message foo.")
        self.assertEqual(messages[-1].getMessage(), "Message foo delivered.")
        
        message_fail = Bunch(id='bar', die=True)
        self.assertRaises(Exception, interface.send, message_fail)
        
        print [i.getMessage() for i in messages]
        
        self.assertEqual(messages[-4].getMessage(), "Attempting delivery of message bar.")
        self.assertEqual(messages[-3].getMessage(), "Acquired existing transport instance.")
        self.assertEqual(messages[-2].getMessage(), "Shutting down transport due to unhandled exception.")
        self.assertEqual(messages[-1].getMessage(), "Delivery of message bar failed.")
        
        interface.stop()
