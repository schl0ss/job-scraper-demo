# Resume Audit Study — Workflow Automation System

A full-stack portal for managing job application submissions in an academic resume audit study. Research Assistants (RAs) claim job postings, submit applications using generated resumes, and log outcomes. Lead RAs monitor progress and administer the system.

---

## Architecture

```
├── app/                    FastAPI backend (Python)
│   ├── models/             SQLAlchemy ORM models
│   ├── schemas/            Pydantic request/response schemas
│   ├── routers/            API route handlers (auth, jobs, admin)
│   ├── services/           Business logic layer
│   └── db/                 Database engine and session factory
├── frontend/               React + TypeScript frontend (Vite)
│   └── src/
│       ├── pages/          Route-level page components
│       ├── components/     Shared UI components
│       └── styles/         Global CSS design tokens
├── employer_dedup.py       Tiered fuzzy employer deduplication engine
├── education_extractor.py  Rule-based education requirement parser
├── theirstack_client.py    TheirStack job data API client
└── demo.py                 Standalone pipeline demo (no server needed)
```

## Stack

| Layer | Technology |
|---|---|
| API | Python 3.11+, FastAPI, SQLAlchemy 2.0 (async) |
| Database | PostgreSQL (prod) / SQLite (local dev) |
| Auth | JWT via python-jose, bcrypt passwords |
| Frontend | React 18, TypeScript, React Router v6, Vite |
| Job data | TheirStack API (aggregates Indeed + 325k sources) |
| Fuzzy matching | rapidfuzz |

---

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+

### Backend

```bash
# Create and activate virtualenv
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt    # or: pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env — set SECRET_KEY and THEIRSTACK_API_KEY at minimum

# Start API server (SQLite used automatically for local dev)
uvicorn app.main:app --reload --port 8000
```

API runs at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`. Proxies `/api/*` to the backend automatically.

### First-time setup

Create the initial Lead RA account (run once after first backend start):

```bash
python3 -c "
import asyncio
from app.db.session import AsyncSessionLocal
from app.services.auth_service import create_user

async def main():
    async with AsyncSessionLocal() as db:
        await create_user(db, 'lead@yourdomain.edu', 'your-password', 'lead_ra')
        print('Lead RA created')

asyncio.run(main())
"
```

Additional RA accounts can be created through the Admin → Users UI once logged in.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL: `postgresql+asyncpg://user:pass@host/db` |
| `SECRET_KEY` | Yes | Random 64-char hex string for JWT signing |
| `THEIRSTACK_API_KEY` | Yes | From [theirstack.com](https://theirstack.com) — free tier: 200 credits/mo |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Default: 480 (8 hours) |
| `RESUME_PDF_DIR` | No | Default: `./resumes` |

Generate a secret key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## Database

The app auto-creates tables on startup in development. For production, use Alembic migrations:

```bash
alembic upgrade head
```

### Schema overview

| Table | Purpose |
|---|---|
| `users` | RA and Lead RA accounts with hashed passwords |
| `employers` | Canonical employer registry (deduplication target) |
| `employer_aliases` | Raw employer name strings → canonical employer |
| `job_postings` | Ingested job listings with education level and status |
| `assignments` | Active claims linking RAs to job postings (24hr lock) |
| `submissions` | Logged application outcomes with RA attribution |

---

## API Endpoints

### Auth
| Method | Path | Access | Description |
|---|---|---|---|
| POST | `/auth/login` | Public | Returns JWT token |
| POST | `/auth/users` | Lead RA | Create RA/Lead RA account |

### Jobs (RA-facing)
| Method | Path | Description |
|---|---|---|
| GET | `/jobs` | List queue — filter by `status`, `education_level` |
| GET | `/jobs/{id}` | Job detail including full description |
| POST | `/jobs/{id}/claim` | Lock job to current RA for 24 hours |
| DELETE | `/jobs/{id}/claim` | Release claim, return to available |
| POST | `/jobs/{id}/submission` | Log outcome: `applied`, `rejected`, `no_response`, `not_qualified`, `duplicate`, `no_longer_accepting` |
| GET | `/jobs/{id}/resume` | Download generated resume PDF |

### Admin (Lead RA only)
| Method | Path | Description |
|---|---|---|
| GET | `/admin/dashboard` | Progress stats and per-RA activity |
| POST | `/admin/ingest` | Fetch new jobs from TheirStack |
| POST | `/admin/stale/mark` | Flag claims older than 24h as stale |
| POST | `/admin/stale/reassign` | Reassign stale claim to another RA |
| GET | `/admin/export/csv` | Download all submissions as CSV |
| GET | `/admin/dedup/review` | Employer merge candidates needing review |

---

## Employer Deduplication

The system uses a 4-tier approach to prevent duplicate applicant names reaching the same employer:

1. **Normalized exact match** — lowercase, strip punctuation, remove common suffixes (Inc, LLC, Health, etc.)
2. **Fuzzy auto-merge** — `rapidfuzz` token sort ratio ≥ 0.95 → automatic merge
3. **Fuzzy + metro match** — score 0.80–0.95 + same metro area → merge
4. **Human review queue** — score 0.80–0.95, different metros → flagged for Lead RA

The canonical employer registry grows over time. Accuracy improves as more postings are processed.

## Education Requirement Extraction

Job descriptions are parsed on ingestion to determine minimum education requirement (`AA`, `BA`, or `unspecified`). This determines how many resume variants to generate per posting (2 or 3).

The extractor uses regex patterns for common degree keywords ("Bachelor's required", "BA/BS", "4-year degree", "Associate's degree", etc.) with surrounding context analysis to distinguish required vs. preferred qualifications.

---

## Deployment (Railway)

See deployment instructions in `DEPLOY.md` (to be added before go-live).

**Quick reference:**
- Set all env vars in Railway dashboard
- `DATABASE_URL` is auto-provided by Railway's PostgreSQL plugin
- Run `alembic upgrade head` as a deploy command
- Frontend can deploy to Railway static site or Vercel

---

## Key Design Decisions

**Why TheirStack over direct Indeed scraping?**
Indeed's official API is deprecated and their job detail pages are protected by Cloudflare. TheirStack provides structured data including full descriptions via a compliant API ($59–200/mo for production volume).

**Why SQLite for local dev?**
Zero-config setup. The SQLAlchemy async driver (`aiosqlite`) is a drop-in replacement for `asyncpg`. Switch to PostgreSQL in production by changing `DATABASE_URL`.

**Why no email notifications?**
The core claim/submit workflow doesn't require them and email infrastructure adds deployment complexity. Can be added post-launch.
