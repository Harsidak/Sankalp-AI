# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Backend (`cd backend`, with `.venv` activated):

- `uvicorn app.main:app --reload --port 8000` — dev server
- `pytest tests/` — full suite; single test: `pytest tests/test_wellness.py::test_name`
- `python -m app.scripts.seed` — rebuild the demo account (`demo@sankalp.app` / `demo1234`) with 60 days of history; idempotent

Frontend (`cd frontend`):

- `npm run dev` / `npm run build` / `npm run preview`
- `npm run lint` — oxlint (config in `frontend/.oxlintrc.json`; React rules-of-hooks is an error)

## State of the repository

The committed history is a **different application** — a Jinja-templated Python
app under `app/`, `static/`, `templates/`. All of it is deleted in the working
tree and replaced, uncommitted, by the current backend/frontend split. So:

- `git show HEAD:<path>` is the only way to see the old code; files listed in
  commits do not exist on disk.
- The working tree, not `git log`, is the source of truth for what this project is.

## Architecture

Two applications in one repo, joined by an HTTP API.

**Backend** — FastAPI over async SQLAlchemy 2.0 against MySQL 8.0.

- Layering is strict: `routers/` handle HTTP and depend on `services/`;
  routers never touch the database directly.
- Services are module-level `async def` functions taking `db: AsyncSession`
  first, not classes. They call `db.flush()`, never `commit()` — the `get_db`
  dependency owns the transaction boundary.
- Responses are wrapped in `APIResponse[T]` / `PaginatedResponse[T]`
  (`schemas/common.py`), so every endpoint returns the same envelope.
- Primary keys are UUIDs stored as `CHAR(36)` via the `GUID` TypeDecorator in
  `core/types.py` — MySQL has no native UUID type. Use `GUID()`, never
  `postgresql.UUID`.
- `core/database.py` applies pool settings only for non-SQLite URLs, because
  the test suite runs the same engine factory against SQLite.
- Auth is JWT access/refresh with rotation; refresh tokens are stored hashed
  and revocable.

**Schema** (`models/wellness.py`) is a graded deliverable, so the constraints
are deliberate and worth preserving:

- Invariants live in the database, not in service code: `UNIQUE(user_id,
  checkin_date)`, `UNIQUE(habit_id, completed_date)`, `UNIQUE(user_id, name)`
  on tags.
- `entry_tags` resolves the journal↔tag many-to-many with a composite
  `(entry_id, tag_id)` primary key and no surrogate id.
- Every table carries `_MYSQL_OPTS` (InnoDB + utf8mb4) and cascades from
  `users` via `ON DELETE CASCADE`.
- Do not add an index whose leading columns already match a UNIQUE constraint;
  several were removed for exactly that reason.

**Frontend** — React 19 + Vite SPA. `src/api/client.js` is an axios instance
with interceptors that attach the access token and silently refresh on 401.
Auth state lives in `src/context/AuthContext.jsx`; routing in `src/routes/`,
where `ProtectedRoute` gates authenticated pages. Vite proxies `/api` to
`localhost:8000` in dev. Icons come from a single SVG sprite at
`public/icons.svg`, referenced as `<use href="/icons.svg#some-icon">`.

## Testing

`tests/conftest.py` swaps MySQL for SQLite and registers a connect listener
issuing `PRAGMA foreign_keys=ON` — without it SQLite ignores foreign keys and
the cascade tests pass for the wrong reason. `pytest.ini` sets
`asyncio_mode = auto`, so async tests need no decorator.

## Gotchas

- Deleting a row on one side of a `secondary` relationship does not update a
  collection already loaded in the session's identity map. `tag_service.delete`
  eagerly loads and explicitly detaches before deleting; a re-query would not
  fix it.
- `bcrypt` is pinned to 4.0.1 — 4.1+ removed `__about__`, which passlib 1.7.4
  reads on import.
- Scripts using the async engine must `await engine.dispose()` before exit or
  aiomysql raises on a closed event loop.
- Journal search uses `LIKE`, not the FULLTEXT index, because MySQL's
  natural-language mode ignores words shorter than `ft_min_token_size`.
