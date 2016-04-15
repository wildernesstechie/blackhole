# (The MIT License)
#
# Copyright (c) 2016 Kura
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

"""Configuration structure."""


import argparse
import getpass
import grp
import inspect
import logging
import os
import pwd
import re
import sys

from blackhole.exceptions import ConfigException


version = __import__('blackhole').__version__


def parse_cmd_args():
    parser = argparse.ArgumentParser('blackhole')
    parser.add_argument('-c', '--conf', type=str,
                        dest='config_file', metavar='/etc/blackhole.conf')
    parser.add_argument('-v', '--version', action='version',
                        version=version)
    parser.add_argument('-t', '--test', dest='test', action='store_true',
                        help='perform a configuration test and exit')
    parser.add_argument('-d', '--debug', dest='debug', action='store_true',
                        help='enable debugging mode.')
    parser.add_argument('-b', '--background', dest='background',
                        action='store_true',
                        help='run as a background process (daemonise).')
    return parser.parse_args()


def config_test(args):
    """
    Test the validity of the configuration file content.

    .. note::

       Problems with the configuration will be written to the console using
       the `logging` module.

       Calls `sys.exit` upon an error.

    :param args: arguments parsed from `argparse`.
    :type args: `argparse.Namespace`
    """
    conffile = args.config_file if args.config_file else None
    logger = logging.getLogger('blackhole.config_test')
    logger.setLevel(logging.INFO)
    if conffile is None:
        logger.fatal('No config file provided.')
        sys.exit(os.EX_USAGE)
    Config(conffile).load().self_test()
    logger.info('%s syntax is OK', conffile)
    logger.info('%s test was successful', conffile)
    sys.exit(os.EX_OK)


class Singleton(type):
    """A singleton for `blackhole.config.Config`."""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """A singleton for `blackhole.config.Config`."""
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args,
                                                                 **kwargs)
        return cls._instances[cls]


