import logging

from wampy.messages.message import Message

logger = logging.getLogger(__name__)


class Registered(Message):
    """ [REGISTERED, REGISTER.Request|id, Registration|id]
    """
    WAMP_CODE = 65

    def __init__(self, wamp_code, request_id, registration_id):
        assert wamp_code == self.WAMP_CODE

        self.request_id = request_id
        self.registration_id = registration_id

        self.message = [
            self.WAMP_CODE, self.request_id, self.registration_id,
        ]

    def process(self, message, client):
        session = client.session
        wamp_code, request_id, registration_id = message
        procedure_name = client.request_ids[request_id]
        session.registration_map[registration_id] = procedure_name

        logger.info(
            'Registered procedure name "%s"', procedure_name,
        )
