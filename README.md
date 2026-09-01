# SankalpAI

A mental-wellness companion: daily mood check-ins, a tagged journal, habit
streaks, and an analytics dashboard built on top of all three.

## Tech Stack

| Layer    | Technology                              |
| -------- | --------------------------------------- |
| Backend  | FastAPI (Python 3.11+), async SQLAlchemy |
| Database | MySQL 8.0 (InnoDB, utf8mb4)             |
| Frontend | React 19 + Vite                         |
| Auth     | JWT access/refresh + Google OAuth 2.0   |
| AI       | OpenAI / Google Gemini (pluggable)      |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- MySQL 8.0 running locally
- An OpenAI or Google AI key (only needed for `/ai/*` endpoints)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux/Mac

pip install -r requirements.txt
cp .env.example .env            # then edit DATABASE_URL and the secrets

python -m app.scripts.seed      # optional: demo account + 60 days of data
uvicorn app.main:app --reload --port 8000
```

Tables are created on startup by `init_db()`. The seed script builds a demo
account — `demo@sankalp.app` / `demo1234` — with 60 days of check-ins,
journal entries, tags, habits, and logs. It is idempotent.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env

npm run dev
```

Vite proxies `/api` to `http://localhost:8000`, so the dev server works
without CORS configuration.

### Docker (full stack)

```bash
cp .env.example .env
docker-compose up --build
```

Compose brings up MySQL with a healthcheck; the backend waits for it.

## Tests and Lint

```bash
cd backend  && pytest tests/           # single test: pytest tests/test_wellness.py::test_name
cd frontend && npm run lint            # oxlint
```

The backend suite runs against SQLite rather than MySQL, with
`PRAGMA foreign_keys=ON` so the cascade tests are meaningful.

## API Documentation

