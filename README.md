# Cold Email System (DIY)

Full DIY cold email system: FastAPI backend, custom Next.js admin panel, Supabase Postgres, GitHub Actions cron, SMTP rotation from DB.

## Features
- Mailboxes fully configurable from admin (add any SMTP mailbox directly)
- Campaigns with templates, personalization {{first_name}}, etc.
- Click tracking via redirect + open pixel (1x1 GIF) — clicks/replies are source of truth (opens unreliable)
- Unsubscribe link + suppression list
- Per-mailbox daily caps, warming, quarantine on repeated errors
- CSV lead upload with dedup + suppression
- JWT cookie auth for admin
- Scheduler via GitHub Actions hitting internal endpoint

## Stack
- Backend: FastAPI (Render/Fly/Railway free tier)
- Admin: Next.js (Vercel)
- DB: Supabase Postgres
- Tracking: same backend or behind your tracking domain

## Setup

### 1) Supabase
Run `sql/schema.sql` in Supabase SQL editor.

### 2) Backend
```bash
cd backend
cp .env.example .env  # fill values
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Or deploy with `render.yaml` / Docker.

### 3) Create admin
POST to `/auth/setup` with first admin:
```json
{"email": "admin@you.com", "password": "strongpass"}
```

### 4) GitHub Actions
Add secrets to repo:
- `API_BASE_URL` (e.g. https://your-backend.onrender.com)
- `CAMPAIGN_ID` (UUID of campaign to run)
- `INTERNAL_CRON_SECRET` (same as backend)

Workflow runs every 30 min.

### 5) Frontend
See `frontend/` README/env.

## Notes
- Store mailbox passwords securely. This is MVP — consider encryption at rest.
- Google may limit bulk sending; use caps + warmup.
- Tracking domain needs DNS + reverse proxy to backend.
- clicks/replies = real signals. opens are best-effort.
