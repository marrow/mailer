# encoding: utf-8

"""Exceptions used by marrow.mail to report common errors."""


__all__ = [
        'MailException',
        'MailConfigurationException',
        'TransportException',
        'TransportFailedException',
        'TransportExhaustedException',
        'ManagerException'
    ]



class MailException(Exception):
    """The base for all marrow.mail exceptions."""
    pass


class MailConfigurationException(MailException):
    """There was an error in the configuration of marrow.mail."""
    
    pass


class TransportException(MailException):
    """The base for all marrow.mail Transport exceptions."""
    
    pass


class TransportFailedException(TransportException):
    """The transport has failed to deliver the message due to an internal
    error; a new instance of the transport should be used to retry."""
    
    pass

class TransportExhaustedException(TransportException):
    """The transport has successfully delivered the message, but can no longer
    be used for message delivery."""
    
    pass


class ManagerException(MailException):
    """The base for all marrow.mail Manager exceptions."""
    pass
