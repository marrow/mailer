# encoding: utf-8

from __future__ import unicode_literals

import logging
import pkg_resources

from functools import partial
from unittest import TestCase
from nose.tools import ok_, eq_, raises
from nose.plugins.skip import Skip, SkipTest

from marrow.mailer.exc import TransportExhaustedException, TransportFailedException, DeliveryFailedException, MessageFailedException
from marrow.mailer.manager.dynamic import DynamicManager, WorkItem


log = logging.getLogger('tests')



class MockFuture(object):
    def __init__(self):
        self.cancelled = False
        self.running = False
        self.exception = None
        self.result = None
        
        super(MockFuture, self).__init__()
    
    def set_running_or_notify_cancel(self):
        if self.cancelled:
            return False
        
        self.running = True
        return True
    
    def set_exception(self, e):
        self.exception = e
    
    def set_result(self, r):
        self.result = r


class TestWorkItem(TestCase):
    calls = list()
    
    def closure(self):
        self.calls.append(True)
        return True
    
    def setUp(self):
        self.f = MockFuture()
        self.wi = WorkItem(self.f, self.closure, (), {})
        
    def test_success(self):
        self.wi.run()
        
        self.assertEquals(self.calls, [True])
        self.assertTrue(self.f.result)
    
    def test_cancelled(self):
        self.f.cancelled = True
        self.wi.run()
        
        self.assertEquals(self.calls, [])
    
    def test_exception(self):
        self.wi.fn = lambda: 1/0
        self.wi.run()
        
        self.assertTrue(isinstance(self.f.exception, ZeroDivisionError))


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
        self.manager = self.manager(self.config, partial(self.MockTransport, self.states, self.messages))
    
    def tearDown(self):
        del self.states[:]
        del self.messages[:]


class TestDynamicManager(ManagerTestCase):
    manager = DynamicManager
    
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
        
        receipt = self.manager.deliver(exc)
        self.assertRaises(DeliveryFailedException, receipt.result)
        
        self.assertEquals(self.states, ['running', 'stopped'])
        self.assertEquals(self.messages, [exc])
        
        self.manager.shutdown()
        self.assertEquals(self.states, ['running', 'stopped'])
    
    def test_transport_failure(self):
        self.manager.startup()
        
        exc = TransportFailedException()
        
        self.manager.deliver(exc).result()
        
        self.assertEquals(self.states, ['running', 'stopped', 'running'])
        self.assertEquals(self.messages, [exc, exc])
        
        self.manager.shutdown()
        self.assertEquals(self.states, ['running', 'stopped', 'running', 'stopped'])
    
    def test_transport_exhaustion(self):
        self.manager.startup()
        
        exc = TransportExhaustedException()
        
        self.manager.deliver(exc).result()
        
        self.assertEquals(self.states, ['running', 'stopped'])
        self.assertEquals(self.messages, [exc])
        
        self.manager.shutdown()
        self.assertEquals(self.states, ['running', 'stopped'])
