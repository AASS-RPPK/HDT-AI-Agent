"""
Kafka consumer for HDT AI Agent.

Subscribes to chatbot.request events published by the Feedback Workflow Producer,
calls the existing Gemini chatbot logic, and publishes the AI response back to
chatbot.response.

Message format in:  {"taskId": str, "message": str, "conversationId": str, "caseId": str}
Message format out: {"taskId": str, "aiResponse": str, "conversationId": str}
"""
from __future__ import annotations

import asyncio
import json
import logging
import os

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from app.db.session import SessionLocal
from app.services.chatbot import send_message

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC_REQUEST   = "chatbot.request"
TOPIC_RESPONSE  = "chatbot.response"

log = logging.getLogger("hdt.ai_agent.kafka")


async def run_chatbot_consumer() -> None:
    """Long-running coroutine: consumes chatbot.request, publishes chatbot.response."""
    # Wait for Kafka to be available before starting
    producer: AIOKafkaProducer | None = None
    for attempt in range(1, 31):
        try:
            producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP)
            await producer.start()
            log.info("Kafka producer connected (attempt %d).", attempt)
            break
        except Exception as exc:
            log.warning("Kafka not ready (attempt %d/30): %s", attempt, exc)
            producer = None
            await asyncio.sleep(5)
    else:
        log.error("Could not connect to Kafka — chatbot consumer not started.")
        return

    consumer = AIOKafkaConsumer(
        TOPIC_REQUEST,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id="ai-agent-chatbot",
        auto_offset_reset="latest",
    )
    await consumer.start()
    log.info("Chatbot Kafka consumer ready on topic '%s'.", TOPIC_REQUEST)

    try:
        async for msg in consumer:
            data: dict = json.loads(msg.value.decode())
            task_id         = data.get("taskId", "")
            message         = data.get("message", data.get("userMessage", ""))
            conversation_id = data.get("conversationId") or None

            log.info("[kafka] chatbot.request taskId=%s", task_id)
            try:
                # send_message uses a synchronous SQLAlchemy session — run in executor
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    _call_send_message,
                    message,
                    conversation_id,
                )
                ai_text, new_conv_id = result
            except Exception as exc:
                log.error("[kafka] chatbot error taskId=%s: %s", task_id, exc)
                ai_text    = f"AI Agent error: {exc}"
                new_conv_id = str(conversation_id or "")

            response_payload = json.dumps({
                "taskId":         task_id,
                "aiResponse":     ai_text,
                "conversationId": str(new_conv_id),
            }).encode()
            await producer.send_and_wait(TOPIC_RESPONSE, response_payload)
            log.info("[kafka] chatbot.response published taskId=%s", task_id)
    finally:
        await consumer.stop()
        await producer.stop()


def _call_send_message(
    message: str,
    conversation_id: str | None,
) -> tuple[str, str]:
    """Synchronous wrapper around send_message for use in run_in_executor."""
    db = SessionLocal()
    try:
        conversation, _user_msg, ai_msg = send_message(
            db,
            message=message,
            conversation_id=conversation_id,
            authorization=None,   # No bearer token in Kafka context
        )
        return ai_msg.content, str(conversation.id)
    finally:
        db.close()
