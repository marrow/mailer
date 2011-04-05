# encoding: utf-8

import imaplib

from datetime import datetime


__all__ = ['IMAPTransport']

log = __import__('logging').getLogger(__name__)



class IMAPTransport(object):
    def __init__(self, config):
        self.host = config.get('host', None)
        self.ssl = config.get('ssl', False)
        self.port = config.get('port', 993 if self.ssl else 143)
        self.username = config.get('username', None)
        self.password = config.get('password', None)
        self.folder = config.get('folder', "INBOX")
    
    def startup(self):
        Protocol = imaplib.IMAP4_SSL if self.ssl else imaplib.IMAP4
        self.connection = Protocol(self.host, self.port)
        
        if self.username:
            result = self.connection.login(self.username, self.password)
            log.debug("Response: %r", result)
    
    def __call__(self, message):
        self.connection.append(self.folder, '', message.date if message.date else datetime.now(), bytes(message))
    
    def shutdown(self):
        self.connection.logout()
