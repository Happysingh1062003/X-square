<p align="center">
  <img src="https://img.shields.io/badge/GrowthOS-AI%20Powered-7c5cfc?style=for-the-badge&labelColor=0a0a0f" />
  <img src="https://img.shields.io/badge/Next.js-16-000?style=for-the-badge&logo=nextdotjs" />
  <img src="https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi" />
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=fff" />
</p>

# ⚡ GrowthOS

**AI-Powered Twitter/X Growth Platform** — Real-time virality modeling, audience-specific content personalization, and a closed-loop learning system that gets smarter with every tweet you publish.

> Built for solo thought leaders, growth agencies (50–500 accounts), and startup founders building in public.

---

## ✨ Features

### Phase 1 — MVP (Implemented)

| Feature | Description |
|---------|-------------|
| **🔥 Virality Scorer** | 12-feature scoring engine with per-account model training and sigmoid calibration |
| **🤖 AI Tweet Generator** | LLM pipeline with 3 production prompts (hooks, threads, replies), retry logic, structured output |
| **📅 Smart Scheduler** | Audience activity modeling, timezone-aware optimal posting, rate-limit-aware queue |
| **📊 Analytics Dashboard** | Real-time engagement tracking, hourly heatmaps, performance trends, top tweet ranking |
| **📡 Trend Radar** | Pre-viral signal detection — trends detected 12-24h before mainstream spike |

### Phase 2 — Intelligence Layer (Designed)

- Engagement Automation Engine
- Trend Detection (pre-viral signal detection)
- Strategy Engine (recommendations, adaptation loop)

### Phase 3 — Scale Layer (Architecture Notes)

- Multi-account management (agency use case)
- White-label API for third-party integration

---

## 🏗️ Architecture

```
growthOS/
├── backend/                    # Python / FastAPI
│   └── app/
│       ├── api/
│       │   └── router.py       # FastAPI routes + JWT auth
│       └── services/
│           ├── virality_scorer.py      # 12-feature virality scoring
│           ├── tweet_generator.py      # LLM pipeline + prompts
│           ├── scheduler.py            # Smart scheduling + rate limits
│           └── analytics_pipeline.py   # Async event ingestion
├── frontend/                   # Next.js 16 + TypeScript
│   └── src/
│       ├── app/
│       │   ├── layout.tsx      # Root layout
│       │   ├── page.tsx        # Dashboard orchestrator
│       │   └── globals.css     # Design system
│       ├── components/
│       │   ├── layout/
│       │   │   ├── Sidebar.tsx
│       │   │   └── Header.tsx
│       │   └── pages/
│       │       ├── OverviewPage.tsx
│       │       ├── ContentQueuePage.tsx
│       │       ├── GeneratorPage.tsx
│       │       ├── AnalyticsPage.tsx
│       │       └── TrendRadarPage.tsx
│       └── lib/
│           ├── mock-data.ts    # Mock data for frontend dev
│           └── store.ts        # Zustand state management
└── README.md
```

### Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Frontend** | Next.js 16, TypeScript, Recharts, Zustand, Lucide Icons | App Router, server components, fast dev |
| **Backend** | FastAPI, Pydantic, Celery, NumPy | Async-first, auto-generated API docs |
| **Database** | PostgreSQL + pgvector | Relational + vector similarity search |
| **Cache** | Redis | Rate limiting, event buffering, session cache |
| **Queue** | Celery + Redis | Scheduled posts, async LLM calls |
| **AI/ML** | GPT-4o-mini / GPT-4o, XGBoost, text-embedding-3-small | Task-specific model selection |
| **Vector Store** | Pinecone (MVP) / Qdrant (scale) | Topic clustering, semantic search |

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** ≥ 18
- **Python** ≥ 3.11
- **npm** or **yarn**

### Frontend

```bash
cd growthOS/frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

Open **http://localhost:3000** — the dashboard runs with mock data, no backend needed.

### Backend

```bash
cd growthOS/backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
# source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn pydantic numpy

# Run API server
uvicorn app.api.router:create_app --factory --reload --port 8000
```

Open **http://localhost:8000/docs** for the interactive API documentation.

---

## 📡 API Endpoints

### Content Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/generate/tweet` | Generate tweet/thread/reply variants |
| `GET` | `/api/v1/generate/quota` | Check remaining generation quota |

