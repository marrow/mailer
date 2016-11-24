#!/usr/bin/env python
# encoding: utf-8

import os
import sys

try:
	from setuptools.core import setup, find_packages
except ImportError:
	from setuptools import setup, find_packages

if sys.version_info < (2, 6):
	raise SystemExit("Python 2.6 later is required.")

elif sys.version_info > (3, 0) and sys.version_info < (3, 2):
	raise SystemExit("Python 3.2 or later is required.")


version = description = url = author = ""  # Satisfy linter.
exec(open(os.path.join("marrow", "mailer", "release.py")).read())

here = os.path.abspath(os.path.dirname(__file__))

tests_require = ['pytest', 'pytest-cov', 'pytest-spec', 'pytest-flakes', 'coverage', 'transaction']


# # Entry Point

setup(
		name = "marrow.mailer",
		version = version,
		
		description = description,
		long_description = "", # codecs.open(os.path.join(here, 'README.rst'), 'r', 'utf8').read(),
		url = url,
		
		author = author.name,
		author_email = author.email,
		
		license = 'MIT',
		keywords = '',
		classifiers = [
				"Development Status :: 5 - Production/Stable",
				"Environment :: Console",
				"Intended Audience :: Developers",
				"License :: OSI Approved :: MIT License",
				"Operating System :: OS Independent",
				"Programming Language :: Python",
				"Programming Language :: Python :: 2.6",
				"Programming Language :: Python :: 2.7",
				"Programming Language :: Python :: 3.3",
				"Programming Language :: Python :: 3.4",
				"Programming Language :: Python :: 3.5",
				"Topic :: Software Development :: Libraries :: Python Modules",
				"Topic :: Utilities",
			],
		
		packages = find_packages(exclude=['examples', 'tests']),
		include_package_data = True,
		package_data = {'': ['README.textile', 'LICENSE.txt']},
		namespace_packages = ['marrow'],
		
		# ## Dependency Declaration
		
		install_requires = [
				'marrow.util < 2.0',
			],
		
		extras_require = {
				":python_version<'3.0.0'": ['futures'],
				'develop': tests_require,
				'requests': ['requests'],
			},
		
		tests_require = tests_require,
		
		setup_requires = ['pytest-runner'] if {'pytest', 'test', 'ptr'}.intersection(sys.argv) else [],
		
		# ## Plugin Registration
		
		entry_points = {
				'marrow.mailer.manager': [
						'immediate = marrow.mailer.manager.immediate:ImmediateManager',
						'futures = marrow.mailer.manager.futures:FuturesManager',
						'dynamic = marrow.mailer.manager.dynamic:DynamicManager',
						# 'transactional = marrow.mailer.manager.transactional:TransactionalDynamicManager'
					],
				'marrow.mailer.transport': [
						'amazon = marrow.mailer.transport.ses:AmazonTransport',
						'mock = marrow.mailer.transport.mock:MockTransport',
						'smtp = marrow.mailer.transport.smtp:SMTPTransport',
						'mbox = marrow.mailer.transport.mbox:MailboxTransport',
						'mailbox = marrow.mailer.transport.mbox:MailboxTransport',
						'maildir = marrow.mailer.transport.maildir:MaildirTransport',
						'sendmail = marrow.mailer.transport.sendmail:SendmailTransport',
						'imap = marrow.mailer.transport.imap:IMAPTransport',
						'appengine = marrow.mailer.transport.gae:AppEngineTransport',
						'logging = marrow.mailer.transport.log:LoggingTransport',
						'postmark = marrow.mailer.transport.postmark:PostmarkTransport',
						'sendgrid = marrow.mailer.transport.sendgrid:SendgridTransport',
						'mailgun = marrow.mailer.transport.mailgun:MailgunTransport[requests]',
					]
			},
		
		zip_safe = False,
	)
