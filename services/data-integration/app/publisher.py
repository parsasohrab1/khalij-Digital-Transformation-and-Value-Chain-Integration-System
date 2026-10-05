"""Publishing a standard event on Kafka with a topic per subsidiary."""
from __future__ import annotations

import logging
import os
import socket
from datetime import datetime, timezone
from typing import Any

from shared.events import SCHEMA_VERSION, CloudEventEnvelope
from shared.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_OFFLINE_EVENTS: list[dict[str, Any]] = []


def _kafka_reachable(timeout: float = 0.3) -> bool:
    if os.getenv("KAFKA_ENABLED", "true").lower() in {"0", "false", "no"}:
        return False
    bootstrap = settings.kafka_bootstrap_servers.split(",")[0].strip()
    host, _, port_s = bootstrap.partition(":")
    port = int(port_s or "9092")
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


class DomainEventPublisher:
    def __init__(self) -> None:
        self._producer = None
        self._mode = "unknown"  # live | offline

    def _get_producer(self):
        if self._mode == "offline":
            return None
        if self._producer is not None:
            return self._producer
        if not _kafka_reachable():
            self._mode = "offline"
            logger.warning("Kafka unreachable; domain events buffered offline")
            return None
        try:
            from shared.kafka_utils import KafkaEventProducer

            self._producer = KafkaEventProducer(
                settings.kafka_bootstrap_servers, client_id="dvc-data-integration"
            )
            self._mode = "live"
            return self._producer
        except Exception as exc:  # noqa: BLE001
            logger.warning("Kafka producer init failed: %s", exc)
            self._mode = "offline"
            return None

    def subsidiary_topic(self, subsidiary_code: str) -> str:
        return f"{settings.kafka_topic_subsidiary_prefix}.{subsidiary_code.lower()}"

    def publish(
        self,
        *,
        event_type: str,
        subsidiary_code: str,
        source: str,
        data: dict[str, Any],
        also_domain_topic: str | None = None,
    ) -> int:
        envelope = CloudEventEnvelope(
            source=source,
            type=event_type,  # type: ignore[arg-type]
            subject=subsidiary_code,
            time=datetime.now(timezone.utc).replace(tzinfo=None),
            dataschema=f"khalij.dvc.events/{SCHEMA_VERSION}",
            data=data,
        )
        payload = envelope.model_dump(mode="json")
        topics = [self.subsidiary_topic(subsidiary_code)]
        if also_domain_topic:
            topics.append(also_domain_topic)

        producer = self._get_producer()
        if producer is None:
            for topic in topics:
                _OFFLINE_EVENTS.append({**payload, "_topic": topic})
            return 0

        published = 0
        try:
            for topic in topics:
                producer.send(topic, payload, key=subsidiary_code)
                published += 1
            producer._producer.poll(0)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Kafka publish failed, switching offline: %s", exc)
            self._mode = "offline"
            self._producer = None
            for topic in topics:
                _OFFLINE_EVENTS.append({**payload, "_topic": topic})
            return 0
        return published

    @staticmethod
    def offline_buffer(limit: int = 50) -> list[dict[str, Any]]:
        return _OFFLINE_EVENTS[-limit:]
