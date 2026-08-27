# AGENTS.md — CRM AI Portal

## Arquitetura

Migração de Streamlit monolith para React + FastAPI BFF.

### Backend (FastAPI)
- **Padrão BFF**: agrega dados de Postgres/Redis/Groq/AwesomeAPI para o frontend
- **Repository**: isolamento de acesso a dados via BaseRepository genérico
- **Observer/Pub-Sub**: fan-out de eventos via Redis Pub/Sub
- **DI**: FastAPI Depends() para injeção de dependências
- **Dados nativos**: leads e deals são tabelas Postgres de primeira classe

### Frontend (React)
- **SPA estática**: sem SSR, servida por Nginx
- **State**: React Query (server state), URL params (filtros), Context (auth), local (UI)
- **Design System**: shadcn/ui + Tailwind CSS v4
- **Gráficos**: Recharts (via shadcn/ui pattern)
- **Lazy loading**: rotas carregadas dinamicamente

### Infra
- Docker Compose: frontend (Nginx), backend (FastAPI), Postgres, Redis
- Nginx Proxy Manager: `/api/*` → backend, `/*` → frontend
- Cloudflare CDN na frente

## Convenções

- Backend: Python 3.12, type hints, structlog, Pydantic v2
- Frontend: TypeScript strict, React 19, Tailwind v4
- Commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`
- Testes: pytest (backend), Vitest + RTL (frontend)
- Response envelope: `{ data, error, meta }`
- Erro: `{ data: null, error: { code, message, details } }`
- **Dependências Python**: `backend/requirements.txt` é a fonte de verdade para dependências runtime. `backend/pyproject.toml` é usado apenas para tooling config (pytest, ruff).

## Entidades

| Entidade | Tabela | Descrição |
|----------|--------|-----------|
| `Lead` | `leads` | Contatos do dashboard (nome, email, telefone, status_lead, criado_em) |
| `CapturedLead` | `captured_leads` | Leads capturados via chat/formulário (nome, email, telefone, interesse) |
| `Deal` | `deals` | Negócios (nome, valor, estagio, pipeline, data_close, lead_id FK) |
| `User` | `users` | Usuários do sistema (email, name, google_id, avatar_url, role) |
| `AuditLog` | `audit_logs` | Log de auditoria |

## Endpoints Principais

| Método | Path | Descrição |
|--------|------|-----------|
| GET | /api/v1/health | Health check (Redis, Postgres) |
| GET | /api/v1/dashboard/kpis | KPIs do pipeline |
| GET | /api/v1/dashboard/charts | Dados de gráficos |
| GET | /api/v1/dashboard/deals | Deals paginados |
| GET | /api/v1/dashboard/leads | Leads paginados |
| GET | /api/v1/market/quotes | Cotações de moeda (AwesomeAPI) |
| GET | /api/v1/market/history/{moeda} | Histórico de cotações |
| POST | /api/v1/chat | Chat SSE streaming |
| POST | /api/v1/leads | Captura de lead (público) |
| POST | /api/v1/leads/{id}/convert | Converter lead em deal |
| POST | /api/v1/reports/generate | PDF report |
| GET | /api/v1/auth/login | Google OAuth login URL |
| GET | /api/v1/auth/callback | Google OAuth callback |
| GET | /api/v1/auth/me | Dados do usuário logado |
| POST | /api/v1/auth/logout | Logout (limpa sessão Redis) |

## Cache Strategy

- **Backend**: Redis, TTL 5min (dashboard), 5-15min (AwesomeAPI)
- **Frontend**: React Query, staleTime 5min (dashboard), 1min (market), stale-while-revalidate
- **Invalidação**: explícita em mutações (lead creation → invalida contacts+deals)

## Segurança

- CORS: apenas frontend origin
- Rate limiting: slowapi (100/min global, 10/min LLM, 30/min market)
- CSRF: double-submit cookie (desativado com Cloudflare WAF). Exempt: `/api/v1/auth/callback` (Google não envia CSRF)
- CSP headers: default-src 'self'
- Input validation: Pydantic strict mode
- AwesomeAPI key: apenas no backend, nunca exposta ao frontend
- Auth: sessões Redis com token opaco (TTL 7d), cookie httpOnly + SameSite=Lax. OAuth state param para CSRF no fluxo Google.
- Rotas públicas: `POST /api/v1/leads`, `POST /api/v1/tickets` (bots de captura)

## Decisões de Nomenclatura

- **Lead** = contato listado no dashboard (`LeadResponse` em `models/dashboard.py`, tabela `leads`)
- **CapturedLead** = lead capturado via chat/formulário (`CapturedLeadResponse` em `models/lead.py`, tabela `captured_leads`)
- **Deal** = negócio (`DealResponse` em `models/dashboard.py`, tabela `deals`)
- Frontend usa `LeadResponse` para dashboard e `CapturedLeadResponse` para captura
- Endpoint de listagem: `/dashboard/leads` (não `/dashboard/contacts`)
- Todos os field names do frontend seguem PT-BR do backend (`nome`, `valor`, `estagio`, `telefone`, `status_lead`, `criado_em`)

## API Envelope Pattern

- Backend: `ResponseEnvelope(data=T, error=None, meta={total, page, page_size, total_pages})`
- Frontend interceptor (`api/client.ts`): extrai `data` do envelope, transforma `meta` → `pagination` no response
- Fetchers retornam dados limpos (não o envelope): `fetchKPIs()` → `KPIResponse[]`, `fetchDeals()` → `PaginatedResponse<DealResponse>`
- KPIs: backend retorna array de `KPICardResponse(title, value)` — não objeto flat
