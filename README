# WhatsApp → Kafka → ClickHouse → Telegram

Конвейер обработки сообщений: захват сообщений из WhatsApp, обработка через Kafka, сохранение в ClickHouse и пересылка в Telegram.

## Предварительные требования

- Node.js LTS (v18+)
- Python 3.10+
- Docker + Docker Compose
- Telegram бот (получить токен через @BotFather)
- Chat ID получателя уведомлений в Telegram

## Конфигурация

Создайте файл `.env` со следующим содержимым:

```ini
KAFKA_BROKERS=localhost:29092
KAFKA_CLIENT_ID=whatsapp-producer
KAFKA_TOPIC=whatsapp.messages
KAFKA_SSL=false
TELEGRAM_BOT_TOKEN=YOUR_TOKEN
TELEGRAM_CHAT_ID=YOUR_CHAT_ID
WA_CLIENT_ID=main
LOG_LEVEL=info
```

## Установка

### 1. Настройка WhatsApp Producer
```bash
cd producer
npm init -y
npm install
```

### 2. Настройка сервиса Speech-to-Text
```bash
cd producer/stt
python -m venv venv
venv\scripts\activate
pip install -r requirements.txt

# Установка FFmpeg (Windows)
winget install Gyan.FFmpeg
# или
winget install ffmpeg
```

### 3. Настройка Consumer
```bash
cd consumer
python -m venv venv
venv\scripts\activate
pip install -r requirements.txt
```

## Запуск системы

Необходимо запустить несколько компонентов в отдельных терминалах:

### Терминал 1: Инфраструктура и Producer
```bash
# Запуск Kafka и ClickHouse
docker compose up -d

# Создание топика в Kafka
node producer/scripts/create-topic.js

# Запуск WhatsApp producer
node producer/src/whatsapp_producer.js
```
При первом запуске необходимо отсканировать QR-код в WhatsApp.

### Терминал 2: Сервис Speech-to-Text
```bash
cd producer/stt
venv\scripts\activate
python stt_server.py
```

### Терминал 3: Kafka Consumer
```bash
cd consumer
venv\scripts\activate
python consumer.py
```

### Терминал 4: Telegram Filter
```bash
cd consumer
venv\scripts\activate
python filter-tg.py
```

## Структура проекта

```
.
├── producer/                      # WhatsApp Producer сервис
│   ├── src/
│   │   ├── kafka.js             # Конфигурация и методы для Kafka
│   │   ├── schema.js            # Схема сообщений
│   │   └── whatsapp_producer.js # Основной код producer'а
│   ├── stt/
│   │   ├── stt_server.py        # Преобразование аудио в текст  
│   |   └── requirements.txt     # Python зависимости
|   |
│   ├── scripts/
│   │   └── create-topic.js      # Скрипт создания Kafka топика
│   └── package.json             # Зависимости Node.js
│
├── consumer/                     # Consumer и Telegram сервис
│   ├── consumer.py              # Основной Kafka consumer
│   ├── filter-tg.py             # Telegram бот и фильтры
│   └── requirements.txt         # Python зависимости
│
├── docker-compose.yml           # Конфигурация Docker контейнеров
├── .env                        # Переменные окружения
└── README.md                   # Документация проекта

## Мониторинг

- Kafka UI: http://localhost:8080
- ClickHouse: http://localhost:8123

