#!/bin/bash
set -e

# Create schemas in main DB (mctrader)
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<-EOSQL
    CREATE SCHEMA IF NOT EXISTS market;
    CREATE SCHEMA IF NOT EXISTS engine;
    CREATE SCHEMA IF NOT EXISTS web;
EOSQL

# Create test DB and schemas (used by pytest integration tests)
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -tc "SELECT 1 FROM pg_database WHERE datname='mctrader_test'" | grep -q 1 \
  || psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -c "CREATE DATABASE mctrader_test;"

psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d mctrader_test <<-EOSQL
    CREATE SCHEMA IF NOT EXISTS market;
    CREATE SCHEMA IF NOT EXISTS engine;
    CREATE SCHEMA IF NOT EXISTS web;
EOSQL
