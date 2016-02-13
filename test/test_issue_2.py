# encoding: utf-8

from __future__ import unicode_literals

from marrow.mailer import Mailer



def test_issue_2():
    mail = Mailer({
            'manager.use': 'immediate',
            'transport.use': 'smtp',
            'transport.host': 'secure.emailsrvr.com',
            'transport.tls': 'ssl'
        })
    
    mail.start()
    mail.stop()
