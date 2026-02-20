ALTER TABLE users
ADD COLUMN IF NOT EXISTS firebase_uid TEXT UNIQUE;

CREATE INDEX IF NOT EXISTS idx_users_firebase_uid
ON users(firebase_uid);

-- (Optionnel mais recommandé)
ALTER TABLE users
ADD COLUMN IF NOT EXISTS email TEXT,
ADD COLUMN IF NOT EXISTS display_name TEXT,
ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now(),
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();
