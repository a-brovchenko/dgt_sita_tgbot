CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    telegram_chat_id BIGINT,
    nickname VARCHAR(255),
    language TEXT,
    region VARCHAR(20) DEFAULT NULL,
    payment_method VARCHAR(255) DEFAULT NULL
  );
