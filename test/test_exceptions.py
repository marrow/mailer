# encoding: utf-8

"""Test the primary configurator interface, Delivery."""

import logging

from unittest import TestCase
from nose.tools import ok_, eq_, raises

from marrow.mailer.exc import DeliveryFailedException


log = logging.getLogger('tests')



class TestDeliveryFailedException(TestCase):
    def test_init(self):
        exc = DeliveryFailedException("message", "reason")
        self.assertEquals(exc.msg, "message")
        self.assertEquals(exc.reason, "reason")
        self.assertEquals(exc.args[0], "message")
        self.assertEquals(exc.args[1], "reason")
