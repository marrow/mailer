# encoding: utf-8

"""Deliver messages using (E)SMTP."""

from smtplib import (SMTP, SMTP_SSL, SMTPException, SMTPRecipientsRefused,
                     SMTPSenderRefused, SMTPServerDisconnected)
import socket
import sys

from marrow.mailer.exc import (MailConfigurationException,
    TransportExhaustedException, TransportException, TransportFailedException)


log = __import__('logging').getLogger(__name__)



class SMTPTransport(object):
    """An (E)SMTP pipelining transport."""
    
    def __init__(self, config):
        if not 'host' in config:
            raise MailConfigurationException('No server configured for SMTP')
        
        self.host = config.get('host', None)
        self.tls = config.get('tls', 'optional')
        self.certfile = config.get('certfile', None)
        self.keyfile = config.get('keyfile', None)
        self.port = config.get('port', 465 if self.tls == 'ssl' else 25)
        self.local_hostname = config.get('local_hostname', None)
        self.username = config.get('username', None)
        self.password = config.get('password', None)
        self.timeout = config.get('timeout', None)
        self.debug = config.get('debug', False)
        
        self.pipeline = config.get('pipeline', None)
        
        self.connection = None
        self.sent = 0
    
    def startup(self):
        if not self.connected:
            self.connect_to_server()
    
    def shutdown(self):
        if self.connected:
            log.debug("Closing SMTP connection")
            
            try:
                try:
                    self.connection.quit()
                
                except SMTPServerDisconnected:
                    pass
                
                except (SMTPException, socket.error):
                    log.exception("Unhandled error while closing connection.")
            
            finally:
                self.connection = None
    
    def connect_to_server(self):
        if self.tls == 'ssl':
            connection = SMTP_SSL(self.host, self.port, self.local_hostname,
                                  self.keyfile, self.certfile, self.timeout)
        else:
            connection = SMTP(self.host, self.port, self.local_hostname,
                              self.timeout)

        log.info("Connecting to SMTP server %s:%s", self.host, self.port)
        connection.set_debuglevel(self.debug)
        connection.connect(self.host, self.port)

        # Do TLS handshake if configured
        connection.ehlo()
        if self.tls in ('required', 'optional'):
            if connection.has_extn('STARTTLS'):
                connection.starttls(self.keyfile, self.certfile)
            elif self.tls == 'required':
                raise TransportException('TLS is required but not available on the server -- aborting')

        # Authenticate to server if necessary
        if self.username and self.password:
            log.info("Authenticating as %s", self.username)
            connection.login(self.username, self.password)

        self.connection = connection
    
    @property
    def connected(self):
        return getattr(self.connection, 'sock', None) is not None

    def deliver(self, message):
        if not self.connected:
            self.connect_to_server()
        
        try:
            self.send_with_smtp(message)
        
        finally:
            if self.pipeline is True:
                return
            
            if not self.pipeline or self.sent >= self.pipeline:
                raise TransportExhaustedException()
    
    def send_with_smtp(self, message):
        try:
            sender = bytes(message.envelope)
            recipients = message.recipients.string_addresses
            self.sent += 1
            self.connection.sendmail(sender, recipients, bytes(message))
        
        except SMTPSenderRefused:
            # The envelope sender was refused.  This is bad.
            e = sys.exc_info()[1]
            log.error("%s REFUSED %s %s", message.id, e.__class__.__name__, e)
            raise TransportFailedException()
        
        except SMTPRecipientsRefused:
            # All recipients were refused. Log which recipients.
            # This allows you to automatically parse your logs for bad e-mail addresses.
            e = sys.exc_info()[1]
            log.warning("%s REFUSED %s %s", message.id, e.__class__.__name__, e)
            raise TransportFailedException()
        
        except SMTPServerDisconnected:
            raise TransportExhaustedException()
        
        except:
            e = sys.exc_info()[1]
            cls_name = e.__class__.__name__
            log.debug("%s EXCEPTION %s", message.id, cls_name, exc_info=True)
            
            if message.retries >= 0:
                log.warning("%s DEFERRED %s", message.id, cls_name)
                message.retries -= 1
            
            else:
                log.exception("%s REFUSED %s", message.id, cls_name)
                raise TransportFailedException
