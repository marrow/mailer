# encoding: utf-8

from __future__ import unicode_literals

import logging
import pkg_resources

from functools import partial
from unittest import TestCase
from nose.tools import ok_, eq_, raises
from nose.plugins.skip import Skip, SkipTest

from marrow.mailer.exc import TransportExhaustedException, TransportFailedException, DeliveryFailedException, MessageFailedException
from marrow.mailer.manager.immediate import ImmediateManager


log = logging.getLogger('tests')



class ManagerTestCase(TestCase):
    manager = None
    config = dict()
    states = []
    messages = []
    
    class MockTransport(object):
        def __init__(self, states, messages):
            self.ephemeral = False
            self.states = states
            self.messages = messages
        
        def startup(self):
            self.states.append('running')
        
        def deliver(self, message):
            self.messages.append(message)
            
            if isinstance(message, Exception) and ( len(self.messages) < 2 or self.messages[-2] is not message):
                raise message
        
        def shutdown(self):
            self.states.append('stopped')
    
    def setUp(self):
        self.manager = ImmediateManager(self.config, partial(self.MockTransport, self.states, self.messages))
    
    def tearDown(self):
        del self.states[:]
        del self.messages[:]


class TestImmediateManager(ManagerTestCase):
    manager = ImmediateManager
    
    def test_startup(self):
        # TODO: Test logging messages.
        self.manager.startup()
        self.assertEquals(self.states, [])
    
    def test_shutdown(self):
        # TODO: Test logging messages.
        self.manager.startup()
        self.manager.shutdown()
        self.assertEquals(self.states, [])
    
    def test_success(self):
        self.manager.startup()
        
        self.manager.deliver("success")
        
        self.assertEquals(self.states, ["running"])
        self.assertEquals(self.messages, ["success"])
        
        self.manager.shutdown()
        self.assertEquals(self.states, ["running", "stopped"])
    
    def test_message_failure(self):
        self.manager.startup()
        
        exc = MessageFailedException()
        
        self.assertRaises(DeliveryFailedException, self.manager.deliver, exc)
        
        self.assertEquals(self.states, ['running', 'stopped'])
        self.assertEquals(self.messages, [exc])
        
        self.manager.shutdown()
        self.assertEquals(self.states, ['running', 'stopped'])
    
    def test_transport_failure(self):
        self.manager.startup()
        
        exc = TransportFailedException()
        
        self.manager.deliver(exc)
        
        self.assertEquals(self.states, ['running', 'stopped', 'running'])
        self.assertEquals(self.messages, [exc, exc])
        
        self.manager.shutdown()
        self.assertEquals(self.states, ['running', 'stopped', 'running', 'stopped'])
    
    def test_transport_exhaustion(self):
        self.manager.startup()
        
        exc = TransportExhaustedException()
        
        self.manager.deliver(exc)
        
        self.assertEquals(self.states, ['running', 'stopped'])
        self.assertEquals(self.messages, [exc])
        
        self.manager.shutdown()
        self.assertEquals(self.states, ['running', 'stopped'])
