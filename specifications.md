Superhuman Alpha Fund — Autonomous Investment Analysis System
Complete Technical Specification
Purpose: This document is the single source of truth for building Superhuman Alpha Fund. Claude Code should read this file in its entirety before writing any code. Follow the implementation order exactly. Every architectural decision, file path, data model, agent definition, and UI requirement is specified below. Do not deviate from this spec without explicit human approval.

Table of Contents
System Overview

Tech Stack

Project Structure

Database Schema

Agent Architecture

Agent Tools

Agent Definitions

Orchestrator

Data Ingestion & Scheduling

Backend API

Natural Language Chat Interface

Frontend Application

Infrastructure & Deployment

Environment Configuration

Data Management Policies

Testing Strategy

Implementation Order

Hard Constraints

Stretch Goals

1. System Overview
Superhuman Alpha Fund is a human-supervised, multi-agent investment analysis system structured as an automated hedge fund. It is research-intensive and fundamentals-driven — NOT a high-frequency trading system.

Core Concept

Teams of AI analyst agents organized by market sector analyze SEC filings (10-K, 10-Q), earnings call transcripts, financial data, and market sentiment

A hierarchical tree of supervisor agents aggregates findings upward through sector supervisors → CIO → CEO

Every agent produces persistent analysis reports with full reasoning chains

A top-level CEO agent makes final investment decisions backed by the full report tree

A human operator supervises via a browser-based dashboard, can interrogate any decision, and can adjust portfolio parameters using natural language

The system runs continuously on a configurable schedule, practicing good data management and retention

What This System IS

A team of specialized AI agents performing deep fundamental analysis

An automated research and recommendation engine

A transparent decision-making system where every conclusion is traceable to source data

A tool that augments human investment judgment

What This System IS NOT

A high-frequency trading bot

An autonomous system that trades without human awareness

A system that uses leverage, margin, or short selling in any form

2. Tech Stack
All technology choices are final. Do not substitute alternatives.

Layer	Technology	Version/Notes
Language	Python	3.12+
Agent Framework	LangGraph + langgraph-supervisor	For hierarchical multi-agent graphs
LLM Provider	Anthropic Claude	claude-sonnet-4-20250514 via langchain-anthropic
Backend API	FastAPI	With async support and WebSocket
Frontend	React + TypeScript	Vite bundler, React 18+
UI Framework	TailwindCSS + shadcn/ui	
State Management	Zustand	Frontend state
Database	PostgreSQL 16	Via asyncpg + SQLAlchemy 2.0 async
Vector Store	ChromaDB	Document embeddings for filing semantic search
Task Queue	Celery	Redis broker
Cache	Redis 7	API response caching, rate limiting, Celery broker
Market Data	yfinance	Price, volume, fundamentals
SEC Filings	SEC EDGAR EFTS API	Direct HTTP, respect 10 req/sec + User-Agent
Earnings Transcripts	financialmodelingprep API	Free tier for transcripts + fundamentals
Sentiment (Social)	pyfin-sentiment	Bullish/Bearish/Neutral classification
Sentiment (News)	FinBERT via transformers	Financial news NLP
Charts (Backend)	Plotly	For report generation
Charts (Frontend)	Recharts	Interactive portfolio charts
Auth	JWT (python-jose + passlib)	Single-user, self-hosted
Containerization	Docker Compose	Full stack orchestration
Logging	structlog	Structured JSON logging throughout
Python Dependencies (backend pyproject.toml)

text
dependencies = [
    "fastapi[standard]>=0.115",
    "uvicorn[standard]>=0.34",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.30",
    "alembic>=1.14",
    "celery[redis]>=5.4",
    "redis>=5.0",
    "chromadb>=0.5",
    "langchain-anthropic>=0.3",
    "langgraph>=0.2",
    "langgraph-supervisor>=0.0.7",
    "langchain-core>=0.3",
    "yfinance>=0.2",
    "httpx>=0.28",
    "pyfin-sentiment>=0.2",
    "transformers>=4.47",
    "torch>=2.5",
    "beautifulsoup4>=4.12",
    "lxml>=5.3",
    "pydantic>=2.10",
    "pydantic-settings>=2.7",
    "python-jose[cryptography]>=3.3",
    "passlib[bcrypt]>=1.7",
    "plotly>=5.24",
    "structlog>=24.4",
    "tenacity>=9.0",
    "python-multipart>=0.0.18",
]
3. Project Structure
Create this exact directory tree. Every file listed must be created.

