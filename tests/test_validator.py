# encoding: utf-8

"""Test the primary configurator interface, Delivery."""

import DNS
import logging

from unittest import TestCase
from nose.tools import ok_, eq_, raises
from nose.plugins.skip import Skip, SkipTest

from marrow.mailer.validator import ValidationException, BaseValidator, DomainValidator, EmailValidator, EmailHarvester

from marrow.util.bunch import Bunch


log = logging.getLogger('tests')



class TestBaseValidator(TestCase):
	class MockValidator(BaseValidator):
		def validate(self, success=True):
			if success:
				return True, None
			
			return False, "Mock failure."
	
	def test_validator_success(self):
		mock = self.MockValidator()
		self.assertTrue(mock.validate_or_raise())
	
	def test_validator_failure(self):
		mock = self.MockValidator()
		self.assertRaises(ValidationException, mock.validate_or_raise, False)


def test_common_rules():
	mock = DomainValidator()
	dataset = [
			('valid@example.com', ''),
			('', 'It cannot be empty.'),
			('*' * 256, 'It cannot be longer than 255 chars.'),
			('.invalid@example.com', 'It cannot start with a dot.'),
			('invalid@example.com.', 'It cannot end with a dot.'),
			('invalid..@example.com', 'It cannot contain consecutive dots.'),
		]
	
	def closure(address, expect):
		eq_(mock._apply_common_rules(address, 255), (address, expect))
	
	for address, expect in dataset:
		yield closure, address, expect


def test_common_rules_fixed():
	mock = DomainValidator(fix=True)
	dataset = [
			('.fixme@example.com', ('fixme@example.com', '')),
			('fixme@example.com.', ('fixme@example.com', '')),
		]
	
	def closure(address, expect):
		eq_(mock._apply_common_rules(address, 255), expect)
	
	for address, expect in dataset:
		yield closure, address, expect


def test_domain_validation_basic():
	mock = DomainValidator()
	dataset = [
			('example.com', ''),
			('xn--ls8h.la', ''), # IDN: (poop).la
			('', 'Invalid domain: It cannot be empty.'),
			('-bad.example.com', 'Invalid domain.'),
		]
	
	def closure(domain, expect):
		eq_(mock.validate_domain(domain), (domain, expect))
	
	for domain, expect in dataset:
		yield closure, domain, expect


def test_domain_lookup():
	mock = DomainValidator()
	dataset = [
			('gothcandy.com', 'a', '174.129.236.35'),
			('a' * 64 + '.gothcandy.com', 'a', False),
			('gothcandy.com', 'mx', [(10, 'mx1.emailsrvr.com'), (20, 'mx2.emailsrvr.com')]),
			('nx.example.com', 'a', False),
			('xn--ls8h.la', 'a', '38.103.165.5'), # IDN: (poop).la
		]
	
	def closure(domain, kind, expect):
		try:
			eq_(mock.lookup_domain(domain, kind, server=['8.8.8.8']), expect)
		except DNS.DNSError:
			raise SkipTest("Skipped due to DNS error.")

	
	for domain, kind, expect in dataset:
		yield closure, domain, kind, expect


def test_domain_validation():
	mock = DomainValidator(lookup_dns='mx')
	dataset = [
			('example.com', 'Domain does not seem to exist.'),
			('xn--ls8h.la', ''), # IDN: (poop).la
			('', 'Invalid domain: It cannot be empty.'),
			('-bad.example.com', 'Invalid domain.'),
			('gothcandy.com', ''),
			('a' * 64 + '.gothcandy.com', 'Domain does not seem to exist.'),
			('gothcandy.com', ''),
			('nx.example.com', 'Domain does not seem to exist.'),
		]
	
	def closure(domain, expect):
		try:
			eq_(mock.validate_domain(domain), (domain, expect))
		except DNS.DNSError:
			raise SkipTest("Skipped due to DNS error.")
	
	for domain, expect in dataset:
		yield closure, domain, expect


@raises(RuntimeError)
def test_bad_lookup_record_1():
	mock = DomainValidator(lookup_dns='cname')


@raises(RuntimeError)
def test_bad_lookup_record_2():
	mock = DomainValidator()
	mock.lookup_domain('example.com', 'cname')


def test_email_validation():
	mock = EmailValidator()
	dataset = [
			('user@example.com', ''),
			('user@xn--ls8h.la', ''), # IDN: (poop).la
			('', 'The e-mail is empty.'),
			('user@user@example.com', 'An email address must contain a single @'),
			('user@-example.com', 'The e-mail has a problem to the right of the @: Invalid domain.'),
			('bad,user@example.com', 'The email has a problem to the left of the @: Invalid local part.'),
		]
	
	def closure(address, expect):
		eq_(mock.validate_email(address), (address, expect))
	
	for address, expect in dataset:
		yield closure, address, expect


def test_harvester():
	mock = EmailHarvester()
	dataset = [
			('', []),
			('test@example.com', ['test@example.com']),
			('lorem ipsum test@example.com dolor sit', ['test@example.com']),
		]
	
	def closure(text, expect):
		eq_(list(mock.harvest(text)), expect)
	
	for text, expect in dataset:
		yield closure, text, expect
