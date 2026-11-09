# SalesVoice AI

An AI-powered sales coaching platform built with a microservices architecture. It helps sales teams track leads, analyse calls, and get real-time coaching suggestions.

## Quick Start

```bash
# Clone and start everything (Docker Desktop required)
git clone https://github.com/<your-username>/salesvoice-ai.git
cd salesvoice-ai
cp .env.example .env        # then fill in real secrets
docker compose -f infra/docker-compose.yml --env-file .env up --build -d
```

The API gateway is available at **http://localhost:8000**. Interactive docs at http://localhost:8000/docs.

## Useful Commands

| Command | What it does |
|---------|-------------|
| `docker compose -f infra/docker-compose.yml --env-file .env up --build -d` | Build and start everything |
| `docker compose -f infra/docker-compose.yml --env-file .env ps` | Status of every container |
| `docker compose -f infra/docker-compose.yml --env-file .env logs -f gateway` | Follow one service's logs |
| `docker compose -f infra/docker-compose.yml --env-file .env down` | Stop containers (data kept) |
| `docker compose -f infra/docker-compose.yml --env-file .env down -v` | Stop and delete all data |

## Architecture

- **Gateway** — single entry point, JWT verification, rate limiting, request routing
- **Auth service** — signup, login, token refresh, user management
- **PostgreSQL** (pgvector) — database with per-service schema isolation
- **Redis** — rate limiting and caching

## Build Roadmap

- [x] **Build 1** — Auth service, API gateway, Docker infrastructure
- [ ] **Build 2** — Leads service (CRUD, pipeline stages, assignment)
- [ ] **Build 3** — Knowledge base service (RAG with vector search)
- [ ] **Build 4** — Calls service (transcription, analysis, coaching)
- [ ] **Build 5** — Frontend (Next.js dashboard)
- [ ] **Build 6** — Production deployment
