import logging
from marrow.mailer import Message, Mailer
logging.basicConfig(level=logging.INFO)

mail = Mailer({'manager.use': 'immediate', 'transport.use': 'mbox', 'transport.file': 'data/mbox'}).start()

message = Message(
		[('Alice Bevan-McGregor', 'alice@gothcandy.com')],
		[('Alice Two', 'alice.mcgregor@me.com')],
		"This is a test message.",
		plain="Testing!"
	)

mail.send(message)
mail.stop()
