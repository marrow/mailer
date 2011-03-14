#!/usr/bin/env python
# encoding: utf-8

import sys, os

try:
    from distribute_setup import use_setuptools
    use_setuptools()

except ImportError:
    pass

from setuptools import setup, find_packages


if sys.version_info < (2, 6):
    raise SystemExit("Python 2.6 or later is required.")

exec(open(os.path.join("marrow", "tags", "release.py")))



setup(
        name = "marrow.mail",
        version = version,
        
        description = "A highly efficient and modular mail delivery framework for Python 2.6+ and 3.1+, formerly.",
        author = "Alice Bevan-McGregor",
        author_email = "alice+marrow@gothcandy.com",
        url = "",
        download_url = "",
        license = "MIT",
        keywords = '',
        
        install_requires = ['marrow.util'],
        
        test_suite = 'nose.collector',
        tests_require = ['nose', 'coverage'],
        
        classifiers = [
                "Development Status :: 1 - Planning",
                "Environment :: Console",
                "Intended Audience :: Developers",
                "License :: OSI Approved :: MIT License",
                "Operating System :: OS Independent",
                "Programming Language :: Python",
                "Topic :: Internet :: WWW/HTTP :: WSGI",
                "Topic :: Software Development :: Libraries :: Python Modules"
            ],
        
        packages = find_packages(exclude=['examples', 'tests', 'tests.*', 'docs', 'third-party']),
        include_package_data = True,
        package_data = {
                '': ['README.textile', 'LICENSE', 'distribute_setup.py'],
                'docs': ['Makefile', 'source/*']
            },
        zip_safe = True,
        
        namespace_packages = ['marrow']
    )
