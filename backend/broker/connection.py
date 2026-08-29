"""Shared RabbitMQ setup.

Both the publisher and the instancer must agree on the queue name and
its settings, so they are declared in one place. Declaring a queue is
idempotent -- whoever starts first creates it.
"""

import os

import pika

QUEUE_NAME = "evmbench.jobs"


def broker_url() -> str:
    return os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2F")


def connect() -> pika.BlockingConnection:
    params = pika.URLParameters(broker_url())
    params.heartbeat = 60
    params.blocked_connection_timeout = 30
    return pika.BlockingConnection(params)


def declare_queue(channel) -> None:
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
