import logging

from wampy.messages.message import Message

logger = logging.getLogger(__name__)


class Result(Message):
    """ The Dealer sends a "RESULT" message to the original
    Caller ::

           [RESULT, CALL.Request|id, Details|dict]

        or

           [RESULT, CALL.Request|id, Details|dict, YIELD.Arguments|list]

        or

           [RESULT, CALL.Request|id, Details|dict, YIELD.Arguments|list,
               YIELD.ArgumentsKw|dict]

    """
    WAMP_CODE = 50

    def __init__(
            self, wamp_code, request_id, details_dict, yield_args=None,
            yield_kwargs=None
    ):

        assert wamp_code == self.WAMP_CODE

        self.request_id = request_id
        self.details = details_dict
        self.yield_args = yield_args
        self.yield_kwargs = yield_kwargs

        self.message = [
            self.WAMP_CODE, self.request_id, self.details, self.yield_args,
            self.yield_kwargs
        ]

    def process(self, message, client):
        logger.info("RESULT received: %s", message)
        client.session._message_queue.put(message)
