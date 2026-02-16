# Superhuman Alpha Fund

An autonomous, multi-agent investment analysis system structured as an AI-driven hedge fund. Teams of AI analyst agents analyze SEC filings, earnings transcripts, financial data, and market sentiment, surfacing investment decisions through a hierarchical supervisor chain (Sector Analysts -> Sector Supervisors -> CIO -> CEO). A browser-based dashboard lets a human operator supervise every decision.

## Architecture

```
Frontend (React + TypeScript)
    |
    v
Backend (FastAPI + WebSocket)
    |
    ├── Agent Hierarchy (LangGraph + Anthropic Claude)
    │     CEO
    │     ├── CIO
    │     │   ├── Sector Supervisor A (Tech, Healthcare, Financials)
    │     │   ├── Sector Supervisor B (Energy, Consumer, Industrials, RE, Utilities)
    │     │   ├── Fixed Income Team (Bond, Credit, Rate analysts)
    │     │   └── Macro Team (Macro, Geopolitical analysts)
    │     └── Risk Manager (veto authority)
    │
    ├── Celery Workers (scheduled analysis, data refresh)
    ├── PostgreSQL (portfolio, reports, decisions, market data)
    ├── ChromaDB (vector store for filings/transcripts)
    └── Redis (task queue, caching)
```

## Prerequisites

- **Docker** and **Docker Compose** (recommended) — OR —
- **Python 3.11+**, **Node.js 20+**, **PostgreSQL 16**, **Redis 7**, **ChromaDB**

### API Keys Required

