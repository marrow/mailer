"""Disabled for now as the "interfaces" module has been removed.

import logging
import pkg_resources
import pytest

from unittest import TestCase

from marrow.mailer.interfaces import IManager, ITransport


log = logging.getLogger('tests')



def test_managers():
	def closure(plugin):
		try:
			plug = plugin.load()
		except ImportError as e:
			pytest.skip(f"Skipped {plugin.name} manager due to ImportError:\n{e!s}")
		
		assert isinstance(plug, IManager), f"{plugin.name} does not conform to the IManager API."
	
	entrypoint = None
	for entrypoint in pkg_resources.iter_entry_points('marrow.mailer.manager', None):
		yield closure, entrypoint
	
	if entrypoint is None:
		pytest.skip("No managers found, have you run `setup.py develop` yet?")


def test_transports():
	def closure(plugin):
		try:
			plug = plugin.load()
		except ImportError as e:
			pytest.skip("Skipped {plugin.name} transport due to ImportError:\n{e!s}")
		
		assert isinstance(plug, ITransport), f"{plugin.name} does not conform to the ITransport API."
	
	entrypoint = None
	for entrypoint in pkg_resources.iter_entry_points('marrow.mailer.transport', None):
		yield closure, entrypoint
	
	if entrypoint is None:
		pytest.skip("No transports found, have you run `setup.py develop` yet?")
"""
