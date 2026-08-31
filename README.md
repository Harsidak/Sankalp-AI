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

## License

MIT