text
Superhuman Alpha-fund/
├── CLAUDE.md                       # Points Claude Code to this spec
├── specifications.md               # THIS FILE
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
│
├── backend/
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/               # Auto-generated migration files
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app: lifespan, CORS, router mounting
│   │   ├── config.py               # Pydantic BaseSettings from .env
│   │   ├── database.py             # Async engine, sessionmaker, get_db dependency
│   │   │
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── __init__.py         # Re-export all models for Alembic
│   │   │   ├── portfolio.py        # Holding, Transaction, CashBalance, RiskProfile
│   │   │   ├── reports.py          # AnalysisReport, AgentDecision
│   │   │   ├── market_data.py      # PriceHistory, FundamentalSnapshot
│   │   │   └── filings.py          # SECFiling, EarningsTranscript, FilingSection
│   │   │
│   │   ├── schemas/                # Pydantic v2 request/response models
│   │   │   ├── __init__.py
│   │   │   ├── portfolio.py
│   │   │   ├── reports.py
│   │   │   ├── agents.py
│   │   │   └── chat.py
│   │   │
│   │   ├── api/                    # FastAPI routers (one file per domain)
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # POST /login, token refresh
│   │   │   ├── portfolio.py        # Portfolio CRUD + performance
│   │   │   ├── reports.py          # Report listing, detail, decision trail
│   │   │   ├── agents.py           # Agent status, manual trigger, direct query
│   │   │   ├── chat.py             # Natural language interface
│   │   │   ├── settings.py         # Risk profile, allocation targets
│   │   │   └── websocket.py        # WebSocket endpoint + connection manager
│   │   │
│   │   ├── services/               # Business logic (no FastAPI dependency)
│   │   │   ├── __init__.py
│   │   │   ├── portfolio_manager.py    # Execute trades, update holdings, validate constraints
│   │   │   ├── data_ingestion.py       # Fetch SEC filings, market data, transcripts
│   │   │   ├── sentiment_service.py    # Social + news sentiment pipeline
│   │   │   ├── report_service.py       # CRUD for reports, decision trail queries
│   │   │   └── chat_router.py          # Intent classification + routing logic
│   │   │
│   │   ├── agents/                 # All LangGraph agent definitions
│   │   │   ├── __init__.py
│   │   │   ├── state.py            # TypedDict state schemas for all agent levels
│   │   │   │
│   │   │   ├── tools/              # @tool decorated functions for agent use
│   │   │   │   ├── __init__.py
│   │   │   │   ├── sec_tools.py
│   │   │   │   ├── market_tools.py
│   │   │   │   ├── fundamental_tools.py
│   │   │   │   ├── sentiment_tools.py
│   │   │   │   ├── transcript_tools.py
│   │   │   │   ├── portfolio_tools.py
│   │   │   │   └── report_tools.py
│   │   │   │
│   │   │   ├── analysts/           # Sector analyst team definitions
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base_analyst.py     # Factory: create_sector_team(sector, symbols)
│   │   │   │   ├── tech_analyst.py
│   │   │   │   ├── healthcare_analyst.py
│   │   │   │   ├── financials_analyst.py
│   │   │   │   ├── energy_analyst.py
│   │   │   │   ├── consumer_analyst.py
│   │   │   │   ├── industrials_analyst.py
│   │   │   │   ├── realestate_analyst.py
│   │   │   │   └── utilities_analyst.py
│   │   │   │
│   │   │   ├── fixed_income/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── bond_analyst.py
│   │   │   │   ├── credit_analyst.py
│   │   │   │   └── rate_analyst.py
│   │   │   │
│   │   │   ├── macro/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── macro_analyst.py
│   │   │   │   └── geopolitical_analyst.py
│   │   │   │
│   │   │   ├── supervisors/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── sector_supervisor.py
│   │   │   │   ├── fixed_income_supervisor.py
│   │   │   │   ├── macro_supervisor.py
│   │   │   │   ├── risk_manager.py
│   │   │   │   └── cio_agent.py
│   │   │   │
│   │   │   ├── ceo_agent.py
│   │   │   └── orchestrator.py         # Builds + compiles the full agent graph
│   │   │
│   │   └── tasks/                  # Celery task definitions
│   │       ├── __init__.py
│   │       ├── celery_app.py           # Celery app + beat schedule config
│   │       ├── data_refresh.py
│   │       ├── filing_monitor.py
│   │       ├── analysis_cycle.py
│   │       └── cleanup.py
│   │
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py                 # Fixtures: test DB, mock LLM, sample data
│       ├── test_tools/
│       │   ├── test_sec_tools.py
│       │   ├── test_market_tools.py
│       │   ├── test_fundamental_tools.py
│       │   └── test_portfolio_tools.py
│       ├── test_services/
│       │   ├── test_portfolio_manager.py
│       │   └── test_data_ingestion.py
│       ├── test_api/
│       │   ├── test_portfolio_api.py
│       │   ├── test_reports_api.py
│       │   └── test_chat_api.py
│       └── test_agents/
│           ├── test_sector_team.py
│           └── test_orchestrator.py
│
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tsconfig.app.json
│   ├── tsconfig.node.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── Dockerfile
│   ├── index.html
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── index.css                   # Tailwind imports
│   │   │
│   │   ├── lib/
│   │   │   ├── api.ts                  # Typed fetch wrapper
│   │   │   ├── websocket.ts            # WebSocket client with reconnection
│   │   │   └── utils.ts                # cn(), formatCurrency(), etc.
│   │   │
│   │   ├── types/
│   │   │   └── index.ts                # All TypeScript interfaces
│   │   │
│   │   ├── store/
│   │   │   ├── portfolioStore.ts
│   │   │   ├── agentStore.ts
│   │   │   ├── chatStore.ts
│   │   │   └── settingsStore.ts
│   │   │
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts
│   │   │   ├── usePortfolio.ts
│   │   │   └── useAgents.ts
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                     # shadcn/ui primitives (install via CLI)
│   │   │   ├── layout/
│   │   │   │   ├── AppLayout.tsx       # Sidebar + header + main content
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── Header.tsx
│   │   │   ├── dashboard/
│   │   │   │   ├── PortfolioSummary.tsx    # Total value, daily P&L, % change
│   │   │   │   ├── AllocationChart.tsx     # Donut chart: sectors + fixed income + cash
│   │   │   │   ├── PerformanceChart.tsx    # Line chart: portfolio vs benchmark
│   │   │   │   ├── RecentDecisions.tsx     # Last 5 decisions with status badges
│   │   │   │   └── AgentStatusGrid.tsx     # Grid of all agent teams with status
│   │   │   ├── portfolio/
│   │   │   │   ├── HoldingsTable.tsx       # Sortable table of all positions
│   │   │   │   ├── TransactionHistory.tsx  # Paginated transaction log
│   │   │   │   └── CashPosition.tsx        # Cash balance + min reserve indicator
│   │   │   ├── agents/
│   │   │   │   ├── AgentTree.tsx           # Interactive hierarchy visualization
│   │   │   │   ├── AgentDetail.tsx         # Single agent: reports, coverage, status
│   │   │   │   └── AgentReportCard.tsx     # Summary card for agent in tree view
│   │   │   ├── reports/
│   │   │   │   ├── ReportList.tsx          # Filterable, searchable report list
│   │   │   │   ├── ReportViewer.tsx        # Full markdown report renderer
│   │   │   │   └── DecisionTrail.tsx       # Expandable chain: CEO→CIO→Supervisor→Analyst
│   │   │   ├── chat/
│   │   │   │   ├── ChatInterface.tsx       # Full chat UI with input, history, markdown
│   │   │   │   ├── ChatMessage.tsx         # Single message with markdown + embedded data
│   │   │   │   └── SuggestionChips.tsx     # Quick-action buttons above input
│   │   │   └── settings/
│   │   │       ├── RiskProfileEditor.tsx   # Aggressiveness slider + allocation pie
│   │   │       ├── PositionLimits.tsx      # Max position %, max sector %
│   │   │       ├── WatchList.tsx           # Add/remove tracked symbols
│   │   │       └── ScheduleConfig.tsx      # View/edit analysis schedule
│   │   │
│   │   └── pages/
│   │       ├── Dashboard.tsx
│   │       ├── Portfolio.tsx
│   │       ├── Agents.tsx
│   │       ├── Reports.tsx
│   │       ├── Chat.tsx
│   │       └── Settings.tsx
│   │
│   └── public/
│       └── favicon.svg
│
└── scripts/
    ├── seed_universe.py            # Seed S&P 500 stocks by sector + major bond ETFs
    ├── setup_db.py                 # Create DB, run migrations, seed initial data
    └── run_analysis.py             # CLI trigger for full analysis cycle
4. Database Schema
Use SQLAlchemy 2.0 declarative style with Mapped type annotations. All models inherit from a shared Base. All tables include created_at and updated_at timestamps via a mixin.

4.1 Portfolio Models (backend/app/models/portfolio.py)

Holding

Column	Type	Constraints	Notes
id	Integer	PK, auto-increment	
symbol	String(10)	NOT NULL, indexed	Ticker symbol
asset_type	String(20)	NOT NULL	Enum: "equity", "etf", "bond_etf", "money_market"
shares	Numeric(18,8)	NOT NULL	Fractional shares supported
avg_cost_basis	Numeric(18,4)	NOT NULL	Average purchase price per share
current_price	Numeric(18,4)	NOT NULL	Latest known price
sector	String(50)	nullable	GICS sector classification
acquired_at	DateTime(tz)	NOT NULL	First purchase timestamp
updated_at	DateTime(tz)	NOT NULL	Last price update
Transaction

Column	Type	Constraints	Notes
id	Integer	PK	
symbol	String(10)	NOT NULL, indexed	
action	String(4)	NOT NULL, CHECK IN ("BUY","SELL")	No other values allowed
shares	Numeric(18,8)	NOT NULL, CHECK > 0	
price_per_share	Numeric(18,4)	NOT NULL	Execution price
total_amount	Numeric(18,4)	NOT NULL	shares × price
fees	Numeric(18,4)	default 0	
agent_decision_id	Integer	FK → agent_decisions.id	Links to the decision that triggered this
executed_at	DateTime(tz)	NOT NULL	
CashBalance

Column	Type	Constraints	Notes
id	Integer	PK	
balance	Numeric(18,4)	NOT NULL, CHECK >= 0	Never negative — no borrowing
updated_at	DateTime(tz)	NOT NULL	
RiskProfile

Column	Type	Constraints	Notes
id	Integer	PK	
aggressiveness	Integer	NOT NULL, CHECK 1-10	Human-settable via chat or UI
max_single_position_pct	Numeric(5,2)	NOT NULL, default 5.00	Max % of portfolio in one stock
max_sector_pct	Numeric(5,2)	NOT NULL, default 25.00	Max % in one sector
min_cash_pct	Numeric(5,2)	NOT NULL, default 5.00	Always keep this % in cash
target_equity_pct	Numeric(5,2)	NOT NULL	
target_fixed_income_pct	Numeric(5,2)	NOT NULL	
target_cash_pct	Numeric(5,2)	NOT NULL	equity+fi+cash must = 100
updated_at	DateTime(tz)	NOT NULL	
updated_by	String(20)	NOT NULL	"human" or "system"
notes	Text	nullable	Natural language description of change
4.2 Report Models (backend/app/models/reports.py)

AnalysisReport

Column	Type	Constraints	Notes
id	Integer	PK	
agent_name	String(100)	NOT NULL, indexed	e.g., "technology_filing_analyst"
agent_role	String(50)	NOT NULL	"analyst", "supervisor", "cio", "risk_manager", "ceo"
report_type	String(50)	NOT NULL	"filing_analysis", "earnings_analysis", "quant_analysis", "sector_overview", "risk_assessment", "macro_outlook", "executive_summary"
symbol	String(10)	nullable, indexed	NULL for sector/macro reports
sector	String(50)	nullable, indexed	
title	String(500)	NOT NULL	
content	Text	NOT NULL	Full markdown report body
recommendation	String(20)	nullable	"STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL", "OVERWEIGHT", "UNDERWEIGHT"
confidence	Integer	nullable, CHECK 1-10	
key_metrics	JSONB	default {}	Structured extracted metrics
parent_report_id	Integer	FK → self, nullable	For tree structure
created_at	DateTime(tz)	NOT NULL	
Add a self-referential relationship: children = relationship("AnalysisReport", back_populates="parent") and parent = relationship("AnalysisReport", remote_side=[id], back_populates="children").

