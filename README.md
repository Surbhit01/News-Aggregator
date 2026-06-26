# News Aggregator

A personalized news aggregator that uses AI to discover, summarize, and deliver relevant news. Built with FastAPI + LangGraph + React.

## Features

- **Personalized Discovery** — RSS feeds categorized by your interests
- **AI Summaries** — TL;DR and key takeaways via LLM (OpenAI, Gemini, Ollama, etc.)
- **Bias Detection** — Source bias indicators + AI-powered perspective analysis
- **Impact Radar** — Identifies who/what the news impacts
- **Morning Briefing** — Daily curated digest delivered on schedule
- **Implicit Learning** — Preferences evolve based on what you read
- **Feedback Loop** — 👍/👎/✕ to fine-tune recommendations

---

## Quick Start

### Prerequisites

- [Python 3.12+](https://python.org)
- [Node.js 22+](https://nodejs.org)
- [uv](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Backend

```bash
cd backend
cp .env.example .env       # Edit .env with your settings
uv sync                    # Install Python deps
uv run uvicorn app.main:app --reload  # Start at :8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                # Start at :5173 (proxies to :8000)
```

Open **http://localhost:5173** — register an account and set your preferences.

---

## Project Structure

```
news-aggregator/
├── backend/                    # FastAPI + LangGraph
│   ├── app/
│   │   ├── main.py            # Entry point, lifespan, routers
│   │   ├── core/              # Config, LLM provider
│   │   ├── db/                # Models, session, CRUD
│   │   ├── agents/            # LangGraph pipeline (8 agents)
│   │   ├── api/routes/        # 7 route groups
│   │   ├── services/          # RSS, cache, scheduler, digest
│   │   └── schemas/           # Pydantic models
│   ├── tests/                 # 73 tests
│   └── Dockerfile
├── frontend/                   # React + Vite + Tailwind
│   ├── src/
│   │   ├── api/               # Axios client + 6 API modules
│   │   ├── components/        # ArticleCard, BiasIndicator, etc.
│   │   ├── pages/             # 5 route pages
│   │   └── context/           # Auth context
│   └── Dockerfile
├── docker-compose.yml          # Full stack with PostgreSQL + Redis
├── .github/workflows/         # CI/CD pipeline
├── docs/
│   ├── ARCHITECTURE.md        # Technical architecture deep-dive
│   ├── CODE_REVIEW.md         # Code review findings
│   └── DEPLOYMENT_PLAN.md     # Deployment guide
├── mvp_tracker.md              # Development checklist
├── user_personas.md           # Test personas and flows
└── project_plan.md            # Original plan
```

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/register` | No | Register new user |
| POST | `/api/auth/login` | No | Login, get JWT |
| GET | `/api/auth/me` | Yes | Current user profile |
| GET | `/api/preferences` | Yes | Get preferences |
| PUT | `/api/preferences` | Yes | Update preferences |
| GET | `/api/preferences/stats` | Yes | Preference statistics |
| GET | `/api/digest` | Yes | Get morning briefing or on-demand digest |
| GET | `/api/digest/articles` | Yes | List articles with sort/filter |
| GET | `/api/digest/articles/{id}/tldr` | Yes | TL;DR for an article |
| POST | `/api/feedback` | Yes | Submit 👍/👎/✕ feedback |
| POST | `/api/history/log` | Yes | Log article read |
| GET | `/api/history` | Yes | Get reading history |
| GET | `/api/alerts` | Yes | Get actionable alerts |
| GET | `/api/biases` | No | List source biases |
| POST | `/api/biases` | Yes | Add/update source bias |
| DELETE | `/api/biases/{domain}` | Yes | Remove source bias |
| GET | `/api/health` | No | Health check |

Full interactive docs at **http://localhost:8000/docs** (Swagger UI).

---

## Configuration

Key environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./news_aggregator.db` | Database connection |
| `SECRET_KEY` | `change-me-in-production` | JWT signing key |
| `LLM_ENABLED` | `true` | Set false for extractive-only (no API calls) |
| `LLM_API_KEY` | — | API key for OpenAI/Gemini/etc. |
| `LLM_MODEL` | `gpt-4o-mini` | Model name |
| `LLM_BASE_URL` | — | Custom URL for non-OpenAI providers |
| `MORNING_BRIEFING_TIME` | `07:00` | Daily briefing cron time |

### LLM Provider Presets

| Provider | `LLM_BASE_URL` | Example Model |
|----------|----------------|---------------|
| OpenAI | (default) | `gpt-4o-mini` |
| Gemini | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-2.0-flash` |
| Ollama | `http://localhost:11434/v1` | `llama3.2` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| Kimi | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |

---

## Docker Deployment

```bash
cp .env.example .env         # Edit with your secrets
docker compose up -d         # Start: PostgreSQL + Redis + Backend + Frontend
docker compose logs -f       # Watch logs
docker compose down          # Stop
```

### Production (Railway)

1. Push to GitHub
2. Connect repo to [Railway](https://railway.app)
3. Add PostgreSQL + Redis add-ons
4. Set env vars: `SECRET_KEY`, `LLM_API_KEY`, `DATABASE_URL`
5. Deploy — CI pipeline runs tests automatically

---

## Testing

```bash
cd backend
uv run pytest -v              # 73 tests
uv run pytest tests/test_personas.py -v  # Persona-based integration tests
```

---

## Documentation

| Document | Description |
|----------|-------------|
| `docs/ARCHITECTURE.md` | System architecture, data flow, agent pipeline, every layer explained |
| `docs/CODE_REVIEW.md` | Code review findings, bugs, improvements |
| `docs/DEPLOYMENT_PLAN.md` | Deployment strategy and steps |
| `mvp_tracker.md` | Development progress checklist |
| `user_personas.md` | Test personas with step-by-step test flows |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, LangGraph, SQLAlchemy |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS v4 |
| Database | SQLite (dev) / PostgreSQL (production) |
| Cache | Redis (with in-memory fallback) |
| LLM | OpenAI SDK (multi-provider: OpenAI, Gemini, Ollama, DeepSeek, Kimi) |
| Async | APScheduler, asyncio |
| Auth | bcrypt + JWT (python-jose) |
| CI/CD | GitHub Actions, Railway |

---

## License

MIT