| Key | Source | Purpose |
|-----|--------|---------|
| `ANTHROPIC_API_KEY` | [Anthropic Console](https://console.anthropic.com/) | Claude LLM for all agents |
| `FMP_API_KEY` | [Financial Modeling Prep](https://financialmodelingprep.com/) | Financial data, ratios, DCF |
| `SEC_USER_AGENT` | Your name + email | SEC EDGAR API (required by SEC) |

Optional: `NEWSAPI_KEY`, `ALPHA_VANTAGE_KEY` for additional data sources.

## Quick Start (Docker)

### 1. Clone and configure

```bash
git clone <repo-url> && cd investment-agent
cp .env.example .env
```

Edit `.env` with your API keys:

```env
ANTHROPIC_API_KEY=sk-ant-...
FMP_API_KEY=...
SEC_USER_AGENT=YourName you@example.com

# Security — change these in production
DB_PASSWORD=superhuman_secure_password_change_me
JWT_SECRET=change_this_to_a_random_string
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change_me
```

### 2. Start all services

```bash
docker compose up -d
```

This starts 7 services:

| Service | Port | Description |
|---------|------|-------------|
| `frontend` | [localhost:3000](http://localhost:3000) | React dashboard |
| `backend` | [localhost:8080](http://localhost:8080) | FastAPI + WebSocket |
| `db` | 5432 | PostgreSQL 16 |
| `redis` | 6379 | Redis 7 |
| `chromadb` | 8100 | ChromaDB vector store |
| `celery_worker` | — | Background task workers |
| `celery_beat` | — | Scheduled task scheduler |

### 3. Initialize the database

```bash
docker compose exec backend python -c "
from app.database import Base, engine
import app.models
import asyncio
async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(init())
"
```

Or from the repo root (if running locally):

```bash
python scripts/setup_db.py
```

### 4. Open the dashboard

Navigate to [http://localhost:3000](http://localhost:3000). Log in with the credentials you set in `.env` (`admin` / `change_me` by default).

## Local Development (without Docker)

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Start PostgreSQL, Redis, ChromaDB (via Docker or natively)
docker compose up -d db redis chromadb

# Run migrations and seed data
cd .. && python scripts/setup_db.py && cd backend

# Start the API server
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# In separate terminals:
celery -A app.celery_app worker -l info -c 4 -Q default,analysis,data
celery -A app.celery_app beat -l info --scheduler celery.beat:PersistentScheduler
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server starts at [http://localhost:5173](http://localhost:5173) and proxies `/api` requests to the backend at port 8080.

### Running Tests

```bash
cd backend
pip install -e ".[dev]"
pytest tests/ -v
```

Tests use an in-memory SQLite database — no running PostgreSQL required.

## Project Structure

```
investment-agent/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Environment configuration
│   │   ├── database.py          # SQLAlchemy async engine + session
│   │   ├── celery_app.py        # Celery configuration + beat schedules
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── api/                 # FastAPI routers (auth, portfolio, reports, agents, chat, settings, websocket)
│   │   ├── services/            # Business logic (chat router, intent classification)
│   │   ├── agents/
│   │   │   ├── tools/           # LangChain @tool functions (market, SEC, portfolio, fundamental, report, sentiment)
│   │   │   ├── analysts/        # 8 sector team factories + fixed income + macro agents
│   │   │   ├── supervisors/     # Sector, FI, macro supervisors + CIO + risk manager
│   │   │   ├── ceo_agent.py     # CEO agent with trade execution
│   │   │   └── orchestrator.py  # 3 execution modes (full, targeted, review)
│   │   └── tasks/               # Celery tasks (data refresh, filing monitor, analysis cycle, cleanup)
│   ├── alembic/                 # Database migrations
│   ├── tests/                   # pytest test suite (94 tests)
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── pages/               # Dashboard, Portfolio, Agents, Reports, Chat, Settings
│   │   ├── components/          # UI components organized by feature
│   │   ├── store/               # Zustand state stores
│   │   ├── hooks/               # React hooks (WebSocket, portfolio, agents)
│   │   ├── lib/                 # API client, WebSocket client, utilities
│   │   └── types/               # TypeScript interfaces
│   ├── package.json
│   └── vite.config.ts
├── scripts/
│   ├── setup_db.py              # Database initialization + seeding
│   └── seed_universe.py         # Stock universe definition (50 stocks across 8 sectors)
├── docker-compose.yml
└── specifications.md            # Complete technical specification
```

## Usage

### Dashboard

The main dashboard shows:
- **Portfolio summary** — total value, cash balance, daily P&L, allocation breakdown
- **Performance chart** — historical portfolio returns
- **Agent status grid** — real-time status of all agents in the hierarchy
- **Recent decisions** — latest trade decisions with reasoning

### Agents Page

View the full agent hierarchy tree. Click any agent to see its details, recent reports, and current status. Trigger targeted analysis runs for specific agents.

### Reports Page

Browse all analysis reports produced by agents. Filter by sector, agent, date range, or report type. View the full decision trail showing how information flowed from analyst reports up through supervisors to the CEO's final decision.

### Chat

Natural language interface to interact with the fund. Example queries:
- "What's our current exposure to tech?"
- "Run analysis on AAPL"
- "Set aggressiveness to 7"
- "Why did we buy MSFT last week?"
- "What's the risk score on our portfolio?"

The chat router classifies intent and routes to the appropriate handler (portfolio query, analysis trigger, settings change, decision query, etc.).

### Settings

- **Risk profile** — aggressiveness (1-10), target allocation (equity/fixed income/cash)
- **Position limits** — max single position %, max sector %, min cash reserve %
- **Watch list** — symbols tracked for analysis
- **Scheduled tasks** — view and manually trigger analysis cycles

## Hard Constraints

The system enforces these rules at every level:
- No margin trading, no leverage, no short selling
- Cash balance can never go negative
- Single position cannot exceed the configured max (default 5%)
- Sector allocation cannot exceed the configured max (default 25%)
- Minimum cash reserve must be maintained (default 5%)
- Every trade decision must have a recorded analysis report and decision trail

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | Anthropic API key (required) |
| `FMP_API_KEY` | — | Financial Modeling Prep key (required) |
| `SEC_USER_AGENT` | `Superhuman Alpha Fund admin@yourdomain.com` | SEC EDGAR identification |
| `DATABASE_URL` | `postgresql+asyncpg://superhuman:superhuman@localhost:5432/superhuman_alpha_fund` | PostgreSQL connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `CHROMA_HOST` | `localhost` | ChromaDB host |
| `CHROMA_PORT` | `8100` | ChromaDB port |
| `JWT_SECRET` | `change_this_to_a_random_string` | JWT signing secret |
| `JWT_EXPIRE_MINUTES` | `1440` | JWT token expiry (24h) |
| `ADMIN_USERNAME` | `admin` | Login username |
| `ADMIN_PASSWORD` | `change_me` | Login password |
| `INITIAL_CASH_BALANCE` | `100000` | Starting portfolio cash ($) |
| `DEFAULT_AGGRESSIVENESS` | `5` | Default risk aggressiveness (1-10) |
| `DB_PASSWORD` | `superhuman_secure_password_change_me` | PostgreSQL password (Docker) |
| `BACKEND_PORT` | `8080` | Backend API port |
| `FRONTEND_PORT` | `3000` | Frontend port |

## License

Proprietary. All rights reserved.
