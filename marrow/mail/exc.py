# encoding: utf-8

"""Exceptions used by marrow.mail to report common errors."""


__all__ = [
        'MailException',
        'MailConfigurationException',
        'TransportException',
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


class TransportExhaustedException(TransportException):
    """"""
    
    def __str__(self):
        return "This Transport instance is no longer capable of delivering mail."


class ManagerException(MailException):
    """The base for all marrow.mail Manager exceptions."""
    pass
