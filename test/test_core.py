# encoding: utf-8

"""Test the primary configurator interface, Mailer."""

import logging
import warnings
import pytest

from unittest import TestCase

from marrow.mailer import Mailer, Delivery, Message
from marrow.mailer.exc import MailerNotRunning
from marrow.mailer.manager.immediate import ImmediateManager
from marrow.mailer.transport.mock import MockTransport

from marrow.util.bunch import Bunch

log = logging.getLogger('tests')

base_config = dict(manager=dict(use='immediate'), transport=dict(use='mock'))


class TestLookup(TestCase):
	def test_load_literal(self):
		assert Mailer._load(ImmediateManager, None) == ImmediateManager

	def test_load_dotcolon(self):
		assert Mailer._load('marrow.mailer.manager.immediate:ImmediateManager', None) == ImmediateManager

	def test_load_entrypoint(self):
		assert Mailer._load('immediate', 'marrow.mailer.manager') == ImmediateManager


class TestInitialization(TestCase):
	def test_deprecation(self):
		with warnings.catch_warnings(record=True) as w:
			warnings.simplefilter("always")

			Delivery(base_config)

			assert len(w) == 1, "No, or more than one, warning issued."
			assert issubclass(w[-1].category, DeprecationWarning), "Category of warning is not DeprecationWarning."
			assert 'deprecated' in str(w[-1].message), "Warning does not include 'deprecated'."
			assert 'Mailer' in str(w[-1].message), "Warning does not include correct class name."
			assert 'Delivery' in str(w[-1].message), "Warning does not include old class name."

	def test_default_manager(self):
		a = Mailer(dict(transport=dict(use='mock')))

		assert a.Manager == ImmediateManager
		assert a.Transport == MockTransport

	def test_standard(self):
		log.info("Testing configuration: %r", dict(base_config))
		a = Mailer(base_config)

		assert a.Manager == ImmediateManager
		assert a.Transport == MockTransport

	def test_bad_manager(self):
		config = dict(manager=dict(use=object()), transport=dict(use='mock'))
		log.info("Testing configuration: %r", dict(config))
		with pytest.raises(TypeError):
			Mailer(config)

	def test_bad_transport(self):
		config = dict(manager=dict(use='immediate'), transport=dict(use=object()))
		log.info("Testing configuration: %r", dict(config))
		with pytest.raises(TypeError):
			Mailer(config)

	def test_repr(self):
		a = Mailer(base_config)
		assert repr(a) == "Mailer(manager=ImmediateManager, transport=MockTransport)"

	def test_prefix(self):
		config = {
				'mail.manager.use': 'immediate',
				'mail.transport.use': 'mock'
			}

		log.info("Testing configuration: %r", dict(config))
		a = Mailer(config, 'mail')

		assert a.Manager == ImmediateManager
		assert a.Transport == MockTransport

	def test_deep_prefix(self):
		config = {
				'marrow.mailer.manager.use': 'immediate',
				'marrow.mailer.transport.use': 'mock'
			}

		log.info("Testing configuration: %r", dict(config))
		a = Mailer(config, 'marrow.mailer')

		assert a.Manager == ImmediateManager
		assert a.Transport == MockTransport

	def test_manager_entrypoint_failure(self):
		config = {
				'manager.use': 'immediate2',
				'transport.use': 'mock'
			}

		log.info("Testing configuration: %r", dict(config))
		with pytest.raises(LookupError):
			Mailer(config)

	def test_manager_dotcolon_failure(self):
		config = {
				'manager.use': 'marrow.mailer.manager.foo:FooManager',
				'transport.use': 'mock'
			}

		log.info("Testing configuration: %r", dict(config))
		with pytest.raises(ImportError):
			Mailer(config)

		config['manager.use'] = 'marrow.mailer.manager.immediate:FooManager'
		log.info("Testing configuration: %r", dict(config))
		with pytest.raises(AttributeError):
			Mailer(config)

	def test_transport_entrypoint_failure(self):
		config = {
				'manager.use': 'immediate',
				'transport.use': 'mock2'
			}

		log.info("Testing configuration: %r", dict(config))
		with pytest.raises(LookupError):
			Mailer(config)

	def test_transport_dotcolon_failure(self):
		config = {
				'manager.use': 'immediate',
				'transport.use': 'marrow.mailer.transport.foo:FooTransport'
			}

		log.info("Testing configuration: %r", dict(config))
		with pytest.raises(ImportError):
			Mailer(config)

		config['manager.use'] = 'marrow.mailer.transport.mock:FooTransport'
		log.info("Testing configuration: %r", dict(config))
		with pytest.raises(AttributeError):
			Mailer(config)


class TestMethods(TestCase):
	def test_startup(self):
		#messages = logging.getLogger().handlers[0].buffer

		interface = Mailer(base_config)
		interface.start()

		#assert len(messages) == 5
		#assert messages[0] == "Mail delivery service starting."
		#assert messages[-1] == "Mail delivery service started."

		interface.start()

		#assert len(messages) == 6
		#assert messages[-1] == "Attempt made to start an already running Mailer service."

		interface.stop()

	def test_shutdown(self):
		interface = Mailer(base_config)
		interface.start()

		#logging.getLogger().handlers[0].truncate()
		#messages = logging.getLogger().handlers[0].buffer

		interface.stop()

		#assert len(messages) == 5
		#assert messages[0] == "Mail delivery service stopping."
		#assert messages[-1] == "Mail delivery service stopped."

		interface.stop()

		#assert len(messages) == 6
		#assert messages[-1] == "Attempt made to stop an already stopped Mailer service."

	def test_send(self):
		message = Bunch(id='foo')

		interface = Mailer(base_config)

		with pytest.raises(MailerNotRunning):
			interface.send(message)

		interface.start()

		#logging.getLogger().handlers[0].truncate()
		#messages = logging.getLogger().handlers[0].buffer

		assert interface.send(message) == (message, True)

		#assert messages[0] == "Attempting delivery of message foo."
		#assert messages[-1] == "Message foo delivered."

		message_fail = Bunch(id='bar', die=True)
		
		with pytest.raises(Exception):
			interface.send(message_fail)

		#assert messages[-4] == "Attempting delivery of message bar."
		#assert messages[-3] == "Acquired existing transport instance."
		#assert messages[-2] == "Shutting down transport due to unhandled exception."
		#assert messages[-1] == "Delivery of message bar failed."

		interface.stop()

	def test_new(self):
		config = dict(
			manager=dict(use='immediate'), transport=dict(use='mock'),
			message=dict(author='from@example.com', retries=1, brand=False))
		
		interface = Mailer(config).start()
		message = interface.new(retries=2)
		
		assert message.author == ["from@example.com"]
		assert message.bcc == []
		assert message.retries == 2
		assert message.mailer is interface
		assert message.brand == False
		
		with pytest.raises(NotImplementedError):
			Message().send()
		
		assert message.send() == (message, True)

		message = interface.new("alternate@example.com", "recipient@example.com", "Test.")

		assert message.author == ["alternate@example.com"]
		assert message.to == ["recipient@example.com"]
		assert message.subject == "Test."
