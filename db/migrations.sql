-- ================================
-- USERS
-- ================================
CREATE TABLE IF NOT EXISTS users (
    user_id        BIGINT PRIMARY KEY,
    username       VARCHAR(64),
    coins          BIGINT DEFAULT 0,

    total_games    INT DEFAULT 0,
    wins           INT DEFAULT 0,
    losses         INT DEFAULT 0,

    daily_claim_at TIMESTAMP,
    is_banned      BOOLEAN DEFAULT FALSE,

    created_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- ================================
-- MATCHES
-- ================================
CREATE TABLE IF NOT EXISTS matches (
    id           SERIAL PRIMARY KEY,
    room_id      VARCHAR(64),

    players      BIGINT[],
    winners      BIGINT[],

    entry_fee    BIGINT,
    total_pot    BIGINT,
    bonus        BIGINT,

    started_at   TIMESTAMPTZ,
    ended_at     TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_matches_room ON matches(room_id);

-- ================================
-- TRANSACTIONS (COIN LOGS)
-- ================================
CREATE TABLE IF NOT EXISTS transactions (
    id          SERIAL PRIMARY KEY,
    user_id     BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    amount      BIGINT NOT NULL,
    reason      TEXT,

    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id);

-- ================================
-- PENALTIES
-- ================================
CREATE TABLE IF NOT EXISTS penalties (
    id              SERIAL PRIMARY KEY,
    user_id         BIGINT,
    reason          TEXT,
    coins_deducted  BIGINT DEFAULT 0,
    banned_until    TIMESTAMPTZ,

    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_penalties_user ON penalties(user_id);
