import datetime
from datetime import date

import pytest

from wampy.peers.clients import Client
from wampy.peers.routers import Crossbar
from wampy.roles.callee import callee
from wampy.testing.helpers import wait_for_session, wait_for_registrations


class DateService(Client):

    @callee
    def get_todays_date(self):
        return datetime.date.today().isoformat()


class TestIP4(object):

    @pytest.fixture(scope="function")
    def config_path(self):
        return './wampy/testing/configs/crossbar.config.ipv4.json'

    def test_ipv4_websocket_connection(self, config_path, router):
        with router:
            service = DateService(router=router)
            with service:
                wait_for_registrations(service, 1)

                client = Client(router=router)

                with client:
                    result = client.rpc.get_todays_date()

            today = date.today()

            assert result == today.isoformat()


class TestIP6(object):

    @pytest.fixture(scope="function")
    def config_path(self):
        return './wampy/testing/configs/crossbar.config.ipv6.json'

    def test_ipv6_websocket_connection(self, config_path, router):
        with router:
            service = DateService(router=router)
            with service:
                wait_for_registrations(service, 1)

                client = Client(router=router)

                with client:
                    result = client.rpc.get_todays_date()

            today = date.today()

            assert result == today.isoformat()


def test_ipv4_secure_websocket_connection():
    # note that TLS not supported by crossbar on ipv6
    crossbar = Crossbar(
        config_path='./wampy/testing/configs/crossbar.config.ipv4.tls.json',
        crossbar_directory='./',
        certificate="./wampy/testing/keys/server_cert.pem",
    )

    with crossbar as router:
        service = DateService(router=router, use_tls=True)
        with service:
            wait_for_registrations(service, 1)

            client = Client(router=router, use_tls=True)
            with client:
                wait_for_session(client)
                result = client.rpc.get_todays_date()

        today = date.today()

        assert result == today.isoformat()
