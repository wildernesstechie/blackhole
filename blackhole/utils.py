# (The MIT License)
#
# Copyright (c) 2013-2017 Kura
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the 'Software'), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Provides utility functionality."""

import codecs
import os
import pathlib
import random
import socket
import time

try:  # pragma: no cover
    import asyncio
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:  # pragma: no cover
    pass


__all__ = ('mailname', 'message_id', 'get_version')


def mailname(mailname_file='/etc/mailname'):
    """
    Fully qualified domain name for HELO and EHLO.

    :param mailname_file: A path to the mailname file.
    :type mailname_file: :py:obj:`str`
    :returns: A domain name.
    :rtype: :py:obj:`str`

    .. note::

       Prefers content of `mailname_file`, falls back on
       :py:func:`socket.getfqdn` if `mailname_file` does not exist or cannot be
       opened for reading.
    """
    mailname_file = pathlib.Path(mailname_file)
    if os.access(mailname_file, os.R_OK):
        mailname_content = open(mailname_file, 'r').readlines()
        if len(mailname_content) == 0:
            return socket.getfqdn()
        mailname_content = mailname_content[0].strip()
        if mailname_content != '':
            return mailname_content
    return socket.getfqdn()


def message_id(domain):
    """
    Return a string suitable for RFC 2822 compliant Message-ID.

    :param domain: A fully qualified domain.
    :type domain: :py:obj:`str`
    :returns: An RFC 2822 compliant Message-ID.
    :rtype: :py:obj:`str`
    """
    timeval = int(time.time() * 100)
    pid = os.getpid()
    randint = random.getrandbits(64)
    return '<{0}.{1}.{2}@{3}>'.format(timeval, pid, randint, domain)


def get_version():
    """
    Extract the __version__ from a file without importing it.

    :return: The version that was extracted.
    :rtype: :py:obj:`str`
    :raises: :py:exc:`AssertionError`
    """
    path = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(pathlib.Path(path), pathlib.Path('__init__.py'))
    if not os.access(filepath, os.R_OK):
        raise OSError('Cannot open __init__.py file for reading')
    with codecs.open(filepath, encoding='utf-8') as fp:
        for line in fp:
            if line.startswith('__version__'):
                try:
                    _, vers = line.split('=')
                except ValueError:
                    msg = 'Cannot extract version from __version__'
                    raise AssertionError(msg)
                version = vers.strip().replace('"', '').replace("'", '')
                try:
                    major, minor, patch = version.split('.')
                    digits = (major.isdigit(), minor.isdigit(),
                              patch.isdigit())
                    if not all(digits):
                        msg = ('{0} is not a valid version '
                               'number').format(version)
                        raise AssertionError(msg)
                except ValueError:
                    msg = '{0} is not a valid version number'.format(version)
                    raise AssertionError(msg)
                return version
    raise AssertionError('No __version__ assignment found')