Create a GIN index on content for full-text search.

AgentDecision

Column	Type	Constraints	Notes
id	Integer	PK	
decision_type	String(20)	NOT NULL	"trade", "rebalance", "hold", "review_needed"
symbol	String(10)	nullable	
action	String(4)	nullable, CHECK IN ("BUY","SELL") or NULL	
recommended_shares	Numeric(18,8)	nullable	
recommended_amount	Numeric(18,4)	nullable	Dollar amount
reasoning	Text	NOT NULL	CEO's reasoning for this specific decision
confidence	Integer	NOT NULL, CHECK 1-10	
risk_score	Numeric(5,2)	nullable	From Risk Manager
supporting_report_ids	JSONB	NOT NULL	Array of AnalysisReport IDs
dissenting_opinions	Text	nullable	Any analyst disagreements
status	String(20)	NOT NULL, default "proposed"	"proposed", "approved", "executed", "rejected", "human_review"
human_override	Boolean	default false	True if human changed the decision
human_notes	Text	nullable	Human's reason for override
created_at	DateTime(tz)	NOT NULL	
executed_at	DateTime(tz)	nullable	
4.3 Market Data Models (backend/app/models/market_data.py)

PriceHistory

Column	Type	Constraints	Notes
id	Integer	PK	
symbol	String(10)	NOT NULL	
date	Date	NOT NULL	
open	Numeric(18,4)		
high	Numeric(18,4)		
low	Numeric(18,4)		
close	Numeric(18,4)	NOT NULL	
volume	BigInteger		
Unique constraint on (symbol, date)			
FundamentalSnapshot

Column	Type	Constraints	Notes
id	Integer	PK	
symbol	String(10)	NOT NULL, indexed	
snapshot_date	Date	NOT NULL	
pe_ratio	Numeric(10,2)	nullable	
pb_ratio	Numeric(10,2)	nullable	
ps_ratio	Numeric(10,2)	nullable	
ev_ebitda	Numeric(10,2)	nullable	
roe	Numeric(10,4)	nullable	
roa	Numeric(10,4)	nullable	
debt_to_equity	Numeric(10,4)	nullable	
current_ratio	Numeric(10,4)	nullable	
revenue_ttm	Numeric(18,2)	nullable	
net_income_ttm	Numeric(18,2)	nullable	
free_cash_flow_ttm	Numeric(18,2)	nullable	
market_cap	Numeric(18,2)	nullable	
dividend_yield	Numeric(10,4)	nullable	
beta	Numeric(10,4)	nullable	
raw_data	JSONB	default {}	Full yfinance info dump
4.4 Filing Models (backend/app/models/filings.py)

SECFiling

Column	Type	Constraints	Notes
id	Integer	PK	
symbol	String(10)	NOT NULL, indexed	
cik	String(10)	NOT NULL	SEC Central Index Key
filing_type	String(10)	NOT NULL	"10-K", "10-Q", "8-K"
filing_date	Date	NOT NULL	
accession_number	String(25)	NOT NULL, unique	SEC unique identifier
filing_url	String(500)	NOT NULL	URL to full filing
is_processed	Boolean	default false	
processed_at	DateTime(tz)	nullable	
Unique constraint on accession_number			
EarningsTranscript

Column	Type	Constraints	Notes
id	Integer	PK	
symbol	String(10)	NOT NULL, indexed	
fiscal_year	Integer	NOT NULL	
fiscal_quarter	Integer	NOT NULL, CHECK 1-4	
event_date	Date	NOT NULL	
full_text	Text	NOT NULL	Complete transcript
ceo_remarks	Text	nullable	Extracted CEO section
cfo_remarks	Text	nullable	Extracted CFO section
qa_section	Text	nullable	Analyst Q&A section
sentiment_score	Numeric(5,4)	nullable	Overall sentiment -1 to 1
is_processed	Boolean	default false	
Unique constraint on (symbol, fiscal_year, fiscal_quarter)			
5. Agent Architecture
5.1 Hierarchy Diagram

text
                              ┌──────────────────┐
                              │    CEO Agent      │
                              │  Final Decisions  │
                              │  Executive Report │
                              └────────┬─────────┘
                                       │
                 ┌─────────────────────┼─────────────────────┐
                 │                     │                     │
        ┌────────┴────────┐  ┌────────┴────────┐  ┌────────┴────────┐
        │   CIO Agent     │  │  Risk Manager   │  │ Macro Supervisor│
        │ Investment       │  │ Portfolio Risk   │  │ Economic        │
        │ Strategy         │  │ Assessment       │  │ Environment     │
        └────────┬────────┘  └─────────────────┘  └────────┬────────┘
                 │                                          │
     ┌───────────┼───────────┐                    ┌────────┼────────┐
     │           │           │                    │                 │
┌────┴────┐ ┌───┴────┐ ┌────┴─────┐        ┌────┴─────┐   ┌──────┴──────┐
│Sector   │ │Sector  │ │Fixed     │        │ Macro    │   │Geopolitical │
│Supv A   │ │Supv B  │ │Income    │        │ Analyst  │   │Analyst      │
│Tech,    │ │Energy, │ │Supervisor│        └──────────┘   └─────────────┘
│Health,  │ │Consumer│ │          │
│Financial│ │Indust, │ └────┬─────┘
└────┬────┘ │Real Est│      │
     │      │Utility │ ┌────┼──────────┐
     │      └───┬────┘ │    │          │
     │          │    ┌──┴──┐┌┴────┐┌───┴──┐
     │          │    │Bond ││Credit││Rate  │
     │          │    │Anlst││Anlst ││Anlst │
     │          │    └─────┘└─────┘└──────┘
     │          │
  [Per sector: 3 agents]
  ┌──┴───────────┐
  │ Filing       │ → reads 10-K, 10-Q
  │ Analyst      │
  ├──────────────┤
  │ Earnings     │ → analyzes transcripts
  │ Analyst      │
  ├──────────────┤
  │ Quantitative │ → ratios, DCF, sentiment
  │ Analyst      │
  └──────────────┘
5.2 Agent Roles

Agent	Reports To	Responsibilities	Tools Used
Filing Analyst (×8 sectors)	Sector Supervisor	Parse 10-K/10-Q, extract key metrics, identify risk factors, analyze MD&A	sec_tools, report_tools
Earnings Analyst (×8 sectors)	Sector Supervisor	Analyze earnings transcripts, detect tone shifts, compare guidance	transcript_tools, report_tools
Quant Analyst (×8 sectors)	Sector Supervisor	Financial ratios, DCF modeling, peer comps, sentiment overlay	fundamental_tools, market_tools, sentiment_tools, report_tools
Sector Supervisor (×2 groups)	CIO	Synthesize analyst reports per sector, rank opportunities, sector outlook	report_tools
Bond Analyst	FI Supervisor	Treasury yields, corporate bond ETF analysis, duration risk	market_tools, report_tools
Credit Analyst	FI Supervisor	Credit spreads, default risk indicators, rating changes	market_tools, report_tools
Rate Analyst	FI Supervisor	Fed funds rate outlook, yield curve analysis, inflation expectations	market_tools, macro data, report_tools
FI Supervisor	CIO	Aggregate fixed income recommendations, allocation suggestion	report_tools
Macro Analyst	Macro Supervisor	GDP, employment, inflation, consumer confidence analysis	market_tools, report_tools
Geopolitical Analyst	Macro Supervisor	Geopolitical risk assessment, trade policy, sanctions impact	report_tools
Macro Supervisor	CEO	Economic environment synthesis, risk backdrop	report_tools
CIO	CEO	Aggregate sector + FI recommendations, propose allocation changes	report_tools, portfolio_tools
Risk Manager	CEO	Independent risk assessment, concentration analysis, VETO authority	portfolio_tools, market_tools, report_tools
CEO	Human	Final decisions, executive summary, enforce all constraints	All report_tools, portfolio_tools
5.3 Information Flow

Data Collection (Celery tasks): Market data, filings, transcripts fetched and stored

Analysis (Bottom-up): Each sector's 3 analysts run in parallel, producing reports

