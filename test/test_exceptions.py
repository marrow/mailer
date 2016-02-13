# encoding: utf-8

"""Test the primary configurator interface, Delivery."""

from unittest import TestCase

from marrow.mailer.exc import DeliveryFailedException


def test_delivery_failed_exception_init():
	exc = DeliveryFailedException("message", "reason")
	assert exc.msg == "message"
	assert exc.reason == "reason"
	assert exc.args[0] == "message"
	assert exc.args[1] == "reason"
