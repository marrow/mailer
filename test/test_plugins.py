# encoding: utf-8

'''

from __future__ import unicode_literals

import logging
import pkg_resources

from unittest import TestCase
from nose.tools import ok_, eq_, raises
from nose.plugins.skip import Skip, SkipTest

from marrow.mailer.interfaces import IManager, ITransport


log = logging.getLogger('tests')



def test_managers():
    def closure(plugin):
        try:
            plug = plugin.load()
        except ImportError as e:
            raise SkipTest("Skipped {name} manager due to ImportError:\n{err}".format(name=plugin.name, err=str(e)))
        
        ok_(isinstance(plug, IManager), "{name} does not conform to the IManager API.".format(name=plugin.name))
    
    entrypoint = None
    for entrypoint in pkg_resources.iter_entry_points('marrow.mailer.manager', None):
        yield closure, entrypoint
    
    if entrypoint is None:
        raise SkipTest("No managers found, have you run `setup.py develop` yet?")


def test_transports():
    def closure(plugin):
        try:
            plug = plugin.load()
        except ImportError as e:
            raise SkipTest("Skipped {name} transport due to ImportError:\n{err}".format(name=plugin.name, err=str(e)))
        
        ok_(isinstance(plug, ITransport), "{name} does not conform to the ITransport API.".format(name=plugin.name))
    
    entrypoint = None
    for entrypoint in pkg_resources.iter_entry_points('marrow.mailer.transport', None):
        yield closure, entrypoint
    
    if entrypoint is None:
        raise SkipTest("No transports found, have you run `setup.py develop` yet?")

'''