Aggregation (Supervisors): Sector supervisors synthesize analyst reports into sector-level recommendations

Strategy (CIO + Risk + Macro): CIO proposes portfolio changes; Risk Manager independently assesses; Macro provides backdrop

Decision (CEO): Reviews all supervisor inputs, makes final BUY/SELL/HOLD decisions

Execution: Trades with confidence ≥ 7 auto-execute; confidence 4-6 flagged for human review; confidence < 4 rejected

Reporting: All reports + decisions persisted; human notified via WebSocket

6. Agent Tools
Every tool is a @tool decorated function (LangChain tools compatible with LangGraph). Tools must be stateless — they read from DB/APIs and return data. All external API calls must use tenacity retry with exponential backoff. All tools return typed dictionaries.

6.1 SEC Tools (sec_tools.py)

python
@tool
def fetch_10k_filing(symbol: str, year: int) -> dict:
    """Fetch and parse a company's 10-K annual filing from SEC EDGAR.
    Returns parsed sections: business, risk_factors, mda, financial_statements, notes.
    Stores full text in ChromaDB for semantic search. Caches in PostgreSQL."""

@tool
def fetch_10q_filing(symbol: str, year: int, quarter: int) -> dict:
    """Fetch and parse a 10-Q quarterly filing. Same return structure as 10-K."""

@tool
def search_filing_content(symbol: str, query: str, top_k: int = 5) -> list[dict]:
    """Semantic search across all stored filing content for a symbol using ChromaDB.
    Returns matching text chunks with section metadata and relevance scores."""

@tool
def get_recent_filings(symbol: str, filing_type: str = "all", limit: int = 5) -> list[dict]:
    """List recent filings for a symbol from the database. Returns metadata, not full content."""
Implementation notes:

Use SEC EDGAR full-text search: https://efts.sec.gov/LATEST/search-index?q={symbol}&dateRange=custom&startdt={start}&enddt={end}&forms={type}

Always send User-Agent header matching SEC_USER_AGENT env var (SEC requires this)

Rate limit: max 10 requests/second to SEC

Parse HTML filings with BeautifulSoup + lxml

For 10-K section extraction: use regex patterns for "Item 1", "Item 1A", "Item 7", etc. or use the FMP section extraction API as fallback

Chunk text at ~1000 tokens for ChromaDB embeddings

Store ChromaDB collection per symbol: filings_{symbol}

6.2 Market Tools (market_tools.py)

python
@tool
def get_stock_price(symbol: str) -> dict:
    """Get current stock price, volume, day change, 52-week range via yfinance.
    Returns: {symbol, price, change, change_pct, volume, high_52w, low_52w, market_cap}"""

@tool
def get_price_history(symbol: str, period: str = "1y", interval: str = "1d") -> dict:
    """Get historical OHLCV data. period: 1mo,3mo,6mo,1y,2y,5y. interval: 1d,1wk,1mo.
    Returns: {symbol, period, data: [{date, open, high, low, close, volume}]}"""

@tool
def get_market_overview() -> dict:
    """Get major market indices (SPY, QQQ, DIA, IWM), VIX, sector ETF performance (XLK, XLV, XLF, etc.).
    Returns: {indices: [...], vix: float, sectors: [...]}"""

@tool
def get_sector_etf_performance(sector: str) -> dict:
    """Get performance data for a specific sector's representative ETF.
    Sector mapping: technology->XLK, healthcare->XLV, financials->XLF, energy->XLE,
    consumer->XLY+XLP, industrials->XLI, real_estate->XLRE, utilities->XLU"""
Implementation notes:

All yfinance calls wrapped in tenacity.retry with 3 attempts

Cache stock prices in Redis with 5-minute TTL during market hours, 1-hour after

Cache price history in Redis with 1-hour TTL

Store daily close prices in PriceHistory table for long-term tracking

6.3 Fundamental Tools (fundamental_tools.py)

python
@tool
def get_financial_ratios(symbol: str) -> dict:
    """Calculate and return key financial ratios.
    Returns: {pe, forward_pe, pb, ps, ev_ebitda, roe, roa, debt_equity, current_ratio,
              quick_ratio, gross_margin, operating_margin, net_margin, revenue_growth_yoy,
              earnings_growth_yoy, dividend_yield, payout_ratio, beta}"""

@tool
def run_dcf_analysis(symbol: str, growth_rate: float = None, discount_rate: float = 0.10,
                     terminal_growth: float = 0.025, projection_years: int = 5) -> dict:
    """Run a discounted cash flow analysis using historical free cash flow.
    If growth_rate is None, estimate from historical FCF growth.
    Returns: {fair_value_per_share, current_price, upside_pct, assumptions: {...}, 
              projected_fcf: [...], sensitivity_table: {...}}"""

@tool
def get_comparable_analysis(symbol: str) -> dict:
    """Compare a stock against its sector peers on key valuation multiples.
    Automatically identifies 5-8 peers in the same GICS sub-industry.
    Returns: {target: {...}, peers: [{symbol, pe, pb, ev_ebitda, ...}], 
              target_vs_median: {pe_premium_pct, ...}}"""
Implementation notes:

Primary data source: yfinance .info, .financials, .balance_sheet, .cashflow

Fallback: FMP API for any missing data points

DCF should use 3 scenarios: bull (growth+2%), base, bear (growth-2%)

Save FundamentalSnapshot to DB after each calculation

6.4 Sentiment Tools (sentiment_tools.py)

python
@tool
def get_social_sentiment(symbol: str) -> dict:
    """Analyze social media sentiment for a stock using pyfin-sentiment.
    Scrapes recent mentions and classifies as Bullish/Bearish/Neutral.
    Returns: {symbol, bullish_pct, bearish_pct, neutral_pct, sample_size, 
              notable_posts: [{text, sentiment, source}], trend: "improving"|"declining"|"stable"}"""

@tool
def get_news_sentiment(symbol: str, days: int = 7) -> dict:
    """Analyze recent news headlines using FinBERT.
    Returns: {symbol, avg_sentiment: float(-1 to 1), positive_count, negative_count, 
              neutral_count, headlines: [{title, sentiment, score, source, date}]}"""

@tool
def get_insider_trading(symbol: str, months: int = 6) -> dict:
    """Get recent insider trading activity (Form 4 filings).
    Returns: {symbol, net_insider_sentiment: "buying"|"selling"|"neutral",
              total_buys: int, total_sells: int, notable: [{name, title, action, shares, value, date}]}"""
Implementation notes:

Social sentiment: Use pyfin-sentiment model. For post data, scrape from free sources (Reddit API, or use a news aggregator). Cache results for 4 hours.

News: Use newsapi.org free tier (100 req/day) or scrape Google News RSS. Run FinBERT on headlines.

Insider trading: Fetch from SEC EDGAR Form 4 filings for the CIK, or use FMP insider trading endpoint.

6.5 Transcript Tools (transcript_tools.py)

python
@tool
def get_earnings_transcript(symbol: str, year: int, quarter: int) -> dict:
    """Fetch earnings call transcript from FMP API.
    Returns: {symbol, year, quarter, date, full_text, sections: {
        ceo_remarks: str, cfo_remarks: str, qa_section: str
    }}"""

@tool  
def analyze_transcript_sentiment(transcript_text: str) -> dict:
    """Run NLP sentiment analysis on earnings call text.
    Returns: {overall_sentiment: float, confidence_indicators: [...],
              hedging_language_count: int, forward_looking_statements: int,
              key_phrases: [{phrase, sentiment, context}]}"""

@tool
def compare_guidance(symbol: str, current_quarter: dict = None) -> dict:
    """Compare current quarter guidance language against previous 4 quarters.
    Detects: raised/lowered/maintained guidance, tone shifts, new risk mentions.
    Returns: {guidance_trend: "improving"|"declining"|"stable", 
              quarter_comparison: [{quarter, key_metrics_mentioned, tone_score}],
              notable_changes: [str]}"""
Implementation notes:

Primary transcript source: FMP API (/stable/earning-call-transcript)

Fallback: earningscall Python package (free tier: limited calls)

Store transcripts in EarningsTranscript table AND in ChromaDB for semantic search

For speaker segmentation: parse transcript text for patterns like "CEO:", speaker names followed by colons

6.6 Portfolio Tools (portfolio_tools.py)

