#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import warnings

from setuptools import setup, find_packages


if sys.version_info < (2, 6):
    raise SystemExit("Python 2.6 or later is required.")

if sys.version_info > (3, 0):
    warnings.warn("Marrow Mailer is untested on Python 3; some features may be broken.", RuntimeWarning)

exec(open(os.path.join("marrow", "mailer", "release.py")).read())



setup(
        name = "marrow.mailer",
        version = version,
        
        description = "A highly efficient and modular mail delivery framework for Python 2.6+ and 3.1+, formerly called TurboMail.",
        long_description = """\
For full documentation, see the README.textile file present in the package,
or view it online on the GitHub project page:

https://github.com/marrow/marrow.mailer""",
        
        author = "Alice Bevan-McGregor",
        author_email = "alice+marrow@gothcandy.com",
        url = "https://github.com/marrow/marrow.mailer",
        license = "MIT",
        
        install_requires = [
            'marrow.util < 2.0',
            'marrow.interface < 2.0'
        ],
        
        test_suite = 'nose.collector',
        tests_require = [
            'nose',
            'coverage',
            'PyDNS',
            'transaction',
            'pymta'
        ] + [
            'futures'
        ] if sys.version_info < (3, 0) else [],
        
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Environment :: Console",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Programming Language :: Python",
            "Programming Language :: Python :: 2.6",
            "Programming Language :: Python :: 2.7",
            # "Programming Language :: Python :: 3",
            # "Programming Language :: Python :: 3.1",
            # "Programming Language :: Python :: 3.2",
            "Topic :: Software Development :: Libraries :: Python Modules"
        ],
        
        packages = find_packages(exclude=['examples', 'tests']),
        zip_safe = True,
        include_package_data = True,
        package_data = {'': ['README.textile', 'LICENSE']},
        
        namespace_packages = ['marrow'],
        
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
                'logging = marrow.mailer.transport.log:LoggingTransport'
            ]
        }
    )
