import { Kafka, Partitioners, logLevel } from 'kafkajs';

const brokers = (process.env.KAFKA_BROKERS || 'localhost:29092').split(',');
const clientId = process.env.KAFKA_CLIENT_ID || 'whatsapp-producer';

const kafka = new Kafka({
    clientId,
    brokers,
    logLevel: logLevel.NOTHING,
    ssl: process.env.KAFKA_SSL === 'true' ? {} : undefined,
    sasl: process.env.KAFKA_SASL_MECHANISM ? {
        mechanism: process.env.KAFKA_SASL_MECHANISM,
        username: process.env.KAFKA_SASL_USERNAME,
        password: process.env.KAFKA_SASL_PASSWORD,
    } : undefined,
});

export const producer = kafka.producer({
    createPartitioner: Partitioners.DefaultPartitioner,
    allowAutoTopicCreation: false,
    idempotent: true, 
    retry: { retries: 10 }
});

export async function connectProducer(logger) {
    await producer.connect();
    logger.info({ brokers }, 'Kafka producer connected');
}

export async function sendMessage({ topic, key, value }) {
    return producer.send({
        topic,
        messages: [{ key, value }],
        acks: -1,
    });
}

export async function disconnectProducer(logger) {
    try {
        await producer.disconnect();
    } catch (e) {
        logger.error(e, 'Kafka producer disconnect error');
    }
}