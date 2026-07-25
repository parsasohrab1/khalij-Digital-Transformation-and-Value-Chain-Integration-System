"""توابع کمکی Kafka برای استریم رویدادهای زنجیره ارزش (Data Mesh)."""
from __future__ import annotations

import json
import logging
from collections.abc import Callable, Iterator
from datetime import datetime

from confluent_kafka import Consumer, KafkaError, KafkaException, Producer

logger = logging.getLogger(__name__)


def _json_default(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class KafkaEventProducer:
    def __init__(self, bootstrap_servers: str, client_id: str = "khalij-dvc"):
        self._producer = Producer(
            {
                "bootstrap.servers": bootstrap_servers,
                "client.id": client_id,
                "retries": 5,
                "retry.backoff.ms": 500,
            }
        )

    def send(self, topic: str, payload: dict, key: str | None = None) -> None:
        try:
            self._producer.produce(
                topic=topic,
                key=key,
                value=json.dumps(payload, default=_json_default).encode("utf-8"),
                callback=self._delivery_callback,
            )
            self._producer.poll(0)
        except BufferError:
            logger.warning("صف تولید Kafka پر است، در انتظار flush...")
            self._producer.flush(5)

    @staticmethod
    def _delivery_callback(err, msg):
        if err is not None:
            logger.error("ارسال پیام به Kafka ناموفق بود: %s", err)

    def flush(self, timeout: float = 10.0) -> None:
        self._producer.flush(timeout)


class KafkaEventConsumer:
    def __init__(self, bootstrap_servers: str, group_id: str, topics: list[str]):
        self._consumer = Consumer(
            {
                "bootstrap.servers": bootstrap_servers,
                "group.id": group_id,
                "auto.offset.reset": "latest",
                "enable.auto.commit": True,
            }
        )
        self._consumer.subscribe(topics)

    def poll_messages(self, timeout: float = 1.0) -> Iterator[dict]:
        while True:
            msg = self._consumer.poll(timeout)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                raise KafkaException(msg.error())
            try:
                yield json.loads(msg.value().decode("utf-8"))
            except json.JSONDecodeError:
                logger.warning("پیام نامعتبر JSON دریافت شد و نادیده گرفته شد.")

    def run(self, handler: Callable[[dict], None]) -> None:
        for message in self.poll_messages():
            handler(message)

    def close(self) -> None:
        self._consumer.close()
