import json
import logging
import os
import signal
import socket
import subprocess
from socket import error as socket_error
from time import time as now

from wampy.errors import ConnectionError, WampyError
from wampy.mixins import ParseUrlMixin

logger = logging.getLogger('wampy.peers.routers')


class Crossbar(ParseUrlMixin):

    def __init__(
        self, config_path, crossbar_directory=None, certificate=None,
    ):

        with open(config_path) as data_file:
            config_data = json.load(data_file)

        self.config = config_data
        self.config_path = config_path
        config = self.config['workers'][0]
        self.realm = config['realms'][0]
        self.roles = self.realm['roles']

        if len(config['transports']) > 1:
            raise WampyError(
                "Only a single websocket transport is supported by Wampy, "
                "sorry"
            )

        self.transport = config['transports'][0]
        self.url = self.transport.get("url")
        if self.url is None:
            raise WampyError(
                "The ``url`` value is required by Wampy. "
                "Please add to your configuration file. Thanks."
            )

        self.ipv = self.transport['endpoint'].get("version", None)
        if self.ipv is None:
            logger.warning(
                "defaulting to IPV 4 because neither was specified."
            )
            self.ipv = 4

        self.parse_url()

        self.websocket_location = self.resource

        self.crossbar_directory = crossbar_directory
        self.certificate = certificate

        self.proc = None

    @property
    def can_use_tls(self):
        return bool(self.certificate)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.stop()

    def _wait_until_ready(self, timeout=5, raise_if_not_ready=True):
        # we're only ready when it's possible to connect to the CrossBar
        # over TCP - so let's just try it.
        end = now() + timeout
        ready = False

        while not ready:
            timeout = end - now()
            if timeout < 0:
                if raise_if_not_ready:
                    raise ConnectionError(
                        'Failed to connect to CrossBar over {}: {}:{}'.format(
                            self.ipv, self.host, self.port)
                    )
                else:
                    return ready

            try:
                self.try_connection()
            except socket.error:
                pass
            else:
                ready = True

        return ready

    def start(self):
        """ Start Crossbar.io in a subprocess.
        """
        # will attempt to connect or start up the CrossBar
        crossbar_config_path = self.config_path
        cbdir = self.crossbar_directory

        # starts the process from the root of the test namespace
        cmd = [
            'crossbar', 'start',
            '--cbdir', cbdir,
            '--config', crossbar_config_path,
        ]

        self.proc = subprocess.Popen(cmd, preexec_fn=os.setsid)

        self._wait_until_ready()
        logger.info(
            "Crosbar.io is ready for connections on %s (IPV%s)",
            self.url, self.ipv
        )

    def stop(self):
        logger.warning("stopping crossbar")
        try:
            os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
        except OSError as exc:
            if "No such process" in str(exc):
                return
            logger.exception("failed to stop crossbar")

    def try_connection(self):
        if self.ipv == 4:
            _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            try:
                _socket.connect((self.host, self.port))
            except socket_error:
                pass

        elif self.ipv == 6:
            _socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

            try:
                _socket.connect(("::", self.port))
            except socket_error:
                pass

        else:
            raise WampyError(
                "unknown IPV: {}".format(self.ipv)
            )

        _socket.shutdown(socket.SHUT_RDWR)
        _socket.close()
