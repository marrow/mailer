#!/usr/bin/env python
# encoding: utf-8

import sys
import os

from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages


if sys.version_info < (2, 6):
    raise SystemExit("Python 2.6 or later is required.")

exec(open(os.path.join("marrow", "tags", "release.py")))


setup(
    name="marrow.mail",
    version=version,

    description="""
A highly efficient and modular mail delivery framework for
Python 2.6+ and 3.1+, formerly called Turbomail.""",
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

    packages=find_packages(exclude=["examples", "tests", "tests.*",
                                    "docs", "third-party"]),
    include_package_data=True,
    package_data={
        "": ["README.textile", "LICENSE", "distribute_setup.py"],
        "docs": ["Makefile", "source/*"]
    },
    zip_safe=True,

    namespace_packages=["marrow"]
)
