#!/usr/bin/env python
# encoding: utf-8

import sys
import logging

from marrow.mailer import Message, Mailer


logging.basicConfig(level=logging.DEBUG)


configuration = {
        'manager.use': 'immediate', # futures
        'manager.workers': 5,
        
        'transport.use': 'smtp',
        'transport.host': 'secure.emailsrvr.com',
        'transport.tls': 'ssl', # None=='', required, optional
        'transport.port': 465, # 25, 465 = SSL
        'transport.username': 'amcgregor@gothcandy.com',
        'transport.password': 'eim1Ewe4was4',
        'transport.pipeline': 5,
        'transport.debug': False
    }


if __name__ == '__main__':
    mail = Mailer(configuration)
    mail.start()
    
    message = Message()
    message.author = [('Alice Bevan-McGregor', 'alice@gothcandy.com')]
    message.to = [('Your Name Here', 'alice.mcgregor@me.com')]
    message.subject = "This is a test message."
    message.plain = "Testing!"
    
    mail.send(message)
    mail.stop()
