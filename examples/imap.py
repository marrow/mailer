import logging
from marrow.mailer import Message, Mailer
logging.basicConfig(level=logging.DEBUG)

mail = Mailer({
        'manager.use': 'futures',
        'transport.use': 'imap',
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
