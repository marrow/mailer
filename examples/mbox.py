import logging
from marrow.mailer import Message, Delivery
logging.basicConfig(level=logging.INFO)

mail = Delivery({'manager': 'immediate', 'transport': 'mbox', 'transport.file': 'data/mbox'})
mail.start()

message = Message([('Alice Bevan-McGregor', 'alice@gothcandy.com')], [('Alice Two', 'alice.mcgregor@me.com')], "This is a test message.", plain="Testing!")

mail.send(message)
mail.stop()

