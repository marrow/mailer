# encoding: utf-8

"""Test the primary configurator interface, Delivery."""

import logging

from unittest import TestCase

from marrow.mail import Delivery
from marrow.mail.manager.immediate import ImmediateManager



class TestLookup(TestCase):
    def test_load_literal(self):
        self.assertEqual(Delivery._load(ImmediateManager, None), ImmediateManager)
    
    def test_load_dotcolon(self):
        self.assertEqual(Delivery._load('marrow.mail.manager.immediate:ImmediateManager', None), ImmediateManager)
    
    def test_load_entrypoint(self):
        self.assertEqual(Delivery._load('immediate', 'marrow.mailer.manager'), ImmediateManager)
    # 
    # def test_load_literal(self):
    #     self.assertEqual(Delivery._load(ImmediateManager, 'manager'), ImmediateManager)
