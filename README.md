# TaskPilot: an AI agent that manages your tasks

**Project chosen: B (TaskPilot).** Users manage a to-do list by chatting with an LLM agent. The agent decides which tool to call (add, list, update, delete, assign), changes the data in Postgres, and shows exactly which tools it used. Roles are enforced on the backend.

## Live app
| | |
|---|---|
| Frontend | `https://taskpilot-taskpilot2.vercel.app` |
| Backend | `https://taskpilot-g5l3.onrender.com` (API docs at `/docs`) |
| Admin login | `admin@taskpilot.dev` / `AdminPass123!` |
| User login | `user@taskpilot.dev` / `DemoPass123!` |

> The backend runs on Render's free plan: it sleeps after 15 minutes idle and the first request can take about a minute. If login seems stuck, wait and retry.

## Tech stack and why
- **FastAPI + SQLAlchemy + Pydantic**: required backend; typed request validation and automatic `/docs`.
- **Groq (`llama-3.3-70b-versatile`)**: free tier, fast, supports native tool calling. Model name is an env var.
- **Neon Postgres**: free hosted Postgres whose data survives restarts (Render's disk does not).
- **Own JWT auth + bcrypt**: small and easy to explain; no third-party auth service.
- **React + Vite**: simple SPA, plain CSS, no UI library. Deployed on Vercel.

## Run locally
```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # fill DATABASE_URL, JWT_SECRET, GROQ_API_KEY, seed passwords
python -m scripts.seed      # creates demo admin + user (reads .env values from your shell, see note)
uvicorn app.main:app --reload   # http://localhost:8000/docs

# frontend (new terminal)
cd frontend
cp .env.example .env
npm install && npm run dev      # http://localhost:5173

# tests (no network, fake LLM)
cd backend && pytest -q
```
Note: the seed script reads `ADMIN_PASSWORD` / `DEMO_PASSWORD` from the environment. Run it as
`set -a; source .env; set +a; python -m scripts.seed` (macOS/Linux) or set the variables in PowerShell first.
If `DATABASE_URL` is not set, the app falls back to a local SQLite file for development only.

## How the AI part works
1. `POST /chat` sends the user's message, the last 10 chat messages, and a system prompt containing today's date, weekday and the IST timezone (so "by Friday" becomes a real date).
2. The LLM may reply with one or more tool calls. The backend executes each, appends the results, and calls the LLM again. This loops (max 5 steps) until the LLM answers in plain text. That is how "mark the report done and add a task to start the next one" runs two tools.
3. **Safe by design:** tool schemas contain no `user_id`. The backend injects the logged-in user and every query filters by it. Any `user_id` the model invents is discarded. Even if the model is tricked by a prompt, it can only reach the current user's rows.
4. LLM timeouts, rate limits or malformed tool calls return a friendly message instead of a crash.

## Login and roles
- Sign-up and login use JWT (12h expiry). Passwords are hashed with bcrypt.
- Sign-up has no role field and always creates `role = "user"`. Admins are created only by `scripts/seed.py`.
- Roles are checked on the backend: `require_admin` guards every `/admin/*` route and reads the role from the database on each request, not from the token. A normal user calling `/admin/users` gets **403**.
- `assign_task` is hidden from non-admin users' tool list and re-checked inside the tool.
- The frontend only shows the admin page to admins, but that is cosmetic; the backend is the real gate.

## Extra features (beyond the minimum)
1. **Confirmation before deleting**: `delete_tasks` never deletes directly. It saves a pending action; the user clicks Delete or Keep them. Confirm/cancel endpoints only accept the owner's actions.
2. **Tool-call trace**: each reply shows chips such as `add_task(title="...", due_date="2026-11-20")`; failed calls are marked red.
3. **Natural-language dates** resolved with the current date in IST.
4. **Admin tool `assign_task`**: admins can say "assign X to user@example.com by Friday".
5. Task checkbox toggle, overdue highlighting, priorities, suggestion buttons (including a daily summary prompt).
6. Automated tests (`backend/tests`) covering role enforcement, user isolation, multi-step tool use, confirmation flow, and LLM failure handling.

## Not finished / could be improved
- Chat history lives in the browser only (resets on refresh); it is not saved in the database.
- No password reset, email verification or rate limiting.
- Admin page is read-only (no user management UI).
- Agent quality depends on the free model; very ambiguous requests may need a follow-up.
- Reminders and notifications are not implemented.

