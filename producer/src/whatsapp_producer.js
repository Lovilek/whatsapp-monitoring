import pino from 'pino';
import pkg from 'whatsapp-web.js';
const { Client, LocalAuth, MessageTypes } = pkg;
import QRCode from 'qrcode-terminal';
import { connectProducer, sendMessage, disconnectProducer } from './kafka.js';
import { toCanonicalPayload } from './schema.js';
import fetch from 'node-fetch'; 

const logger = pino({ level: process.env.LOG_LEVEL || 'info' });
const topic = process.env.KAFKA_TOPIC || 'whatsapp.messages';
const waClientId = process.env.WA_CLIENT_ID || 'main';
const STT_URL = process.env.STT_URL || 'http://localhost:9009/transcribe';

const wa = new Client({
  authStrategy: new LocalAuth({ clientId: waClientId }),
  puppeteer: { headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox'] }
});

wa.on('qr', (qr) => {
  logger.warn('Scan this QR with WhatsApp to authenticate:');
  QRCode.generate(qr, { small: true });
});
wa.on('ready', () => logger.info('WhatsApp client ready'));
wa.on('authenticated', () => logger.info('WhatsApp authenticated'));
wa.on('auth_failure', (m) => logger.error({ msg: m }, 'WhatsApp auth failure'));
wa.on('disconnected', (r) => logger.warn({ reason: r }, 'WhatsApp disconnected'));

await connectProducer(logger);
wa.initialize();

async function transcribeAudio({ audioBase64, mime }) {
  const res = await fetch(STT_URL, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ audio_base64: audioBase64, mime }),
    timeout: 120000,
  });
  if (!res.ok) throw new Error(`STT HTTP ${res.status}`);
  return await res.json(); 
}

wa.on('message', async (msg) => {
  try {
    const chat = await msg.getChat();
    const contact = await msg.getContact();

    const baseFields = {
      messageId: msg.id._serialized,
      chatId: chat.id._serialized,
      chatName: chat.name || chat.formattedTitle || chat.id.user || 'unknown',
      senderId: contact.id._serialized,
      senderName: contact.pushname || contact.name || contact.number || 'unknown',
      senderNumber: contact.number,
      timestampMs: (msg.timestamp || Math.floor(Date.now() / 1000)) * 1000,
      isGroup: chat.isGroup,
      type: msg.type,
    };

    
    if (msg.type === MessageTypes.TEXT || msg.type === 'chat') {
      const body = (msg.body || '').trim();
      if (!body) return; 
      const payload = toCanonicalPayload({ ...baseFields, body });
      await sendMessage({ topic, key: payload.id, value: JSON.stringify(payload) });
      logger.debug({ id: payload.id }, 'Produced WA text message');
      return;
    }

    if (msg.type === MessageTypes.AUDIO || msg.type === MessageTypes.PTT || msg.type === 'audio' || msg.type === 'ptt') {
      const media = await msg.downloadMedia(); 
      if (!media?.data) {
        const payload = toCanonicalPayload({ ...baseFields, body: '' });
        await sendMessage({ topic, key: payload.id, value: JSON.stringify(payload) });
        logger.debug({ id: payload.id }, 'Produced WA audio message without media data');
        return;
      }

      let transcriptText = '';
      try {
        const stt = await transcribeAudio({ audioBase64: media.data, mime: media.mimetype || 'audio/ogg' });
        transcriptText = (stt.text || '').trim();
      } catch (e) {
        logger.error(e, 'STT error');
      }

      const payload = toCanonicalPayload({ ...baseFields, body: transcriptText });
      await sendMessage({ topic, key: payload.id, value: JSON.stringify(payload) });
      logger.debug({ id: payload.id }, 'Produced WA audio message');
      return;
    }

  } catch (e) {
    logger.error(e, 'Error handling WA message');
  }
});

async function shutdown() {
  logger.info('Shutting down...');
  try { await wa.destroy(); } catch {}
  await disconnectProducer(logger);
  process.exit(0);
}
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
