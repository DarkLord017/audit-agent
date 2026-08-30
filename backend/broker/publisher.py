"""Puts jobs on the queue. Used by the API."""

import logging

import pika

from backend.broker.connection import QUEUE_NAME, connect, declare_queue
from backend.broker.messages import JobMessage

log = logging.getLogger(__name__)


class JobPublisher:
    """Publishes a job and returns immediately.

    The API does not start containers any more. It writes the row,
    drops a message here, and answers the user in milliseconds.
    """

    def __init__(self, connection: pika.BlockingConnection | None = None):
        self._connection = connection
        self._channel = None

    @property
    def channel(self):
        """Open lazily, and reopen if the broker dropped us."""
        if self._connection is None or self._connection.is_closed:
            self._connection = connect()
            self._channel = None
        if self._channel is None or self._channel.is_closed:
            self._channel = self._connection.channel()
            declare_queue(self._channel)
        return self._channel

    # Both trees, because a dead connection surfaces either way depending
    # on where pika notices it. StreamLostError sits under
    # AMQPConnectionError; ChannelWrongStateError under AMQPChannelError.
    RETRYABLE = (pika.exceptions.AMQPConnectionError, pika.exceptions.AMQPChannelError)

    def publish(self, message: JobMessage) -> None:
        """Publish, reconnecting once if the broker dropped us.

        The is_closed check in `channel` is not enough on its own. pika
        only discovers a connection the broker closed when it tries to
        use it, so an idle API answers the next submission with a 500
        (StreamLostError: connection reset by peer) instead of quietly
        reconnecting. One retry on a fresh connection covers it; a second
        failure is real and should surface.
        """
        try:
            self._publish(message)
        except self.RETRYABLE as exc:
            log.warning("broker dropped us (%s); reconnecting and retrying once", exc)
            self._reset()
            self._publish(message)
        log.info("queued job %s", message.job_id)

    def _reset(self) -> None:
        """Throw the cached connection away so `channel` builds a new one."""
        try:
            if self._connection is not None and self._connection.is_open:
                self._connection.close()
        except Exception:                       # already gone; nothing to salvage
            log.debug("stale connection would not close cleanly", exc_info=True)
        self._connection = None
        self._channel = None

    def _publish(self, message: JobMessage) -> None:
        self.channel.basic_publish(
            exchange="",
            routing_key=QUEUE_NAME,
            body=message.to_bytes(),
            properties=pika.BasicProperties(
                # persistent: written to disk, so a broker restart does
                # not lose queued jobs.
                delivery_mode=pika.DeliveryMode.Persistent,
                content_type="application/json",
                message_id=message.job_id,
            ),
        )

    def close(self) -> None:
        if self._connection and self._connection.is_open:
            self._connection.close()
