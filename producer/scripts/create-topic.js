import { Kafka } from 'kafkajs';
import { fileURLToPath } from 'url';
import path from 'path';
import dotenv from 'dotenv';
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.resolve(__dirname, '../../.env') });
const brokers = process.env.KAFKA_BROKERS.split(',');
const topic = process.env.KAFKA_TOPIC;

const kafka = new Kafka({ brokers, clientId: 'wa-topic-admin' });
const admin = kafka.admin();

(async () => {
    await admin.connect();
    const topics = await admin.listTopics();

    if (!topics.includes(topic)) {
        await admin.createTopics({
            topics: [{
                topic,
                numPartitions: 6, 
                replicationFactor: 1, 
                configEntries: [
                    { name: 'cleanup.policy', value: 'delete' },
                    { name: 'retention.ms', value: String(7 * 24 * 60 * 60 * 1000) },
                    { name: 'max.message.bytes', value: '10485760' }
                ]
            }]
        });
        console.log(`Topic created: ${topic}`);
    } else {
        console.log(`Topic exists: ${topic}`);
    }

    await admin.disconnect();
    process.exit(0);
})().catch(async (e) => {
    console.error(e);
    try { 
        await admin.disconnect(); 
    } catch {}
    process.exit(1);
});