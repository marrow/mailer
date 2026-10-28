# encoding: utf-8

"""Utilities for testing Marrow Mailer and applications that use it."""

from __future__ import print_function

import sys
import time
from threading import Thread
from socket import socket
from threading import Event, RLock
from datetime import datetime
from collections import namedtuple, deque
from email.parser import Parser

if sys.version_info < (3, 0):
	from smtpd import SMTPServer
	from asyncore import loop
else:
	# Python 3.12 removed smtpd and asyncore, and the smtpd based server below fails on earlier Python 3 releases as
	# well (Thread._stop is a method there, and smtpd passes mail_options and rcpt_options); use aiosmtpd instead.
	SMTPServer = loop = None

try:
	from pytest import fixture
except:  # We don't honestly care if pytest is installed.
	def fixture(*args, **kw):
		if len(args) == 1 and callable(args[0]) and not kw:
			return args[0]

		return lambda fn: fn


TestMessage = namedtuple('TestMessage', ('sender', 'recipients', 'time', 'message', 'raw'))


class _MessageStore(object):
	"""Message capture shared by the smtpd (Python 2) and aiosmtpd (Python 3) based servers."""

	def process_message(self, peer, sender, recipients, data):
		# We construct a helpful namedtuple with all of the relevant delivery details.
		message = TestMessage(sender, recipients, datetime.utcnow(), Parser().parsestr(data), data)

		with self._lock:  # Protect against parallel access.
			self.messages.append(message)

	def __getitem__(self, i):
		return self.messages.__getitem__(i)

	def __len__(self):
		return len(self.messages)

	def __iter__(self):
		return iter(self.messages)

	def drain(self):
		with self._lock:  # Protect against parallel access.
			self.messages.clear()

	def next(self):
		with self._lock:  # Protect against parallel access.
			return self.messages.popleft()


if SMTPServer is not None:
	class DebuggingSMTPServer(_MessageStore, SMTPServer, Thread):
		"""A generalized testing SMTP server that captures messages delivered to it."""

		POLL_TIMEOUT = 0.001

		def __init__(self, host='127.0.0.1', port=2526):
			# Initialize the SMTP component.
			# My face that asyncore doesn't use new style classes!
			SMTPServer.__init__(self, (host, port), None)

			# Retrieve the actually-bound socket address. May, in some circumstances, use a reverse DNS name.
			if self._localaddr[1] == 0:
				self.address = self.socket.getsockname()
			else:
				self.address = (host, port)

			# Create a place to store messages.
			self.messages = deque()

			# Setup threading.
			self._stop = Event()
			self._lock = RLock()
			Thread.__init__(self, name=self.__class__.__name__)

		@classmethod
		def main(cls):
			server = cls()

			print("Debugging SMTP server is running on ", server.address[0], ":", server.address[1], sep="")
			print("Press Control+C to stop.")

			try:
				loop()
			except KeyboardInterrupt:
				pass

		def run(self):
			while not self._stop.is_set():
				loop(timeout=self.POLL_TIMEOUT, count=1)

		def stop(self, timeout=None):
			self._stop.set()
			self.join(timeout)
			self.close()

else:
	class _Handler(object):
		"""aiosmtpd handler passing each delivered message to the server."""

		def __init__(self, server):
			self.server = server

		def handle_DATA(self, server, session, envelope):
			self.server.process_message(session.peer, envelope.mail_from, envelope.rcpt_tos, envelope.content)

			# aiosmtpd awaits the result; a completed future avoids async syntax, which Python 2 can't parse.
			result = server.loop.create_future()
			result.set_result('250 OK')
			return result


	class DebuggingSMTPServer(_MessageStore):
		"""A generalized testing SMTP server that captures messages delivered to it.

		On Python 3 this runs on aiosmtpd, which must be installed to create one.
		"""

		def __init__(self, host='127.0.0.1', port=2526):
			from aiosmtpd.controller import Controller

			if port == 0:  # aiosmtpd needs the actual port number up front.
				probe = socket()
				probe.bind((host, 0))
				port = probe.getsockname()[1]
				probe.close()

			self.address = (host, port)

			# Create a place to store messages.
			self.messages = deque()
			self._lock = RLock()

			self._controller = Controller(_Handler(self), hostname=host, port=port, decode_data=True)

		@classmethod
		def main(cls):
			server = cls()
			server.start()

			print("Debugging SMTP server is running on ", server.address[0], ":", server.address[1], sep="")
			print("Press Control+C to stop.")

			try:
				while True:
					time.sleep(1)
			except KeyboardInterrupt:
				pass
			finally:
				server.stop()

		def start(self):
			self._controller.start()

		def stop(self, timeout=None):
			self._controller.stop()



@fixture(scope='session')
def smtp(request):
	# TODO: Identify a random port number that is available.

	# Construct the debugging server instance.
	server = DebuggingSMTPServer()
	server.start()

	request.addfinalizer(server.stop)

	return server



if __name__ == '__main__':  # pragma: no cover
	DebuggingSMTPServer.main()
