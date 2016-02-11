# encoding: utf-8

"""Utilities for testing Marrow Mailer and applications that use it."""

from __future__ import print_function

from threading import Thread
from socket import socket
from threading import Event, RLock
from datetime import datetime
from collections import namedtuple, deque
from smtpd import SMTPServer
from email.parser import Parser
from asyncore import loop

try:
	from pytest import fixture
except:  # We don't honestly care if pytest is installed.
	def fixture(fn):
		return fn


TestMessage = namedtuple('TestMessage', ('sender', 'recipients', 'time', 'message', 'raw'))


class DebuggingSMTPServer(SMTPServer, Thread):
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
	
	def process_message(self, peer, sender, recipients, data):
		# We construct a helpful namedtuple with all of the relevant delivery details.
		message = TestMessage(sender, recipients, datetime.utcnow(), Parser().parsestr(data), data)
		
		with self._lock:  # Protect against parallel access.
			self.messages.append(message)
	
	def run(self):
		while not self._stop.is_set():
			loop(timeout=self.POLL_TIMEOUT, count=1)
	
	def stop(self, timeout=None):
		self._stop.set()
		self.join(timeout)
		self.close()
	
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



@fixture(scope='session')
def smtp(request):
	# TODO: Identify a random port number that is available.
	
	# Construct the debugging server instance.
	server = DebuggingSMTPServer()
	server.start()
	
	request.add_finalizer(server.stop)
	
	return server



if __name__ == '__main__':  # pragma: no cover
	DebuggingSMTPServer.main()
