# encoding: utf-8

from __future__ import unicode_literals

import logging

from unittest import TestCase
from nose.tools import ok_, eq_, raises

from marrow.mailer import Mailer


log = logging.getLogger('tests')



def test_issue_2():
	mail = Mailer({
			'manager.use': 'immediate',
			'transport.use': 'smtp',
			'transport.host': 'secure.emailsrvr.com',
			'transport.tls': 'ssl'
		})
	
	mail.start()
	mail.stop()
