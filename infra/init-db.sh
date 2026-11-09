#!/bin/sh
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<SQL
CREATE EXTENSION IF NOT EXISTS vector;
REVOKE ALL ON SCHEMA public FROM PUBLIC;

CREATE ROLE auth_svc LOGIN PASSWORD '${AUTH_DB_PASSWORD}';
CREATE SCHEMA auth AUTHORIZATION auth_svc;
ALTER ROLE auth_svc SET search_path = auth;

CREATE ROLE leads_svc LOGIN PASSWORD '${LEADS_DB_PASSWORD}';
CREATE SCHEMA leads AUTHORIZATION leads_svc;
ALTER ROLE leads_svc SET search_path = leads;

CREATE ROLE knowledge_svc LOGIN PASSWORD '${KNOWLEDGE_DB_PASSWORD}';
CREATE SCHEMA knowledge AUTHORIZATION knowledge_svc;
GRANT USAGE ON SCHEMA public TO knowledge_svc;
ALTER ROLE knowledge_svc SET search_path = knowledge;
SQL
