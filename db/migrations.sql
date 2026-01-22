SET search_path TO public;

DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS penalties CASCADE;
DROP TABLE IF EXISTS matches CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- USERS
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(64),
    coins BIGINT NOT NULL DEFAULT 0,
    total_games INT NOT NULL DEFAULT 0,
    wins INT NOT NULL DEFAULT 0,
    losses INT NOT NULL DEFAULT 0,
    daily_claim_at TIMESTAMPTZ,
    cheat_strikes INT NOT NULL DEFAULT 0,
    last_cheat_reason TEXT,
    last_cheat_at TIMESTAMPTZ,
    is_banned BOOLEAN NOT NULL DEFAULT FALSE,
    ban_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    room_id VARCHAR(64) NOT NULL,
    players BIGINT[] NOT NULL,
    winners BIGINT[] NOT NULL,
    entry_fee BIGINT NOT NULL,
    total_pot BIGINT NOT NULL,
    bonus BIGINT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ
);

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    amount BIGINT NOT NULL,
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE penalties (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    reason TEXT NOT NULL,
    coins_deducted BIGINT NOT NULL DEFAULT 0,
    banned_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
