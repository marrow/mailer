# encoding: utf-8

import random

from marrow.mailer.exc import TransportFailedException, TransportExhaustedException

from marrow.util.bunch import Bunch


__all__ = ['MockTransport']

log = __import__('logging').getLogger(__name__)



class MockTransport(object):
    """A no-op dummy transport.
    
    Accepts two configuration directives:
    
     * success - probability of successful delivery
     * failure - probability of failure
     * exhaustion - probability of exhaustion
    
    All are represented as percentages between 0.0 and 1.0, inclusive.
    (Setting failure or exhaustion to 1.0 means every delivery will fail
    badly; do not do this except under controlled, unit testing scenarios!)
    """
    
    __slots__ = ('ephemeral', 'config')
    
    def __init__(self, config):
        base = {'success': 1.0, 'failure': 0.0, 'exhaustion': 0.0}
        base.update(dict(config))
        self.config = Bunch(base)
    
    def startup(self):
        pass
    
    def deliver(self, message):
        """Concrete message delivery."""
        
        config = self.config
        success = config.success
        failure = config.failure
        exhaustion = config.exhaustion
        
        if getattr(message, 'die', False):
            1/0
        
        if failure:
            chance = random.randint(0,100001) / 100000.0
            if chance < failure:
                raise TransportFailedException("Mock failure.")
        
        if exhaustion:
            chance = random.randint(0,100001) / 100000.0
            if chance < exhaustion:
                raise TransportExhaustedException("Mock exhaustion.")
        
        if success == 1.0:
            return True
        
        chance = random.randint(0,100001) / 100000.0
        if chance <= success:
            return True
        
        return False
    
    def shutdown(self):
        pass
