#!/usr/bin/env python3

from setuptools import setup


setup(
		use_scm_version = {
				'version_scheme': 'post-release',
				'local_scheme': 'dirty-tag',
			}
	)