class Config(metaclass=Singleton):
    """
    Configuration module.

    Default values are provided as well as self-test functionality
    to sanity check configuration.
    """

    config_file = None
    _address = '127.0.0.1'
    _port = 25
    _user = None
    _group = None
    # _log_file = None
    _timeout = 60
    _tls_port = None
    _tls_key = None
    _tls_cert = None
    _pidfile = None

    def __init__(self, config_file="/etc/blackhole.conf"):
        """
        Initialise the configuration.

        :param config_file: The configuration file,
                            default '/etc/blackhole.conf'
        :type config_file: str
        """
        self.config_file = config_file
        self.user = getpass.getuser()
        self.group = grp.getgrgid(os.getgid()).gr_name

    def load(self):
        """
        Load the configuration file and parse.

        Spaces, single and double quotes will be stripped. Lines beginning in
        # will be ignored.

        :returns: obj -- An instance of `blackhole.config.Config`
        """
        if self.config_file is None:
            return self
        if not os.access(self.config_file, os.R_OK):
            raise IOError('Config file does not exist or is not readable.')
        for line in open(self.config_file, 'r').readlines():
            line = line.strip()
            if line.startswith('#'):
                continue
            try:
                key, value = line.split('=')
            except ValueError:
                continue
            key, value = key.strip(), value.strip()
            key = "_{}".format(key)
            value = value.replace('"', '').replace("'", '')
            setattr(self, key, value)
        return self

    @property
    def address(self):
        """
        An IPv4 address.

        :returns: str -- IPv4 address.
        """
        return self._address

    @address.setter
    def address(self, address):
        self._address = address

    @property
    def port(self):
        """
        A port number.

        :returns: int -- A port number.
        """
        return int(self._port)

    @port.setter
    def port(self, port):
        self._port = port

    @property
    def user(self):
        """
        A UNIX user.

        .. note::

           Defaults to the current user.

        :returns: str -- A UNIX user.
        """
        return self._user

    @user.setter
    def user(self, user):
        self._user = user

    @property
    def group(self):
        """
        A UNIX group.

        .. note::

           Defaults to the current group.

        :returns: str -- A UNIX group.
        """
        return self._group

    @group.setter
    def group(self, group):
        self._group = group

    # @property
    # def log_file(self):
    #     """
    #     A full file path.
    #
    #     :returns: str -- A full file path.
    #     """
    #     return self._log_file
    #
    # @log_file.setter
    # def log_file(self, value):
    #     self._log_file = value

    @property
    def timeout(self):
        """
        A timeout in seconds.

        .. note::

           Defaults to 60 seconds.

        :returns: int -- A timeout in seconds.
        """
        return int(self._timeout)

    @timeout.setter
    def timeout(self, value):
        self._timeout = value

    @property
    def tls_port(self):
        """
        A port number.

        :returns: int
        """
        if self._tls_port is None:
            return None
        return int(self._tls_port)

    @tls_port.setter
    def tls_port(self, tls_port):
        self._tls_port = tls_port

    @property
    def tls_key(self):
        """
        A TLS key file.

        :returns: str
        """
        return self._tls_key

    @tls_key.setter
    def tls_key(self, value):
        self._tls_key = value

    @property
    def tls_cert(self):
        """
        A TLS certificate file.

        :returns: str
        """
        return self._tls_cert

    @tls_cert.setter
    def tls_cert(self, tls_cert):
        self._tls_cert = tls_cert

    @property
    def pidfile(self):
        return self._pidfile

    @pidfile.setter
    def pidfile(self, pidfile):
        self._pidfile = pidfile

    def self_test(self):
        """Test configuration validity.

        .. notes::

           Uses the magic of `inspect.getmembers` to introspect methods
           beginning with 'test_' and calling them.

        :returns: obj -- An instance of `blackhole.config.Config`.
        """
        members = inspect.getmembers(self, predicate=inspect.ismethod)
        for member in members:
            name, mcallable = member
            if name.startswith('test_'):
                mcallable()
        return self

    def test_address(self):
        """
        Validate IPv4 address format.

        :raises: `blackhole.exceptions.ConfigException`

        .. note::

           Classifies 'localhost' as a valid IPv4 address.
        """
        address = re.match(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", self.address)
        if self.address not in ('localhost',) and not address:
            msg = '{} is not a valid IPv4 address.'.format(self.address)
            raise ConfigException(msg)

    def test_port(self):
        """
        Validate port number.

        :raises: `blackhole.exceptions.ConfigException`

        .. note::

           Only verifies port is a valid integer, does not verify port is
           available or not in use.
        """
        try:
            int(self.port)
        except ValueError:
            msg = '{} is not a valid port number.'.format(self.port)
            raise ConfigException(msg)

    def test_user(self):
        """
        Validate user exists in UNIX password database.

        :raises: `blackhole.exceptions.ConfigException`

        .. note::

           Defaults to `getpass.getuser` if no user is specified.
        """
        try:
            pwd.getpwnam(self.user)
        except ValueError:
            msg = '{} is not a valid user.'.format(self.user)
            raise ConfigException(msg)

    def test_group(self):
        """
        Validate group exists in UNIX group database.

        :raises: `blackhole.exceptions.ConfigException`

        .. note::

           Defaults to `getpass.getuser` if no group is specified. Assumes a
           group has been created with the same name as the user.
        """
        try:
            grp.getgrnam(self.group)
        except ValueError:
            msg = '{} is a not a valid group.'.format(self.group)
            raise ConfigException(msg)

    # def test_log_file(self):
    #     """
    #     Validate log file and location are writable.
    #
    #     :raises: `blackhole.exceptions.ConfigException`
    #     """
    #     if self.log_file is not None and not os.access(self.log_file, os.W_OK):
    #         msg = 'Cannot open log file {} for writing.'.format(self.log_file)
    #         raise ConfigException(msg)

    def test_timeout(self):
        """
        Validate timeout - only allow a valid integer value in seconds.

        :raises: `blackhole.exceptions.ConfigException`
        """
        try:
            int(self.timeout)
        except ValueError:
            msg = '{} is not a valid number of seconds.'.format(self.timeout)
            raise ConfigException(msg)

    def test_tls_port(self):
        """
        Validate TLS port number.

        :raises: `blackhole.exceptions.ConfigException`

        .. note::

           Only verifies port is a valid integer, does not verify port is
           available or not in use.
        """
        if self._tls_port is None:
            return
        try:
            int(self.tls_port)
        except ValueError:
            msg = '{} is not a valid port number.'.format(self.tls_port)
            raise ConfigException(msg)
        if self.port == self.tls_port:
            raise ConfigException("SMTP and SMTP/TLS ports must be different.")

    def test_tls_settings(self):
        """
        Validate TLS configuration.

        :raises: `blackhole.exceptions.ConfigException`

        .. note::

           Verifies that if you provide all TLS settings, not just some.
        """
        port = self.tls_port if self.tls_port is not None else False
        cert = os.access(self.tls_cert, os.R_OK) if self.tls_cert else False
        key = os.access(self.tls_key, os.R_OK) if self.tls_key else False
        if (port, cert, key) == (False, False, False):
            return
        if not all((port, cert, key)):
            msg = 'To use TLS you must supply a port, certificate file and key file.'
            raise ConfigException(msg)
