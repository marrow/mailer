#!/usr/bin/env python
# encoding: utf-8

import sys
import logging

from marrow.mailer import Message, Mailer


logging.basicConfig(level=logging.INFO)


configuration = {
        'manager.use': 'immediate', # futures
        'manager.workers': 5,
        
        'transport.use': 'smtp',
        'transport.host': '',
        'transport.tls': 'ssl', # None=='', required, optional
        'transport.port': 465, # 25, 465 = SSL
        'transport.username': '',
        'transport.password': '',
        'transport.max_messages_per_connection': 5,
        'transport.debug': False
    }


if __name__ == '__main__':
    mail = Mailer(configuration)
    mail.start()
    
    message = Message()
    message.author = [('Alice Bevan-McGregor', 'alice@gothcandy.com')]
    message.to = [('Your Name Here', 'you@example.com')]
    message.subject = "This is a test message."
    message.plain = "Testing!"
    
    mail.send(message)
    mail.stop()