python
@tool
def get_current_holdings() -> list[dict]:
    """Get all current portfolio holdings with P&L calculations.
    Returns: [{symbol, shares, avg_cost, current_price, market_value, 
               unrealized_pnl, unrealized_pnl_pct, sector, asset_type, weight_pct}]"""

@tool
def get_cash_balance() -> dict:
    """Get current cash balance and reserve requirements.
    Returns: {balance, min_reserve, available_for_investment, pct_of_portfolio}"""

@tool
def get_risk_profile() -> dict:
    """Get current risk profile settings.
    Returns all RiskProfile fields as dict."""

@tool
def get_portfolio_metrics() -> dict:
    """Calculate portfolio-level risk and return metrics.
    Returns: {total_value, daily_pnl, total_return_pct, sharpe_ratio, beta, 
              max_drawdown, concentration_hhi, sector_weights: {...}, 
              top_5_positions: [...], correlation_to_spy: float}"""

@tool
def validate_trade(action: str, symbol: str, shares: float, estimated_price: float) -> dict:
    """Validate a proposed trade against all constraints.
    Checks: sufficient cash (buys), sufficient shares (sells), position limits,
    sector limits, minimum cash reserve, NO MARGIN, NO SHORT SELLING.
    Returns: {valid: bool, errors: [str], warnings: [str], 
              post_trade_position_pct: float, post_trade_cash: float}"""

@tool
def execute_trade(action: str, symbol: str, shares: float, price: float, decision_id: int) -> dict:
    """Execute a validated trade. Updates holdings, cash balance, creates transaction record.
    REJECTS: any action other than BUY or SELL, any trade that would make cash negative.
    Returns: {success: bool, transaction_id: int, new_cash_balance: float, error: str|None}"""
CRITICAL: validate_trade and execute_trade must enforce:

action must be exactly "BUY" or "SELL" — reject everything else

For BUY: shares × price must not exceed available_cash - minimum_cash_reserve

For SELL: must own at least shares of symbol

Post-trade position must not exceed max_single_position_pct

Post-trade sector weight must not exceed max_sector_pct

These checks are in addition to DB-level constraints — defense in depth

6.7 Report Tools (report_tools.py)

python
@tool
def save_analysis_report(agent_name: str, agent_role: str, report_type: str,
                         title: str, content: str, symbol: str = None, sector: str = None,
                         recommendation: str = None, confidence: int = None,
                         key_metrics: dict = None, parent_report_id: int = None) -> dict:
    """Save an analysis report to the database. Returns: {report_id: int}"""

@tool
def get_reports_for_symbol(symbol: str, limit: int = 10) -> list[dict]:
    """Get most recent analysis reports for a symbol, ordered by created_at desc."""

@tool
def get_reports_by_agent(agent_name: str, limit: int = 10) -> list[dict]:
    """Get most recent reports from a specific agent."""

@tool
def get_decision_trail(decision_id: int) -> dict:
    """Get the full chain of reports that supported a decision.
    Follows parent_report_id relationships from CEO report down to analyst reports.
    Returns: {decision: {...}, report_chain: [{level: "ceo"|"cio"|..., report: {...}}]}"""

@tool
def get_latest_sector_reports(sector: str) -> dict:
    """Get the latest analysis reports for all stocks in a sector.
    Returns: {sector, reports: [{symbol, report_type, recommendation, confidence, summary}]}"""
7. Agent Definitions
7.1 Base Sector Team Factory (base_analyst.py)

The create_sector_team function creates a LangGraph subgraph for any sector. Each team has 3 agents managed by a supervisor:

python
def create_sector_team(sector_name: str, tracked_symbols: list[str]) -> CompiledGraph:
    """
    Factory that creates a 3-agent analyst team + supervisor for a market sector.

    Agents created:
    1. Filing Analyst - specializes in SEC filing analysis
    2. Earnings Analyst - specializes in earnings call transcript analysis  
    3. Quantitative Analyst - specializes in financial modeling + sentiment

    The sector supervisor coordinates these agents and synthesizes their findings.
    Returns a compiled LangGraph that can be used as a node in the parent graph.
    """
Each sector-specific file (e.g., tech_analyst.py) calls this factory with sector-specific system prompt additions. For example, the tech analyst's filing analyst gets additional instructions about analyzing R&D spending trends, patent portfolios, and cloud revenue metrics.

7.2 System Prompts

Filing Analyst Template:

text
You are a filing analyst specializing in the {sector} sector.

YOUR TASK: Analyze SEC 10-K and 10-Q filings for {symbols}.

FOR EACH FILING YOU ANALYZE:
1. Extract key financial metrics: revenue, operating income, net income, FCF, margins
2. Identify YoY trends in these metrics
3. Read Risk Factors (Item 1A) — flag any NEW risks not in prior filings
4. Read MD&A (Item 7) — summarize management's explanation of results
5. Check for: restatements, auditor changes, going concern language, unusual items
6. Note any significant changes in accounting policies

OUTPUT: Save a detailed report using save_analysis_report with:
- report_type: "filing_analysis"
- Specific numbers and direct quotes from filings
- Clear BUY/SELL/HOLD recommendation with confidence 1-10
- key_metrics dict with extracted numbers

{sector_specific_additions}
Earnings Analyst Template:

text
You are an earnings call analyst specializing in the {sector} sector.

YOUR TASK: Analyze earnings call transcripts for {symbols}.

FOR EACH TRANSCRIPT:
1. Summarize CEO's key messages (prepared remarks)
2. Summarize CFO's financial commentary
3. Analyze the Q&A section — what are analysts most concerned about?
4. Detect tone: confident vs hedging, specific vs vague guidance
5. Compare guidance to previous quarter — raised, lowered, maintained?
6. Identify management buzzwords and strategic themes
7. Flag any analyst questions that were deflected or poorly answered

OUTPUT: Save a detailed report using save_analysis_report with:
- report_type: "earnings_analysis"  
- Specific quotes from transcript
- Guidance comparison vs prior quarter
- Tone assessment with examples

{sector_specific_additions}
Quantitative Analyst Template:

text
You are a quantitative analyst specializing in the {sector} sector.

YOUR TASK: Build a quantitative picture for {symbols}.

FOR EACH STOCK:
1. Pull current financial ratios and compare to 5-year averages
2. Run DCF analysis with bull/base/bear scenarios
3. Compare valuation multiples against sector peers
4. Analyze price momentum (50-day vs 200-day MA, RSI equivalent)
5. Overlay social media and news sentiment
6. Check insider trading patterns (last 6 months)

OUTPUT: Save a detailed report using save_analysis_report with:
- report_type: "quant_analysis"
- DCF fair value and current price comparison
- Peer comparison table
- Sentiment summary
- Clear valuation call: undervalued/fairly valued/overvalued

{sector_specific_additions}
Sector Supervisor Template:

text
You are the supervisor for the {sector} sector analyst team.

YOUR TASK: After your team of analysts has completed their work, synthesize their findings.

PROCESS:
1. Review each analyst's report for your covered stocks ({symbols})
2. For each stock: aggregate the filing analysis + earnings analysis + quant analysis
3. Identify where analysts agree (high conviction) vs disagree (flag for discussion)
4. Rank all stocks in your sector: best opportunities to worst
5. Provide sector-level outlook (bullish/neutral/bearish) with reasoning

OUTPUT: Save a sector overview report using save_analysis_report with:
- report_type: "sector_overview"
- Ranked stock list with synthesized recommendation and confidence
- Sector outlook paragraph
- Key risks and catalysts for the sector
- Any analyst disagreements highlighted
CEO Agent Prompt:

text
You are the CEO of Superhuman Alpha Fund, an automated investment analysis system.

ABSOLUTE RULES — VIOLATION OF ANY RULE IS A CRITICAL FAILURE:
1. NO MARGIN TRADING. NO BORROWING. NO SHORT SELLING. NO LEVERAGE. Cash positions only.
2. Every trade must have supporting analysis from at least 2 hierarchy levels.
3. Never exceed position limits or sector limits from the risk profile.
4. Always maintain minimum cash reserves per the risk profile.
5. Every decision MUST include: reasoning, confidence (1-10), supporting report IDs, risk assessment, and any dissenting opinions.

