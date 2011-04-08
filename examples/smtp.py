import logging
from marrow.mailer import Message, Delivery
logging.basicConfig(level=logging.INFO)

mail = Delivery({
        'manager': 'futures',
        'transport': 'smtp',
        'transport.host': '',
        'transport.tls': 'ssl',
        'transport.username': '',
        'transport.password': '',
        'transport.max_messages_per_connection': 5
    })
mail.start()

message = Message([('Alice Bevan-McGregor', 'alice@gothcandy.com')], [('Alice Two', 'alice.mcgregor@me.com')], "This is a test message.", plain="Testing!")

mail.send(message)
mail.stop()
