-- =============================================================
-- Covenexa — PostgreSQL Initialization Script
-- Runs once when the PostgreSQL container starts for the first time.
-- =============================================================

-- Enable UUID generation extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgcrypto for password hashing utilities
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enable citext for case-insensitive text (emails)
CREATE EXTENSION IF NOT EXISTS "citext";

-- Confirm setup
DO $$
BEGIN
    RAISE NOTICE 'Covenexa database initialized successfully.';
    RAISE NOTICE 'Extensions: uuid-ossp, pgcrypto, citext enabled.';
END $$;
