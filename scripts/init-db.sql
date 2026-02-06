-- Initialize database with basic setup
-- This script runs when the PostgreSQL container starts for the first time

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create database user if not exists (for production)
-- DO $$ 
-- BEGIN
--     IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'ml_platform_user') THEN
--         CREATE ROLE ml_platform_user WITH LOGIN PASSWORD 'secure_password';
--     END IF;
-- END
-- $$;

-- Grant permissions
-- GRANT ALL PRIVILEGES ON DATABASE ml_platform TO ml_platform_user;