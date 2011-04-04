# encoding: utf-8

"""marrow.mailer mail delivery framework and MIME message abstraction."""


import logging
import warnings
import pkg_resources

from functools import partial

from marrow.mailer.message import Message
from marrow.mailer.exc import MailerNotRunning

from marrow.util.bunch import Bunch
from marrow.util.object import load_object


__all__ = ['Delivery', 'Message']

log = __import__('logging').getLogger(__name__)


class Delivery(object):
    """The primary marrow.mailer interface.
    
    Instantiate and configure marrow.mailer, then use the instance to initiate mail delivery.
    
    Where managers and transports are defined in the configuration you may pass in the class,
    an entrypoint name (simple string), or package-object notation ('foo.bar:baz').
    """
    
    def __repr__(self):
        return "Delivery(manager=%s, transport=%s)" % (self.Manager.__name__, self.Transport.__name__)
    
    def __init__(self, config, prefix=None):
        self.manager, self.Manager = None, None
        self.Transport = None
        self.running = False
        self.config = config = Bunch(config)
        
        if prefix is not None:
            self.config = config = Bunch.partial(prefix, config)
        
        self.manager_config = manager_config = Bunch.partial('manager', config)
        self.transport_config = transport_config = Bunch.partial('transport', config)
        self.message_config = Bunch.partial('message', config)
        
        self.Manager = Manager = self._load(config.manager, 'marrow.mailer.manager')
        
        if not Manager:
            raise LookupError("Unable to determine manager from specification: %r" % (config.manager, ))
        
        self.Transport = Transport = self._load(config.transport, 'marrow.mailer.transport')
        
        if not Transport:
            raise LookupError("Unable to determine transport from specification: %r" % (config.transport, ))
        
        self.manager = Manager(manager_config, partial(Transport, transport_config))
    
    @staticmethod
    def _load(spec, group):
        if not isinstance(spec, str):
            # It's already an object, just use it.
            return spec
        
        if ':' in spec:
            # Load the Python package(s) and target object.
            return load_object(spec)
        
        # Load the entry point.
        for entrypoint in pkg_resources.iter_entry_points(group, spec):
            return entrypoint.load()
    
    def start(self):
        if self.running:
            log.warning("Attempt made to start an already running delivery service.")
            return
        
        log.info("Mail delivery service starting.")
        
        self.manager.startup()
        self.running = True
        
        log.info("Mail delivery service started.")
    
    def stop(self):
        if not self.running:
            log.warning("Attempt made to stop an already stopped delivery service.")
            return
        
        log.info("Mail delivery service stopping.")
        
        self.manager.shutdown()
        self.running = False
        
        log.info("Mail delivery service stopped.")
    
    def send(self, message):
        if not self.running:
            raise MailerNotRunning("Mail service not running.")
        
        log.info("Attempting delivery of message %s.", message.id)
        
        try:
            result = self.manager.deliver(message)
        
        except:
            log.error("Delivery of message %s failed.", message.id)
            raise
        
        log.debug("Message %s delivered.", message.id)
        return result