### Content Discovery

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/discover/trending` | Trending topics in niche |
| `GET` | `/api/v1/discover/viral` | Top viral tweets |
| `POST` | `/api/v1/discover/similar` | Semantic similarity search |

### Scheduling

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/schedule/queue` | Get scheduled post queue |
| `POST` | `/api/v1/schedule/post` | Add post to queue |
| `PATCH` | `/api/v1/schedule/post/{id}` | Update scheduled post |
| `DELETE` | `/api/v1/schedule/post/{id}` | Remove from queue |
| `POST` | `/api/v1/schedule/optimal-time` | Calculate optimal posting time |

### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/analytics/snapshot` | Analytics snapshot (24h/7d/30d/90d) |
| `GET` | `/api/v1/analytics/tweets` | Per-tweet performance data |
| `GET` | `/api/v1/analytics/audience` | Audience interest model |

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/auth/x/authorize` | Initiate X OAuth 2.0 flow |
| `GET` | `/api/v1/auth/x/callback` | OAuth callback handler |
| `POST` | `/api/v1/auth/refresh` | Refresh JWT token |

---

## 🧠 AI Pipeline

### Virality Scoring (12 Features)

```
Score = sigmoid(weighted_sum([
  engagement_rate,        # total engagements / impressions
  velocity,               # engagements per minute (first hour)
  amplification_ratio,    # (retweets + quotes) / (likes + replies)
  recency_decay,          # exponential decay from creation time
  follower_reach_ratio,   # impressions / follower count
  media_boost,            # video: 0.45, image: 0.25, poll: 0.35
  thread_depth_bonus,     # thread starters: 0.3
  quote_to_reply_ratio,   # quotes are higher-signal
  sentiment_polarity,     # strong opinions → viral
  topic_trending_score,   # hashtag trending momentum
  posting_hour_alignment, # optimal posting time match
  historical_author_virality  # author's track record
]))
```

### Closed-Loop Learning

```
Generate → Publish → Measure → Score → Update Profile → Generate (improved)
```

Every published tweet becomes a training sample. The system trains per-account XGBoost models weekly to personalize virality weights, optimal posting times, and content style.

---

## 🎨 Design System

Premium dark theme with:
- **Glassmorphism** cards with blur + transparency
- **Gradient accents** (`#7c5cfc` → `#c77dff` → `#e0aaff`)
- **Micro-animations** — hover lifts, skeleton loaders, pulse dots
- **Inter font** with 800-weight metric numbers
- Responsive down to mobile breakpoints

---

## 🗄️ Database

### PostgreSQL Tables

- `accounts` — User accounts and plans
- `x_connections` — OAuth tokens for X API (encrypted)
- `tweets` — Ingested tweets with embeddings (pgvector)
- `engagement_events` — Like, RT, reply, quote events
- `scheduled_posts` — Post queue with status tracking
- `analytics_snapshots` — Periodic rollup metrics
- `content_templates` — Reusable hook/CTA templates

### Redis Keys

| Pattern | Type | TTL | Purpose |
|---------|------|-----|---------|
| `session:{user}` | STRING | 24h | JWT session cache |
| `rate:{user}:{endpoint}` | ZSET | 60s | Sliding window rate limiter |
| `queue:{account}` | LIST | — | Scheduled post queue |
| `counters:{account}:{tweet}` | HASH | 48h | Real-time engagement counts |
| `trending:global` | ZSET | 15min | Current trending topics |

---

## ⚙️ Environment Variables

```env
# Backend
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://user:pass@localhost:5432/growthOS
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your-256-bit-secret
X_CLIENT_ID=your-x-oauth-client-id
X_CLIENT_SECRET=your-x-oauth-client-secret

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🛡️ X API Rate Limits

GrowthOS is designed around X API v2 constraints:

| Limit | Value | How We Handle It |
|-------|-------|-----------------|
| Monthly tweets | 1,500 (free) | Quota tracking with 90% safety margin |
| Requests / 15 min | 300 | Token bucket rate limiter |
| OAuth requirement | OAuth 2.0 PKCE | Built-in auth flow |

---

## 📜 License

MIT

---

<p align="center">
  <b>Built with intelligence, not just automation.</b>
</p>
