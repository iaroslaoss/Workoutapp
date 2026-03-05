# Lift & Move (Trainer Plan Builder MVP)

Monorepo containing:
- `backend`: FastAPI + SQLAlchemy 2.0 + Alembic + JWT auth
- `frontend`: React + TypeScript + Vite + Tailwind
- `docker-compose.yml`: Postgres + backend + frontend dev stack

## Prerequisites
- Docker + Docker Compose

## Quick Start
1. Copy env files (already included for local dev defaults):
   - `backend/.env`
   - `frontend/.env`
2. Start services:
   ```bash
   docker compose up --build
   ```
3. Run migrations:
   ```bash
   docker compose exec backend alembic upgrade head
   ```
4. Seed admin + global exercises:
   ```bash
   docker compose exec backend python -m scripts.seed
   ```
5. Open apps:
   - Frontend: http://localhost:5173
   - Backend docs: http://localhost:8000/docs

## Default Seeded Admin
- Email: `admin@liftmove.local`
- Password: `Admin123!`

## Backend Local Dev (without Docker app container)
1. Ensure Postgres is running (from compose `db`).
2. In `backend`:
   ```bash
   pip install -r requirements.txt
   alembic upgrade head
   python -m scripts.seed
   uvicorn app.main:app --reload --port 8000
   ```

## Frontend Local Dev
In `frontend`:
```bash
npm install
npm run dev
```

## Implemented v1 Scope
- Trainer register/login (JWT)
- Protected API routes
- Exercise bank CRUD + filters (name/category/equipment/muscle_group)
- Plan templates CRUD
- Plan days CRUD (`/plans/{id}/days`, `/days/{id}`)
- Plan exercises CRUD (`/days/{id}/exercises`, `/plan-exercises/{id}`)
- Client CRUD + assign template + assignment summary
- Read-only client view page
- Nice-to-have: duplicate plan template and duplicate day contents endpoints
- Alembic migration + seed data (~15 global exercises)
# Workoutapp
