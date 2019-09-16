"""Release information about Marrow Mailer."""

from collections import namedtuple


version_info = namedtuple('version_info', ('major', 'minor', 'micro', 'releaselevel', 'serial'))(5, 0, 0, 'alpha', 1)
version = ".".join([str(i) for i in version_info[:3]]) + ((version_info.releaselevel[0] + str(version_info.serial)) if version_info.releaselevel != 'final' else '')

author = namedtuple('Author', ['name', 'email'])("Alice Bevan-McGregor", 'alice@gothcandy.com')

description = "A light-weight modular mail delivery framework for Python 3.7+ and Pypy3."
url = 'https://github.com/marrow/mailer/'
