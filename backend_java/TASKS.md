# Sankalp – Java backend: who does what

This folder is the Java (Spring Boot) version of the Python backend in `../backend`.
It talks to the **same MySQL database** and exposes the **same URLs and JSON**, so the React app works with it unchanged.

## How to run

1. MySQL running, database `sankalp` created, tables created by the Python side once (`cd backend && alembic upgrade head`, optionally `python -m app.scripts.seed` for demo data).
2. Install JDK 21+ and Maven (IntelliJ already has both built in).
3. Set your DB password: environment variable `DB_PASSWORD` (see `src/main/resources/application.properties` for all settings).
4. `mvn spring-boot:run` -> server on http://localhost:8000
5. Check it: `curl http://localhost:8000/api/v1/health`
6. React: stop the Python server, then `cd frontend && npm run dev` (Vite already forwards `/api` to port 8000).

## The rule every module follows

```
Controller   (HTTP only: read request, call service, wrap in ApiResponse)
   -> Service      (the rules / logic, @Transactional)
       -> Repository   (talks to MySQL; Spring writes the SQL)
           -> Entity       (one class = one table)
```
`XxxDtos.java` holds the request/response shapes (records). A controller never touches a repository.

## The one contract between modules

Every module except `auth`, `health`, `ai-models` needs to know **who is logged in**.
The auth module's `JwtFilter` must:

1. read the header `Authorization: Bearer <access token>`,
2. check the token, find the user id inside it,
3. do `request.setAttribute("userId", <that id as String>)`,
4. otherwise answer **401**.

Controllers then simply declare `@RequestAttribute("userId") String userId`. (Look at `habits/HabitController.java`.)
`JwtFilter` must let `/api/v1/auth/login`, `/api/v1/auth/register`, `/api/v1/auth/refresh` and `/api/v1/health` through **without** a token.
Until `JwtFilter` exists, nothing that needs a user will work, so **auth is the first thing to finish**.

The JSON envelope is always `ApiResponse` (`common/ApiResponse.java`); errors are thrown as `NotFoundException` / `ConflictException` and turned into JSON in `common/ErrorHandler.java`.

---

## Module status

| Module      | Status                 | Owner |
|-------------|------------------------|-------|
| health      | done                   |       |
| habits      | done                   |       |
| journal     | done                   |       |
| tags        | done                   |       |
| dashboard   | done                   |       |
| insights    | done                   |       |
| ai          | done                   |       |
| **auth**    | **empty – teammate**   |       |
| **users**   | **empty – teammate**   |       |
| checkins    | done                   |       |

(Dashboard and insights read the `checkins` table with plain SQL, so they do not depend on the checkins Java code.)

---

## Teammate task 1 – AUTH (do this first)

Files (all empty now): `auth/AuthController`, `AuthService`, `AuthDtos`, `JwtService`, `JwtFilter`, `RefreshToken`, `RefreshTokenRepository`.
Python to read: `backend/app/routers/auth.py`, `services/auth_service.py`, `core/security.py`, `schemas/auth.py`.
Table: `refresh_tokens` (+ `users`, see task 2).
Libraries already in `pom.xml`: `spring-security-crypto` (BCrypt), `jjwt` (JWT). Secret: `jwt.secret` in `application.properties`.

Endpoints (all under `/api/v1/auth`):

| Method | URL | Body | Does |
|---|---|---|---|
| POST | `/register` | email, password (min 8), full_name | create user (hash password with BCrypt), return tokens. Email already used -> `ConflictException` |
| POST | `/login` | email, password | check password, return tokens. Wrong -> 401 |
| POST | `/refresh` | refresh_token | check it is stored, not revoked, not expired; revoke it; return a NEW pair (this is "rotation") |
| GET | `/me` | – | the logged-in user (id, email, full_name, avatar_url, auth_provider, is_verified) |
| POST | `/logout` | refresh_token | mark that refresh token revoked |

Token response (snake_case JSON): `access_token`, `refresh_token`, `token_type` ("bearer"), `expires_in` (seconds).
Rules: access token lives 15 min, refresh token 7 days; the token's `sub` = user id; the refresh token is stored **hashed** (SHA-256), never as plain text.
Also: `JwtFilter` (see contract above). Skip Google login.
Tip: passwords already in the DB were hashed by Python's bcrypt (`$2b$...`) – Spring's `BCryptPasswordEncoder` can check those, so the demo user `demo@sankalp.app / demo1234` will log in.

## Teammate task 2 – USERS

Files (empty): `users/User`, `UserRepository`, `UserService`, `UserController`, `UserDtos`.
Python to read: `routers/users.py`, `services/user_service.py`, `models/user.py`, `schemas/user.py`.
Table: `users`. The `User` entity is also needed by auth (register/login look users up by email).

Endpoints (under `/api/v1/users`):

| Method | URL | Does |
|---|---|---|
| GET | `/me` | profile of the logged-in user |
| PUT | `/me` | update full_name / avatar_url |
| PUT | `/me/password` | body current_password + new_password; wrong current -> error |

Optional extras if time allows: `GET /me/export`, `DELETE /me`.
Tip: the table has `UNIQUE(email)`; ids are 36-character strings (UUID) – copy how `habits/Habit.java` does the id.

## Teammate task 3 – CHECKINS

Files (empty): `checkins/CheckIn`, `CheckInRepository`, `CheckInService`, `CheckInController`, `CheckInDtos`.
Python to read: `routers/checkins.py`, `services/checkin_service.py`, `schemas/wellness.py` (top part), `models/wellness.py` (class `CheckIn`).
Table: `checkins` – has `UNIQUE(user_id, checkin_date)`: one check-in per user per day.

Endpoints (under `/api/v1/checkins`):

| Method | URL | Does |
|---|---|---|
| GET | `` | list check-ins, oldest first. Query: `start`+`end` dates, or `days` (default 30) |
| GET | `/today` | today's check-in or null |
| GET | `/streak` | `{current_streak, longest_streak, checked_in_today}` – same logic as the habit streaks in `habits/HabitService.java` |
| POST | `` | create (or replace today's if it already exists): mood_score 1-5, energy_score 1-5, note (max 2000), checkin_date (optional, not in the future) |
| PATCH | `/{id}` | change mood_score / energy_score / note |
| DELETE | `/{id}` | delete |

Tip: the best templates are `tags` (simple CRUD) and `habits` (dates + streaks). Copy their structure.

---

## Finished modules – one line each (so you can explain them)

- **health** – `GET /health`: runs `select 1`; says connected / disconnected.
- **tags** – CRUD on labels. Name is lowercased, unique per user (409 if repeated). List shows how many entries use each tag.
- **habits** – CRUD + `POST /{id}/log` which ticks/unticks a day (insert/delete one `habit_logs` row). Streaks are calculated in Java from the dates.
- **checkins** – one mood/energy rating per day; posting twice re-rates the same day. `/today` returns null when nothing is recorded, `/streak` anchors on today/yesterday and looks back a year for the longest run.
- **journal** – CRUD + search (`LIKE`) + filter by tags + pages. Tags attach through the `entry_tags` join table (many-to-many).
- **dashboard** – one endpoint, five SQL queries (mood per day, averages, entry count, top tags, habit completions).
- **insights** – SQL that relates mood to habits / weekdays / tags, plus a one-sentence headline written from the numbers.
- **ai** – talks to an OpenAI-compatible API. `/inference` = full answer, `/stream` = answer word by word (SSE), `/reflect` = short reflection, `/models`.
  Set `AI_API_KEY` (and `AI_BASE_URL` / `AI_MODEL` for NVIDIA etc.) before using it.
