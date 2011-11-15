# encoding: utf-8

from __future__ import unicode_literals

import logging

from unittest import TestCase
from nose.tools import ok_, eq_, raises

from marrow.mailer import Delivery


log = logging.getLogger('tests')



def test_issue_2():
    mail = Delivery({
            'manager': 'immediate',
            'transport': 'smtp',
            'transport.host': 'secure.emailsrvr.com',
            'transport.tls': 'ssl'
        })
    
    mail.start()
    mail.stop()