YOUR PROCESS:
1. Read the CIO's investment strategy recommendations.
2. Read the Risk Manager's independent portfolio risk assessment.
3. Read the Macro Supervisor's economic outlook.
4. Cross-reference all recommendations against the current risk profile and allocation targets.
5. Produce your FINAL DECISIONS as a list of specific trades.
6. For each proposed trade, call validate_trade to verify constraint compliance.
7. For trades with confidence >= 7: mark as "approved" for auto-execution.
8. For trades with confidence 4-6: mark as "human_review".
9. For trades with confidence < 4: mark as "rejected" with explanation.

EXECUTIVE REPORT: Generate a comprehensive summary including:
- Market environment (1 paragraph drawing from macro analysis)
- Table of proposed actions: symbol, action, shares, amount, reasoning, confidence
- Portfolio impact: projected allocation shift, risk metrics change
- Dissenting opinions summary (any analyst who disagreed with the final call)
- 30-day outlook and what to watch for

HUMAN PREFERENCES: Always check the current risk profile first. The human may have recently:
- Changed aggressiveness (1=ultra conservative, 10=aggressive growth)
- Adjusted allocation targets (equity vs fixed income vs cash)
- Modified position or sector limits
Respect ALL human-set parameters. When in doubt, be more conservative.
8. Orchestrator
backend/app/agents/orchestrator.py builds and compiles the complete multi-agent LangGraph.

8.1 Graph Construction

python
def build_fund_graph(db_session, stock_universe: dict[str, list[str]]) -> CompiledGraph:
    """
    Build the complete Superhuman Alpha Fund agent hierarchy as a LangGraph.

    Args:
        db_session: Async database session for tools
        stock_universe: Dict mapping sector names to lists of stock symbols
            e.g., {"technology": ["AAPL", "MSFT", "NVDA", ...], ...}

    Returns:
        Compiled LangGraph ready for invocation

    Graph structure:
        1. All sector teams run in PARALLEL (they are independent)
        2. Fixed income team runs in PARALLEL with sector teams
        3. Macro team runs in PARALLEL with sector + FI teams
        4. After all teams complete → CIO aggregates + Risk Manager assesses (parallel)
        5. After CIO + Risk complete → CEO makes final decisions
    """
8.2 Execution Modes

Full Analysis Cycle: Run the entire graph end-to-end. Used for daily scheduled analysis and manual "run full analysis" triggers.

Targeted Analysis: Run only one sector team for a specific symbol, then feed the new report up through CIO → CEO for an updated decision. Used when a new filing is detected or human requests fresh analysis.

Portfolio Review: Skip sector analysis, just run Risk Manager + CEO with existing reports to re-evaluate current positions against updated risk profile.

9. Data Ingestion & Scheduling
9.1 Celery Configuration (celery_app.py)

python
beat_schedule = {
    "refresh-market-data": {
        "task": "app.tasks.data_refresh.refresh_market_data",
        "schedule": crontab(minute="*/15", hour="9-16", day_of_week="1-5"),  # Every 15 min during market hours ET
    },
    "refresh-after-hours": {
        "task": "app.tasks.data_refresh.refresh_market_data",
        "schedule": crontab(minute="0", hour="17-23,0-8", day_of_week="1-5"),  # Hourly after hours
    },
    "refresh-fundamentals": {
        "task": "app.tasks.data_refresh.refresh_fundamentals",
        "schedule": crontab(minute="30", hour="18", day_of_week="1-5"),  # 6:30 PM ET weekdays
    },
    "check-new-filings": {
        "task": "app.tasks.filing_monitor.check_new_filings",
        "schedule": crontab(minute="*/30", hour="8-20", day_of_week="1-5"),  # Every 30 min during business hours
    },
    "daily-analysis-cycle": {
        "task": "app.tasks.analysis_cycle.run_full_analysis",
        "schedule": crontab(minute="0", hour="19", day_of_week="1-5"),  # 7 PM ET weekdays
    },
    "weekly-cleanup": {
        "task": "app.tasks.cleanup.cleanup_old_data",
        "schedule": crontab(minute="0", hour="3", day_of_week="0"),  # 3 AM Sunday
    },
}
9.2 Task Definitions

data_refresh.py:

refresh_market_data(): Update prices for all holdings + watchlist symbols. Update major indices. Store in Redis cache + PriceHistory table (daily).

refresh_fundamentals(): Pull latest fundamental data via yfinance for all tracked symbols. Save FundamentalSnapshot.

filing_monitor.py:

check_new_filings(): Query SEC EDGAR EFTS for new 10-K, 10-Q, 8-K filings for all tracked CIKs. If new filing found: create SECFiling record, trigger ingest_filing task.

ingest_filing(filing_id: int): Download filing, parse sections, store in ChromaDB, mark as processed, trigger run_targeted_analysis for the affected symbol.

analysis_cycle.py:

run_full_analysis(): Execute the full agent graph (orchestrator). Broadcast progress via WebSocket. Save all reports and decisions. Notify human of any decisions requiring review.

run_targeted_analysis(symbol: str): Run only the relevant sector team + CIO + CEO for one symbol.

cleanup.py:

cleanup_old_data(): Archive reports older than 2 years. Prune intraday price data older than 1 year (keep daily only). Vacuum ChromaDB. Log all cleanup actions.

10. Backend API
10.1 Endpoint Specification

Auth

Method	Path	Description	Request	Response
POST	/api/auth/login	Login, get JWT	{username, password}	{access_token, token_type}
Portfolio

Method	Path	Description	Response
GET	/api/portfolio	Portfolio summary	{total_value, daily_pnl, total_return, cash_balance, allocation}
GET	/api/portfolio/holdings	All holdings	[{symbol, shares, cost_basis, current_price, pnl, weight}]
GET	/api/portfolio/performance?period=1y	Performance time series	{dates: [], values: [], benchmark: []}
GET	/api/portfolio/transactions?page=1&limit=20	Transaction history	Paginated list with agent decision links
Reports

Method	Path	Description	Query Params	Response
GET	/api/reports	List reports	?agent=&sector=&symbol=&type=&page=&limit=	Paginated report list
GET	/api/reports/{id}	Report detail		Full report with content
GET	/api/reports/decision-trail/{decision_id}	Decision reasoning chain		Nested report tree from CEO → analysts
GET	/api/reports/latest-by-sector	Latest sector summaries		Grouped by sector
Agents

Method	Path	Description
GET	/api/agents	All agents with status, last run, next scheduled
GET	/api/agents/{name}	Single agent detail + recent reports
POST	/api/agents/trigger/{name}	Manually trigger an agent or team run
POST	/api/agents/query	Route a question to the appropriate agent. Body: {question: str}
Chat

Method	Path	Description
POST	/api/chat	Natural language interface. Body: {message: str}. See Section 11.
GET	/api/chat/history?limit=50	Recent chat history
Settings

Method	Path	Description
GET	/api/settings/risk-profile	Current risk profile
PUT	/api/settings/risk-profile	Update risk profile (partial update supported)
GET	/api/settings/watchlist	Current watchlist
POST	/api/settings/watchlist	Add symbol to watchlist
DELETE	/api/settings/watchlist/{symbol}	Remove from watchlist
GET	/api/settings/schedule	Current Celery beat schedule
WebSocket

Path	Description
/api/ws	Real-time updates: agent run progress, new reports, new decisions, price updates
10.2 WebSocket Message Format

typescript
type WSMessage = {
  type: "agent_status" | "new_report" | "new_decision" | "price_update" | "analysis_progress";
  payload: {
    agent_name?: string;
    status?: "running" | "completed" | "error";
    report_id?: number;
    decision_id?: number;
    symbol?: string;
    price?: number;
    progress_pct?: number;
    message?: string;
  };
  timestamp: string;  // ISO 8601
};
11. Natural Language Chat Interface
11.1 Intent Classification

The chat endpoint uses a dedicated LLM call (not a full agent) to classify user intent before routing:

Intent	Examples	Routing
DECISION_QUERY	"Why did we buy AAPL?", "Explain the sell decision"	Fetch decision trail, format as readable response
SETTINGS_CHANGE	"Be more aggressive", "Set max position to 3%", "More bonds"	Parse into parameter changes, confirm, apply
ANALYSIS_QUERY	"What about TSLA?", "How's tech looking?"	Find latest reports or trigger fresh analysis
PORTFOLIO_QUERY	"How are we doing?", "Biggest winner?", "Cash position?"	Query portfolio data, format response
TRIGGER_ANALYSIS	"Run analysis on NVDA", "Re-evaluate healthcare"	Trigger targeted or sector analysis task
GENERAL	"What's the market doing?", "Good morning"	Market overview or friendly response
11.2 Settings Change Parsing

