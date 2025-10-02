import asyncio
import os
import re
import orjson
from contextlib import asynccontextmanager

from aiokafka import AIOKafkaConsumer
from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:29092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "whatsapp.messages")

TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "952628629"))

NEGATIVE_WORDS = [
    "проблема", "жалоба", "ненавижу", "плохо", "недоволен",
]
NEGATIVE_RE = re.compile(rf"\b({'|'.join(map(re.escape, NEGATIVE_WORDS))})\b", re.IGNORECASE | re.UNICODE)

def is_negative(text: str | None) -> bool:
    if not text:
        return False
    return bool(NEGATIVE_RE.search(text.lower()))

@asynccontextmanager
async def make_consumer():
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BROKERS,
        enable_auto_commit=False,         
        auto_offset_reset="latest",       
        value_deserializer=lambda v: v,   
    )
    await consumer.start()
    try:
        yield consumer
    finally:
        await consumer.stop()

async def send_alert(bot: Bot, payload: dict):
    if not TG_TOKEN or not TG_CHAT_ID:
        print("[WARN] Telegram creds are not set; skip sending")
        return
    text = (
        "🚨 Негативное сообщение\n"
        f"Чат: {payload.get('chat','-')}\n"
        f"От: {payload.get('sender','-')}\n"
        f"Текст: {payload.get('message','')}"
    )
    await bot.send_message(chat_id=TG_CHAT_ID, text=text)

async def run():
    bot = Bot(token=TG_TOKEN)
    async with make_consumer() as consumer:
        print(f"[neg-alerts] aiogram online. topic={KAFKA_TOPIC}")
        try:
            async for msg in consumer:
                try:
                    payload = orjson.loads(msg.value)
                except Exception as e:
                    print("[WARN] JSON parse error:", e)
                    continue

                if is_negative(payload.get("message")):
                    await send_alert(bot, payload)
        finally:
            await bot.session.close()

def main():
    asyncio.run(run())

if __name__ == "__main__":
    main()
