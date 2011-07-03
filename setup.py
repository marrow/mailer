#!/usr/bin/env python
# encoding: utf-8

import sys
import os

from setuptools import setup, find_packages


if sys.version_info < (2, 6):
    raise SystemExit("Python 2.6 or later is required.")

exec(open(os.path.join("marrow", "mailer", "release.py")).read())


setup(
    name="marrow.mailer",
    version=version,
    
    description="""
A highly efficient and modular mail delivery framework for
Python 2.6+ and 3.1+, formerly called TurboMail.""",
    author="Alice Bevan-McGregor",
    author_email="alice+marrow@gothcandy.com",
    url="",
    download_url="",
    license="MIT",
    keywords="",
    
    install_requires=["marrow.util"],
    
    test_suite="nose.collector",
    tests_require=["nose", "coverage"],
    
    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    
    packages=find_packages(exclude=["examples", "tests"]),
    zip_safe=True,
    include_package_data=True,
    package_data={
        "": ["README.textile", "LICENSE", "distribute_setup.py"]
    },
    
    namespace_packages=["marrow"],
    entry_points = {
        'marrow.mailer.manager': [
            "immediate = marrow.mailer.manager.immediate:ImmediateManager",
            "futures = marrow.mailer.manager.futures:FuturesManager",
            "dynamic = marrow.mailer.manager.dynamic:DynamicManager",
            "transactional = marrow.mailer.manager.transactional:TransactionalDynamicManager"
        ],
        'marrow.mailer.transport': [
            "amazon = marrow.mailer.transport.ses:AmazonTransport",
            "mock = marrow.mailer.transport.mock:MockTransport",
            "smtp = marrow.mailer.transport.smtp:SMTPTransport",
            "mbox = marrow.mailer.transport.mbox:MailboxTransport",
            "mailbox = marrow.mailer.transport.mbox:MailboxTransport",
            "maildir = marrow.mailer.transport.maildir:MaildirTransport",
            "sendmail = marrow.mailer.transport.sendmail:SendmailTransport",
            "imap = marrow.mailer.transport.imap:IMAPTransport",
            "appengine = marrow.mailer.transport.gae:AppEngineTransport",
            "logging = marrow.mailer.transport.log:LoggingTransport",
            "sms = marrow.mailer.transport.sms:SMSTransport",
        ]
    }
)
