# encoding: utf-8

"""Exceptions used by marrow.mailer to report common errors."""


__all__ = [
        'MailException',
        'MailConfigurationException',
        'TransportException',
        'TransportFailedException',
        'MessageFailedException',
        'TransportExhaustedException',
        'ManagerException'
    ]



class MailException(Exception):
    """The base for all marrow.mailer exceptions."""
    
    pass


# Application Exceptions

class DeliveryException(MailException):
    """The base class for all public-facing exceptions."""
    
    pass


class DeliveryFailedException(DeliveryException):
    """The message stored in args[0] could not be delivered for the reason
    given in args[1].  (These can be accessed as e.msg and e.reason.)"""
    
    def __init__(self, message, reason):
        self.msg = message
        self.reason = reason
        
        super(DeliveryFailedException, self).__init__(message, reason)


# Internal Exceptions

class MailerNotRunning(MailException):
    """Raised when attempting to deliver messages using a dead interface."""
    
    pass


class MailConfigurationException(MailException):
    """There was an error in the configuration of marrow.mailer."""
    
    pass


class TransportException(MailException):
    """The base for all marrow.mailer Transport exceptions."""
    
    pass


class TransportFailedException(TransportException):
    """The transport has failed to deliver the message due to an internal
    error; a new instance of the transport should be used to retry."""
    
    pass


class MessageFailedException(TransportException):
    """The transport has failed to deliver the message due to a problem with
    the message itself, and no attempt should be made to retry delivery of
    this message.  The transport may still be re-used, however.
    
    The reason for the failure should be the first argument.
    """
    
    pass


class TransportExhaustedException(TransportException):
    """The transport has successfully delivered the message, but can no longer
    be used for future message delivery; a new instance should be used on the
    next request."""
    
    pass


class ManagerException(MailException):
    """The base for all marrow.mailer Manager exceptions."""
    pass
