# CRM AI Portal

Portal CRM com dashboard analítico, chat com IA e captura de leads, integrado ao HubSpot.

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Frontend | React 19 + TypeScript + Vite + Tailwind CSS v4 + shadcn/ui |
| Backend | FastAPI (async) + Python 3.12 |
| Database | PostgreSQL 16 + SQLAlchemy async + Alembic |
| Cache | Redis 7 |
| AI/LLM | LangChain + Groq (Llama 3.3 70B) |
| CRM | HubSpot REST API |
| Deploy | Docker Compose + Nginx Proxy Manager + Cloudflare |

## Estrutura

```
├── backend/           # FastAPI BFF
│   ├── app/
│   │   ├── api/v1/    # Endpoints REST
│   │   ├── models/    # Pydantic contracts
│   │   ├── entities/  # SQLAlchemy ORM
│   │   ├── repositories/  # Data access
│   │   ├── services/  # Business logic
│   │   ├── events/    # Redis Pub/Sub fan-out
│   │   ├── cache/     # Redis cache layer
│   │   ├── auth/      # Google OAuth
│   │   ├── middleware/ # Security, logging, rate limit
│   │   └── observability/ # Sentry, metrics, health
│   ├── templates/     # Jinja2 PDF templates
│   └── tests/         # pytest
├── frontend/          # React SPA
│   └── src/
│       ├── api/       # API client
│       ├── components/ # shadcn/ui + layout
│       ├── features/  # Dashboard, Chat, Leads, Reports, Auth
│       ├── hooks/     # React Query hooks
│       └── test/      # Vitest + MSW
└── docker-compose.yml # 4 services: frontend, backend, postgres, redis
```

## Setup

```bash
cp .env.example .env
# Editar .env com suas credenciais

docker compose up -d
# Frontend: http://localhost:8502
# Backend API: http://localhost:8000/api/docs
```

## Desenvolvimento Local

```bash
# 1. Subir dependências (Postgres + Redis)
#    A rede rede_vps é criada automaticamente pelo docker-compose.override.yml
docker compose up -d redis postgres

# 2. Configurar backend/.env
#    DATABASE_URL e REDIS_URL apontam para localhost (não nomes de serviço)
#    DATABASE_URL=postgresql+asyncpg://postgres:123@localhost:5433/postgres
#    REDIS_URL=redis://localhost:6380/0

# 3. Rodar backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# 4. Rodar frontend (em outro terminal)
cd frontend
npm install
npm run dev
```

## Testes

```bash
# Backend
cd backend && pytest tests/ -v

# Frontend
cd frontend && npm test
```

## Deploy

```bash
./deploy.sh
```

## API

- `GET /api/v1/health` — Health check detalhado
- `GET /api/v1/dashboard/kpis` — KPIs do pipeline
- `GET /api/v1/dashboard/charts` — Dados para gráficos
- `GET /api/v1/dashboard/deals` — Deals paginados
- `GET /api/v1/dashboard/leads` — Leads paginados
- `POST /api/v1/chat` — Chat analítico (SSE streaming)
- `POST /api/v1/leads` — Captura de lead + fan-out (público)
- `POST /api/v1/leads/{id}/convert` — Converter lead em deal
- `POST /api/v1/reports/generate` — Gerar PDF
- `POST /api/v1/reports/csv-upload` — Análise de CSV
- `GET /api/v1/auth/login` — Google OAuth login URL
- `GET /api/v1/auth/callback` — Google OAuth callback
- `GET /api/v1/auth/me` — Dados do usuário logado
- `POST /api/v1/auth/logout` — Logout (limpa sessão Redis)

## Variáveis de Ambiente

| Variável | Descrição | Default |
|----------|-----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:123@localhost:5433/postgres` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6380/0` |
| `GROQ_API_KEY` | API key do Groq (LLM) | — |
| `GROQ_MODEL` | Modelo do Groq | `llama-3.3-70b-versatile` |
| `GOOGLE_CLIENT_ID` | Client ID do Google OAuth | — |
| `GOOGLE_CLIENT_SECRET` | Client Secret do Google OAuth | — |
| `GOOGLE_REDIRECT_URI` | Redirect URI do OAuth | — |
| `SESSION_TTL_SECONDS` | TTL da sessão Redis (segundos) | `604800` (7 dias) |
| `SECRET_KEY` | Chave secreta da aplicação | `change-me-in-production` |
| `APP_ENV` | Ambiente (`development`/`production`/`cloudflare`) | `development` |
| `FRONTEND_ORIGIN` | Origin do frontend (CORS) | `http://localhost:5173` |
| `SENTRY_DSN` | DSN do Sentry (opcional) | — |
