-- ================================
-- USERS
-- ================================
CREATE TABLE IF NOT EXISTS users (
    user_id            BIGINT PRIMARY KEY,
    username           VARCHAR(64),

    coins              BIGINT NOT NULL DEFAULT 0,

    total_games        INT NOT NULL DEFAULT 0,
    wins               INT NOT NULL DEFAULT 0,
    losses             INT NOT NULL DEFAULT 0,

    daily_claim_at     TIMESTAMPTZ,

    -- Anti-cheat / moderation
    cheat_strikes      INT NOT NULL DEFAULT 0,
    last_cheat_reason  TEXT,
    last_cheat_at      TIMESTAMPTZ,

    is_banned          BOOLEAN NOT NULL DEFAULT FALSE,
    ban_until          TIMESTAMPTZ,

    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- ================================
-- MATCHES
-- ================================
CREATE TABLE IF NOT EXISTS matches (
    id           SERIAL PRIMARY KEY,
    room_id      VARCHAR(64) NOT NULL,

    players      BIGINT[] NOT NULL,
    winners      BIGINT[] NOT NULL,

    entry_fee    BIGINT NOT NULL,
    total_pot    BIGINT NOT NULL,
    bonus        BIGINT NOT NULL,

    started_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at     TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_matches_room ON matches(room_id);

-- ================================
-- TRANSACTIONS (COIN LOGS)
-- ================================
CREATE TABLE IF NOT EXISTS transactions (
    id          SERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    amount      BIGINT NOT NULL,
    reason      TEXT,

    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id);

-- ================================
-- PENALTIES (AUDIT LOG)
-- ================================
CREATE TABLE IF NOT EXISTS penalties (
    id              SERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL,
    reason          TEXT NOT NULL,
    coins_deducted  BIGINT NOT NULL DEFAULT 0,
    banned_until    TIMESTAMPTZ,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_penalties_user ON penalties(user_id);