Natural language settings changes must be parsed into concrete parameter updates and confirmed before applying:

text
User: "Let's be more aggressive, I want to take more risk"
System: "I'll update your risk profile:
  - Aggressiveness: 5 → 7
  - Target equity: 60% → 75%  
  - Target fixed income: 30% → 15%
  - Target cash: 10% → 10% (unchanged)
  Shall I apply these changes?"
User: "Yes"
System: "Done. I've updated your risk profile. The next analysis cycle will use these new targets."
Mapping rules for aggressiveness changes:

Description	Aggressiveness Δ	Equity Δ	Fixed Income Δ
"much more aggressive" / "maximum growth"	+3	+15%	-15%
"more aggressive" / "take more risk"	+2	+10%	-10%
"slightly more aggressive"	+1	+5%	-5%
"slightly more conservative"	-1	-5%	+5%
"more conservative" / "reduce risk"	-2	-10%	+10%
"much more conservative" / "safety first"	-3	-15%	+15%
All values clamped: aggressiveness [1,10], each allocation [0%,100%], sum must = 100%.

11.3 Decision Trail Formatting

When a user asks about a decision, format the response as a readable chain:

text
📊 Decision: BUY 50 shares of NVDA at $142.30 (Confidence: 8/10)

🏢 CEO Assessment:
"Strong convergence across all analyst levels. NVDA shows exceptional revenue growth..."

📈 CIO Recommendation: OVERWEIGHT Technology, STRONG BUY NVDA
- Based on sector supervisor ranking NVDA #1 in technology sector

🔬 Technology Sector Analysis:
├── Filing Analyst (Confidence: 9): "Revenue grew 122% YoY driven by data center..."
├── Earnings Analyst (Confidence: 8): "Management raised full-year guidance by 15%..."  
└── Quant Analyst (Confidence: 7): "DCF fair value $165, currently trading at 14% discount..."

⚠️ Risk Manager Assessment: Risk Score 3.2/10 (Low)
- Post-trade NVDA position: 4.2% (below 5% limit)
- Technology sector weight: 22% (below 25% limit)

🌍 Macro Context: "Positive AI investment cycle supports tech spending..."
12. Frontend Application
12.1 Layout

Single-page application with persistent left sidebar navigation:

text
┌─────────┬──────────────────────────────────────────────┐
│         │  Header: "Superhuman Alpha Fund" + portfolio value     │
│ 📊 Dash │  + daily P&L + last analysis timestamp       │
│ 💼 Port ├──────────────────────────────────────────────│
│ 🤖 Agent│                                              │
│ 📄 Repts│           Main Content Area                  │
│ 💬 Chat │        (renders active page)                 │
│ ⚙️ Sett │                                              │
│         │                                              │
│         │                                              │
└─────────┴──────────────────────────────────────────────┘
12.2 Page Specifications

Dashboard (/)

Top row: 4 metric cards — Total Value, Daily P&L (green/red), Total Return %, Cash Available

Middle left: Allocation donut chart (Recharts PieChart) — sectors + fixed income + cash, interactive hover

Middle right: Performance line chart (Recharts LineChart) — portfolio value vs SPY benchmark, time period selector (1M/3M/6M/1Y/ALL)

Bottom left: Recent Decisions list — last 5 AgentDecisions, each with status badge (✅ executed, 🔍 human review, ❌ rejected), click to expand reasoning

Bottom right: Agent Status grid — card per agent team showing status, last run time, health indicator

Portfolio (/portfolio)

Holdings table (sortable, filterable): symbol, name, shares, avg cost, current price, market value, P&L ($), P&L (%), weight %, sector

Color coding: green for gains, red for losses

Click any row → slide-out panel with latest analysis reports for that symbol

Below table: Transaction history (paginated, most recent first) with link to decision that triggered each trade

Cash position card with visual indicator of reserve vs available

Agents (/agents)

Interactive tree visualization of the full agent hierarchy (Section 5.1)

Use reactflow library for the tree layout

Each node shows: agent name, role, status indicator (green/yellow/red), last run time

Click any node → right panel shows: agent description, recent reports, covered symbols, performance stats

"Run Now" button on each node to manually trigger that agent/team

Reports (/reports)

Filterable list: by agent, by sector, by symbol, by report type, by date range

Search box for full-text search within report content

Click any report → full markdown-rendered report view (use react-markdown)

If report has child reports → show expandable tree of supporting reports

If report is linked to a decision → show decision outcome badge

Chat (/chat)

Full-screen chat interface (like ChatGPT UI)

Message bubbles with markdown rendering

Suggestion chips above input: "Portfolio overview", "Run full analysis", "Recent decisions", "Market update"

Settings changes show inline confirmation cards with "Apply" / "Cancel" buttons

Analysis results include embedded mini-charts and data tables

Real-time streaming of agent responses via WebSocket

Chat history persisted and scrollable

Settings (/settings)

Risk Profile section:

Aggressiveness slider (1-10) with label (1="Ultra Conservative" → 10="Aggressive Growth")

Allocation target editor: 3 number inputs (equity/FI/cash) that must sum to 100%, with visual pie chart preview

Position limit inputs: max single position %, max sector %

Minimum cash reserve %

Watchlist section: Add/remove symbols with autocomplete search

Schedule section: Read-only view of analysis schedule with "Run Now" button

All changes show a diff preview before saving

12.3 TypeScript Types (frontend/src/types/index.ts)

Define interfaces matching all backend Pydantic response schemas:

Portfolio, Holding, Transaction, CashBalance

RiskProfile, AllocationTargets

AnalysisReport, AgentDecision, DecisionTrail

Agent, AgentStatus

ChatMessage, ChatResponse

WSMessage

12.4 Real-Time Updates

The WebSocket hook (useWebSocket.ts) should:

Connect on app mount with auto-reconnection (exponential backoff, max 30s)

Dispatch incoming messages to the appropriate Zustand store

Show a toast notification for: new decisions, completed analysis cycles, errors

Update agent status indicators in real-time during analysis runs

Update portfolio values when price updates arrive

13. Infrastructure & Deployment
13.1 Docker Compose

text
services:
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: Superhuman Alpha_fund
      POSTGRES_USER: Superhuman Alpha
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "${DB_PORT:-5432}:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U Superhuman Alpha -d Superhuman Alpha_fund"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    ports:
      - "${REDIS_PORT:-6379}:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  chromadb:
    image: chromadb/chroma:0.5.23
    restart: unless-stopped
    ports:
      - "${CHROMA_PORT:-8100}:8000"
    volumes:
      - chromadata:/chroma/chroma
    environment:
      ANONYMIZED_TELEMETRY: "false"

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    ports:
      - "${BACKEND_PORT:-8080}:8080"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      chromadb:
        condition: service_started
    env_file: .env
    environment:
      DATABASE_URL: postgresql+asyncpg://Superhuman Alpha:${DB_PASSWORD}@db:5432/Superhuman Alpha_fund
      REDIS_URL: redis://redis:6379/0
      CHROMA_HOST: chromadb
      CHROMA_PORT: 8000
    volumes:
      - filing_data:/app/data/filings

  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.tasks.celery_app worker -l info -c 4 -Q default,analysis,data
    restart: unless-stopped
    depends_on:
      - backend
    env_file: .env
    environment:
      DATABASE_URL: postgresql+asyncpg://Superhuman Alpha:${DB_PASSWORD}@db:5432/Superhuman Alpha_fund
      REDIS_URL: redis://redis:6379/0
      CHROMA_HOST: chromadb
      CHROMA_PORT: 8000
    volumes:
      - filing_data:/app/data/filings

  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.tasks.celery_app beat -l info --scheduler celery.beat:PersistentScheduler
    restart: unless-stopped
    depends_on:
      - redis

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: unless-stopped
    ports:
      - "${FRONTEND_PORT:-3000}:80"
    depends_on:
      - backend

volumes:
  pgdata:
  chromadata:
  filing_data:
13.2 Backend Dockerfile

text
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY . .
RUN alembic upgrade head || true
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
13.3 Frontend Dockerfile

