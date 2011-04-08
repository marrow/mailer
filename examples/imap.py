import logging
from marrow.mailer import Message, Delivery
logging.basicConfig(level=logging.DEBUG)

mail = Delivery({
        'manager': 'futures',
        'transport': 'imap',
        'transport.host': '',
        'transport.ssl': True,
        'transport.username': '',
        'transport.password': '',
        'transport.folder': 'Marrow'
    })

mail.start()

message = Message([('Alice Bevan-McGregor', 'alice@gothcandy.com')], [('Alice Two', 'alice.mcgregor@me.com')], "This is a test message.", plain="Testing!")

mail.send(message)
mail.stop()
