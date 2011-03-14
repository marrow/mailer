# encoding: utf-8

""""""


import logging
import warnings
import pkg_resources

from marrow.util.bunch import Bunch
from marrow.util.object import load_object


__all__ = ['Delivery']

log = __import__('logging').getLogger(__name__)


class Delivery(object):
    """The primary marrow.mail interface.
    
    Instantiate and configure marrow.mail, then use the instance to initiate mail delivery.
    
    Where managers and transports are defined in the configuration you may pass in the class,
    an entrypoint name (simple string), or package-object notation ('foo.bar:baz').
    """
    
    def __init__(self, config, prefix=None):
        self.manager, self.Manager = None, None
        self.Transport = None
        self.running = False
        config = self.config = Bunch(config)
        
        if prefix is not None:
            for chunk in prefix.split('.'):
                config = self.config = Bunch.partial(chunk, self.config)
        
        manager_config = Bunch.partial('manager', self.config)
        transport_config = Bunch.partial('transport', self.config)
        
        self.Manager = self._load(config.manager, 'marrow.mail.manager')
        
        if not self.Manager:
            raise LookupError("Unable to determine manager from specification: %r" % (config.manager, ))
        
        self.Transport = self.transport = self._load(config.transport, 'marrow.mail.transport')
        
        if not self.Transport:
            raise LookupError("Unable to determine transport from specification: %r" % (config.manager, ))
        
        self.manager = self.Manager(manager_config, self.Transport, transport_config)
    
    def _load(self, spec, group):
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
        
        self.manager.stop()
        self.running = False
        
        log.info("Mail delivery service stopped.")
    
    def send(self, message):
        if not self.running:
            raise Exception("Mail service not running.") # TODO: Need concrete exceptions of our own.
        
        return self.manager.deliver(message)
