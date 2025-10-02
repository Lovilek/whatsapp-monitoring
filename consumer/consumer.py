# consumer/consumer.py
import json
from datetime import datetime, timezone
from confluent_kafka import Consumer
import clickhouse_connect
import traceback
import os
from dotenv import load_dotenv

load_dotenv()

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC")
CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT"))
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD")
CLICKHOUSE_DB = os.getenv("CLICKHOUSE_DB")

    

client = clickhouse_connect.get_client(
    host=CLICKHOUSE_HOST, port=CLICKHOUSE_PORT,
    username=CLICKHOUSE_USER, password=CLICKHOUSE_PASSWORD,
    database=CLICKHOUSE_DB
)
try:
    print('DB:', client.query('SELECT currentDatabase()').first_item)
    print('Tables in wa:', client.query('SHOW TABLES FROM wa').result_rows)
    print('DESCRIBE wa.whatsapp_messages:')
    for row in client.query('DESCRIBE TABLE wa.whatsapp_messages').result_rows:
        print(row)
except Exception as e:
    print(e)
    raise

client.command("""
CREATE DATABASE IF NOT EXISTS wa
""")

client.command("""
CREATE TABLE IF NOT EXISTS wa.whatsapp_messages
(
    chat String,
    sender String,
    sender_number String,
    message String,
    timestamp DateTime
)
ENGINE = MergeTree
ORDER BY timestamp
""")

conf = {
    'bootstrap.servers': KAFKA_BROKERS,
    'group.id': 'wa-consumer',
    'auto.offset.reset': 'earliest'
}
consumer = Consumer(conf)
consumer.subscribe([KAFKA_TOPIC])

def parse_ts(p):
    ts_ms = p.get('ts_ms')
    if isinstance(ts_ms, (int, float)):
        return datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
    s = p.get('timestamp')
    if isinstance(s, str) and s:
        if s.endswith('Z'):
            s = s.replace('Z', '+00:00')
        try:
            return datetime.fromisoformat(s)
        except Exception:
            pass
    return datetime.now(timezone.utc)

print("Consumer started...")

while True:
    msg = consumer.poll(1.0)
    if msg is None:
        continue
    if msg.error():
        print("Consumer error:", msg.error())
        continue

    p = json.loads(msg.value().decode('utf-8'))
    ts = parse_ts(p)

    try:
        client.insert(
            "whatsapp_messages",
            [[
                p.get("chat", ""),
                p.get("sender", ""),
                p.get("sender_number", "") or p.get("senderNumber", ""),
                p.get("message", ""),
                ts,  
            ]],
            column_names=["chat", "sender","sender_number", "message", "timestamp"]
        )
        consumer.commit(msg)  
        print("Inserted:", p.get("id"))
    except Exception as e:
        print("❌ ClickHouse insert failed:", e)
        traceback.print_exc()
