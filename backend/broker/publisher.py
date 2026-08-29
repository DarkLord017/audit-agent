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

    def publish(self, message: JobMessage) -> None:
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
        log.info("queued job %s", message.job_id)

    def close(self) -> None:
        if self._connection and self._connection.is_open:
            self._connection.close()