With the backend running:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
Sankalp-AI/
├── backend/            # FastAPI backend
│   ├── app/
│   │   ├── models/     # SQLAlchemy ORM (auth + wellness domain)
│   │   ├── schemas/    # Pydantic request/response models
│   │   ├── services/   # Business logic; routers never touch the DB
│   │   ├── routers/    # HTTP endpoints
│   │   └── scripts/    # seed.py
│   ├── alembic/        # Migrations
│   └── tests/
├── frontend/           # React + Vite SPA
│   └── src/            # api/, pages/, routes/, context/, hooks/
└── docker-compose.yml
```

## Database Schema

Six wellness tables alongside the auth tables, all InnoDB/utf8mb4 with
`ON DELETE CASCADE` down from `users`:

- `checkins` — `UNIQUE(user_id, checkin_date)` enforces one per day
- `journal_entries` / `tags` / `entry_tags` — a true many-to-many, the join
  table keyed on the composite `(entry_id, tag_id)`
- `habits` / `habit_logs` — `UNIQUE(habit_id, completed_date)`; completion is
  row presence, so marking done is an insert and undoing it is a delete

## Feature Inventory

Every feature this system can reasonably carry, split into what is **built and
working today** and what is **still possible**. The "possible" half is ordered
by what a grader would actually notice, not by what is fun to build.

Two constraints shaped this list, and should keep shaping it:

- **The showcase is the JavaScript and the database schema.** AI is a thin
  slice — one API call — not the centre of the project.
- **Under a week.** Anything that needs a new infrastructure piece (a queue, a
  worker, a second datastore, a mobile build) is out of scope and is marked so.

### 1. Built and working

#### Authentication & accounts

| Feature | Where |
|---|---|
| Email + password registration with strength rules | `POST /auth/register` |
| Login issuing a JWT access/refresh pair | `POST /auth/login` |
| **Refresh-token rotation** — the old token is revoked as the new one is issued | `POST /auth/refresh` |
| Refresh tokens stored **hashed**, never in plaintext, and individually revocable | `refresh_tokens` table |
| Logout (revokes one token) and revoke-all-sessions | `POST /auth/logout` |
| Google OAuth — both the authorization-code and the ID-token flow | `POST /auth/google` |
| Silent re-auth in the browser: a 401 refreshes and replays the original request | `api/client.js` |
| Concurrent-401 queueing, so ten parallel calls trigger **one** refresh | `failedQueue` in `client.js` |
| Protected routes that wait for auth to resolve before deciding | `ProtectedRoute.jsx` |
| Profile read/update, password change | `/users/me`, `/users/me/password` |
| Rate limiting on auth endpoints | `core/cache.py` |

#### Daily check-ins

- One mood (1–5) and energy (1–5) rating per calendar day, plus an optional note.
- **Upsert semantics** — `UNIQUE(user_id, checkin_date)` makes "create" and
  "edit" the same action; re-rating a day updates it rather than duplicating it.
- Backfill: any past day can be selected and rated; future dates are rejected
  by a validator, not by the UI alone.
- Streak computation — current run *and* longest run anywhere in the last year,
  anchored on today-or-yesterday so an unfinished today does not read as broken.
- A 35-day heat strip, coloured by mood, where each cell jumps to that day.

#### Journal

- Full CRUD on entries with a title and body.
- **Tags as a real many-to-many** — `entry_tags` with a composite
  `(entry_id, tag_id)` primary key and no surrogate id.
- Tag CRUD with `UNIQUE(user_id, name)`, lowercase normalisation, and a colour.
- Server-side search across title and body (`LIKE`, deliberately — MySQL's
  natural-language FULLTEXT mode ignores words shorter than `ft_min_token_size`).
- Filter by any combination of tags, combined with search.
- Server-side pagination with a proper `PaginatedResponse` envelope.
- Tag chips carry a live entry count.

#### Habits

- CRUD with a name, icon, colour, and a weekly target (1–7).
- **Completion is row presence**, not a boolean — `UNIQUE(habit_id, completed_date)`.
  The toggle endpoint inserts or deletes one row.
- Current and longest streak per habit, recomputed server-side on every toggle.
- A 14-day toggle grid; the UI applies the returned result in place rather than
  re-fetching, so ~70 cells stay responsive.
- Archive/restore, separate from delete.

#### Dashboard

- One request supplies the whole page, so no two cards can disagree about which
  window they describe.
- Mood/energy trend line over a selectable 7/30/90-day window.
- Average mood, average energy, longest streak, journal count.
- Per-habit completion rings against a pro-rated target.
- Top tags by frequency.

#### Insights — the analytics showcase

Four SQL aggregations, none of it stored, none of it computed in Python:

1. **Habit → mood impact.** Average mood on days a habit was kept versus days it
   was not, via a conditional `AVG(CASE WHEN …)` over an outer join *whose NULL
   side carries the meaning* ("no log row that day" = missed). Measured from the
   earlier of the habit's creation and its first log, using a correlated
   subquery that needs its own `aliased()` because the table is already in the
   enclosing FROM.
2. **Mood by weekday**, Monday-first, portable across MySQL's `DAYOFWEEK()`
   (1=Sun) and SQLite's `strftime('%w')` (0=Sun) by rotating both.
3. **Score distribution** — every check-in bucketed 1–5, including empty buckets.
4. **Mood by journal tag** — tags joined through `entry_tags` to entries, then
   LEFT JOINed to that day's check-in, so a tag on an unrated day still counts
   as an entry but contributes no mood.

Plus a **plain-language headline** that names the strongest signal — and
**stays silent** when the evidence is thin (a 4-day minimum on each side and a
0.3-point floor). A wellness app that invents correlations from three data
points is worse than one that says nothing.

#### Account & data

- **Whole-account export** as one JSON document — check-ins, entries with their
  tags resolved to names, habits with their completed dates, tags — plus a row
  count per table so it can be checked against the database at a glance.
- Browser-side download of that export (built from the response, because the
  endpoint needs an `Authorization` header a plain link cannot send).
- **Permanent account deletion** behind a typed `DELETE` phrase and the current
  password. One `DELETE` against `users` empties every dependent table via
  `ON DELETE CASCADE` — the response reports exactly what went with it.

#### AI (deliberately thin)

- `POST /ai/reflect` — a single call that reads recent check-ins and entries
  back to the user as a short reflection.
- Generic inference / streaming / embeddings endpoints exist behind the same
  service.

#### Cross-cutting

- Every endpoint returns the same `APIResponse[T]` / `PaginatedResponse[T]`
  envelope.
- Strict layering: routers do HTTP, services do work, routers never touch the DB.
- Services take `db: AsyncSession` first and call `flush()`, never `commit()` —
  the `get_db` dependency owns the transaction boundary.
- UUID primary keys as `CHAR(36)` via a `GUID` TypeDecorator, since MySQL has no
  native UUID type.
- Light/dark theme across the whole app, driven entirely by design tokens.
- **67 passing tests**, including cascade tests that cannot pass for the wrong
  reason (`PRAGMA foreign_keys=ON` is forced on the SQLite test engine).
- A seed script that builds 60 days of *non-uniform* history — weekly rhythm,
  real gaps, habits that get easier over time — because flat data makes a
  working dashboard look broken.

### 2. Still possible — ranked by what a grader notices

#### Tier 1 — high visible value, low cost (a day or less each)

| Feature | Why it lands | Sketch |
|---|---|---|
| **Wire up the chat tables** | `chat_sessions` / `chat_messages` already exist in the schema with **no router and no service**. An unused table is a visible smell; two tables' worth of CRUD closes it. | A `chat_service`, a `/chat` router, and persist what `/ai/reflect` already produces. |
| **A written schema/ER document** | DBMS courses grade the *design*, and right now the reasoning lives only in code comments. | One page: ER diagram, every constraint, and *why* — the composite PK, the two UNIQUEs, the cascade, the indexes deliberately **not** added because a UNIQUE already leads with those columns. |
| **Saved views / smart filters** | Cheap, and shows query composition. | Persist a named filter (tags + date range + search) per user; one small table. |
| **Weekly summary card** | Reuses the aggregation you already have. | "This week vs last week" — mood delta, habits kept, entries written. |
| **CSV export alongside JSON** | Trivial next to the existing export. | Same service, a different serializer. |
| **Empty-state onboarding** | The demo account looks great; a *new* account currently looks broken. | A first-run checklist: first check-in → first habit → first entry. |

#### Tier 2 — real substance, ~1–2 days each

| Feature | Why it lands | Sketch |
|---|---|---|
| **Goals with milestones** | A new entity with a genuine one-to-many, plus derived progress. | `goals` + `goal_milestones`, progress computed in SQL from completed milestones. |
| **Mood ↔ sleep correlation** | Extends the insight engine with a second variable. | Add a sleep-hours column to check-ins; the same conditional-aggregation pattern. |
| **Journal prompts** | Makes the blank page less blank; a small reference table. | A `prompts` table, one served per day, deterministic per user+date. |
| **Full-text search done properly** | Directly addresses a documented limitation. | A FULLTEXT index with `IN BOOLEAN MODE`, falling back to `LIKE` for short terms. |
| **Tag co-occurrence** | A genuinely interesting self-join over `entry_tags`. | "stress appears with sleep in 60% of entries" — one self-join, one GROUP BY. |
| **Habit calendar heatmap (full year)** | The visual everyone recognises. | You already have the data; it is a rendering task. |
| **Soft delete + restore for entries** | Shows you understand the difference between deactivating and destroying. | `deleted_at` plus a filtered default query and a trash view. |
| **Audit log** | Classic DBMS coursework material. | An `activity_log` table written by the service layer; a "recent activity" feed. |

#### Tier 3 — impressive but expensive; pick at most one

| Feature | Cost | Note |
|---|---|---|
| **Database views / stored procedures / triggers** | Low code, high syllabus value | e.g. a view for the weekly rollup, or a trigger maintaining a denormalised streak. Worth it *only* if your syllabus asks for them — otherwise it fights the ORM. |
| **Alembic migrations** | Half a day | Currently `init_db()` creates the tables. Migrations are the professional answer and are easy to demo. |
| **Role-based access (admin view)** | A day | A second role plus an aggregate-over-all-users screen. Adds an authorization dimension. |
| **Shared/accountability habits** | 1–2 days | A join table between users and habits; introduces multi-user relationships. |
| **Email reminders** | Needs a scheduler | Out of scope this week — a real background worker is infrastructure, not a feature. |
| **Mobile app / PWA offline sync** | Days | Out of scope. Conflict resolution alone is bigger than the rest of the project. |
| **Real-time multi-device sync (WebSockets)** | Days | Out of scope, and the app has no genuine need for it. |

#### Deliberately not worth building

- **Heavier AI** — a RAG pipeline, embeddings search over journals, a
  multi-turn therapy agent. It contradicts the stated focus, and it is the part
  a grader can least easily verify.
- **Microservices / Docker Compose orchestration** — ceremony without a
  question it answers.
- **A second database** (Redis, Mongo) — the rate limiter's in-memory cache is
  honest about being in-memory; swapping it for Redis adds an install step and
  demonstrates nothing new.

### 3. Known gaps in what is already built

Worth fixing before adding anything new:

1. **`Chat.jsx` is still RAG-era** — it targets an interface that no longer
   matches `/ai/reflect`.
2. **No Alembic** — `init_db()` creates tables at startup. Fine for a demo,
   not defensible as a deployment story.
3. **`/ai/reflect` needs a key** — `OPENAI_API_KEY` or `GOOGLE_API_KEY` in
   `backend/.env`, or the endpoint fails at call time rather than at startup.
4. **A brand-new account has no guided path** — every screen is an empty state
   at once.
5. **No server-side pagination on check-ins** — bounded by `days` instead,
   which is fine at this scale but is not the same thing.

## License

MIT
