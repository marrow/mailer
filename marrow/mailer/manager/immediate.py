# encoding: utf-8

from marrow.mailer.exc import TransportExhaustedException, TransportFailedException, DeliveryFailedException, MessageFailedException
from marrow.mailer.manager.util import TransportPool


__all__ = ['ImmediateManager']

log = __import__('logging').getLogger(__name__)



class ImmediateManager(object):
    __slots__ = ('transport', )
    
    def __init__(self, config, Transport):
        """Initialize the immediate delivery manager."""
        
        # Create a transport pool; this will encapsulate the recycling logic.
        self.transport = TransportPool(Transport)
        
        super(ImmediateManager, self).__init__()
    
    def startup(self):
        """Perform startup actions.
        
        This just chains down to the transport layer.
        """
        
        log.info("Immediate delivery manager starting.")
        
        log.debug("Initializing transport queue.")
        self.transport.startup()
        
        log.info("Immediate delivery manager started.")
    
    def deliver(self, message):
        result = None
        
        while True:
            with self.transport() as transport:
                try:
                    result = transport.deliver(message)
                
                except MessageFailedException as e:
                    raise DeliveryFailedException(message, e.args[0] if e.args else "No reason given.")
                
                except TransportFailedException:
                    # The transport has suffered an internal error or has otherwise
                    # requested to not be recycled. Delivery should be attempted
                    # again.
                    transport.ephemeral = True
                    continue
                
                except TransportExhaustedException:
                    # The transport sent the message, but pre-emptively
                    # informed us that future attempts will not be successful.
                    transport.ephemeral = True
            
            break
        
        return message, result
    
    def shutdown(self):
        log.info("Immediate delivery manager stopping.")
        
        log.debug("Draining transport queue.")
        self.transport.shutdown()
        
        log.info("Immediate delivery manager stopped.")