text
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
Frontend nginx.conf should proxy /api/* and /api/ws to the backend service.

14. Environment Configuration
.env.example

bash
# === REQUIRED ===
ANTHROPIC_API_KEY=sk-ant-xxx                    # Claude API key
FMP_API_KEY=xxx                                  # financialmodelingprep.com API key
SEC_USER_AGENT="Superhuman Alpha Fund admin@yourdomain.com"  # Required by SEC EDGAR

# === DATABASE ===
DB_PASSWORD=Superhuman Alpha_secure_password_change_me
DB_PORT=5432

# === REDIS ===
REDIS_PORT=6379

# === CHROMADB ===
CHROMA_PORT=8100

# === APP ===
BACKEND_PORT=8080
FRONTEND_PORT=3000
JWT_SECRET=change_this_to_a_random_string
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# === PORTFOLIO DEFAULTS ===
INITIAL_CASH_BALANCE=100000
DEFAULT_AGGRESSIVENESS=5

# === OPTIONAL ===
NEWSAPI_KEY=                                     # newsapi.org for news sentiment
ALPHA_VANTAGE_KEY=                               # Backup market data source

# === AUTH ===
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change_me                         # Hashed on first startup
15. Data Management Policies
Data Type	Hot Storage	Archive	Delete
Transaction history	Forever	Never	Never
Agent decisions	Forever	Never	Never
Analysis reports	2 years	Move to reports_archive table	Never
Daily price history	5 years	N/A	After 5 years
Intraday cache (Redis)	Market hours	N/A	TTL-based (5-60 min)
SEC filings (raw)	3 years	Move to cold storage	After 10 years
SEC filings (ChromaDB)	3 years	N/A	Rebuild from raw if needed
Earnings transcripts	5 years	N/A	After 5 years
Fundamental snapshots	5 years	N/A	After 5 years
Chat history	1 year	N/A	After 1 year
The weekly cleanup task handles all archival and deletion per this policy.

16. Testing Strategy
16.1 Test Structure

text
tests/
├── conftest.py          # Shared fixtures
├── test_tools/          # Unit tests for each tool (mock external APIs)
├── test_services/       # Unit tests for business logic
├── test_api/            # Integration tests for FastAPI endpoints
└── test_agents/         # Integration tests for agent teams (with real LLM)
16.2 Fixtures (conftest.py)

test_db: Async PostgreSQL test database (use testcontainers or SQLite for speed)

mock_yfinance: Mock yfinance responses with realistic data

mock_sec_edgar: Mock SEC EDGAR API responses

mock_fmp: Mock FMP API responses

sample_portfolio: Pre-populated portfolio with 10 holdings across 3 sectors

sample_reports: Pre-populated analysis reports at all hierarchy levels

test_client: FastAPI TestClient with auth headers

16.3 Test Requirements

All agent tools: test with mocked external APIs, verify return schema matches expected dict structure

Portfolio manager: test trade execution, constraint validation (especially no-margin enforcement), cash balance updates

API endpoints: test auth, CRUD operations, pagination, filtering

Chat router: test intent classification for each intent type with 3+ examples each

Decision trail: test report chain traversal returns correct hierarchy

WebSocket: test connection, message broadcasting, reconnection

16.4 Running Tests

bash
cd backend
pytest tests/ -v --asyncio-mode=auto -x
pytest tests/test_tools/ -v       # Fast, no LLM calls
pytest tests/test_agents/ -v -k "not slow"  # Skip full pipeline tests
17. Implementation Order
Build in this exact sequence. Each phase must be complete and passing tests before starting the next.

Phase 1: Foundation

Initialize project structure (all directories and __init__.py files)

pyproject.toml with all dependencies

config.py — Pydantic Settings

database.py — async engine + session

All SQLAlchemy models (models/)

Alembic setup + initial migration

docker-compose.yml (db, redis, chromadb only — no app containers yet)

seed_universe.py — populate stock universe by sector

Test: verify DB creates all tables, seed runs successfully

Phase 2: Agent Tools

Implement all 7 tool modules in agents/tools/

Write unit tests for each tool with mocked external APIs

Implement data_ingestion.py service (shared data fetching logic)

Implement sentiment_service.py

Test: all tool tests pass

Phase 3: Agent Hierarchy

Define state schemas (state.py)

Implement base_analyst.py — sector team factory

Implement one sector team fully (e.g., tech_analyst.py)

Test the single sector team end-to-end with 2-3 real stocks

Implement remaining 7 sector teams

Implement fixed income agents + supervisor

Implement macro agents + supervisor

Implement Risk Manager agent

Implement CIO agent

Implement CEO agent

Test: each supervisor correctly aggregates child agent reports

Phase 4: Orchestrator

Implement orchestrator.py — wire full graph

Test full pipeline with small universe (10 stocks, 3 sectors)

Verify: reports saved with correct parent-child relationships

Verify: CEO decisions reference supporting reports

Verify: no-margin constraint enforced at every level

Phase 5: Backend API

Implement all FastAPI routers

Implement portfolio_manager.py service

Implement report_service.py

Implement WebSocket connection manager + broadcasting

Implement chat_router.py with intent classification

Write API endpoint tests

Test: full API works with seeded data

Phase 6: Scheduling

Implement Celery app + beat schedule

Implement all 4 task modules

Test: data refresh tasks run successfully

Test: full analysis cycle completes end-to-end

Test: filing monitor detects mock new filing and triggers analysis

Phase 7: Frontend

Initialize React project with Vite + TypeScript + Tailwind + shadcn/ui

Implement API client + WebSocket client

Implement Zustand stores

Build Layout (sidebar + header)

Build Dashboard page

Build Portfolio page

Build Agents page (with tree visualization)

Build Reports page (with decision trail)

Build Chat page

Build Settings page

Test: all pages render correctly with mock data

Phase 8: Integration & Docker

Add backend + celery + frontend Dockerfiles

Complete docker-compose.yml with all services

Write setup_db.py for first-run initialization

Write README.md with complete setup instructions

End-to-end test: docker compose up, seed data, trigger analysis, verify UI

18. Hard Constraints
These constraints must be enforced at EVERY relevant layer. Violations are critical bugs.

NO MARGIN TRADING: Enforced at — DB CHECK constraint on Transaction.action, validate_trade tool, execute_trade tool, CEO system prompt, CIO system prompt. There is no code path that creates a short position or borrows funds.

CASH BALANCE ≥ 0: Enforced at — DB CHECK constraint on CashBalance.balance, execute_trade checks before decrementing.

POSITION LIMITS: Enforced at — validate_trade checks max_single_position_pct and max_sector_pct from RiskProfile before approving any trade.

MINIMUM CASH RESERVE: Enforced at — validate_trade ensures post-trade cash ≥ min_cash_pct × total_portfolio_value.

REPORT TRACEABILITY: Every AgentDecision.supporting_report_ids must reference valid AnalysisReport IDs. The decision trail from CEO to analyst must be navigable.

HUMAN SUPREMACY: Human settings changes always override agent recommendations. The human can reject any proposed trade. Auto-execution only happens for confidence ≥ 7.

RATE LIMITING: SEC EDGAR ≤ 10 req/sec. yfinance: use caching to minimize calls. FMP: respect free tier limits. All external calls use tenacity retry.

DATA PERSISTENCE: No analysis is ever performed without saving the report. Agent ephemeral reasoning is fine, but conclusions must be persisted.

19. Stretch Goals
Implement only if all core functionality is complete and tested:

Backtesting Module: Replay historical decisions using historical price data. Calculate hypothetical returns if all CEO decisions were auto-executed.

Email/SMS Alerts: Send notifications for high-confidence trades, significant portfolio changes, or analysis cycle completion. Use fastapi-mail or Twilio.

PDF Export: Generate PDF versions of executive summary reports using weasyprint.

Multi-Portfolio Support: Allow multiple portfolio instances (e.g., "Aggressive Growth", "Income", "Balanced") each with their own risk profile.

Tax-Lot Tracking: Track individual purchase lots for tax-loss harvesting suggestions.

Benchmark Comparison: Compare portfolio against multiple benchmarks (SPY, QQQ, sector ETFs).

Options Screening (cash-secured puts and covered calls only — NO naked options).

END OF SPECIFICATION

Claude Code: Read this entire document before writing any code. Follow the implementation order in Section 17 exactly. Ask clarifying questions if any requirement is ambiguous. Do not skip any phase. Write tests alongside implementation. Commit frequently with descriptive messages.

