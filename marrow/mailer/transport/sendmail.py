# encoding: utf-8

import os

from marrow.mailer.exc import MessageFailedException


__all__ = ['SendmailTransport']

log = __import__('logging').getLogger(__name__)



class SendmailTransport(object): # pragma: no cover
    __slots__ = ('ephemeral', 'executable')
    
    def __init__(self, config):
        self.executable = config.get('path', '/usr/sbin/sendmail')
    
    def startup(self):
        pass
    
    def deliver(self, message):
        # TODO: Utilize -F full_name (sender full name), -f sender (envelope sender), -V envid (envelope ID), and space-separated BCC recipients
        # TODO: Record the output of STDOUT and STDERR to capture errors.
        proc = os.popen('%s -t -i' % (self.executable, ), 'w')
        proc.write(bytes(message))
        status = proc.close()
        
        if status != 0:
            raise MessageFailedException("Status code %d." % (status, ))
    
    def shutdown(self):
        pass
