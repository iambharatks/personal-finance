# Finance Command Center

A personal finance app for one person: import bank data, see where the money goes, edit and
categorise it. FastAPI + SQLAlchemy on the server, React + TypeScript + Tailwind on the client.

Status: **Milestone 1** — dashboard (KPIs, balance, monthly cash flow, spending by category)
and a transaction grid with filters, sorting and inline editing.

## Run it on this PC

Needs [uv](https://docs.astral.sh/uv/) and Node.js 20+.

```powershell
.\dev.ps1
```

Open http://localhost:5173. The first run creates `private/finance.db`. To load the bank
history, put the curated CSV at `private/seed/transactions.csv` and run:

```powershell
cd server
uv run python -m app.cli seed
```

Locally there is no login unless a password is set (see below).

## Where things live

```
vercel.json        how the two halves are deployed
dev.ps1            runs both halves locally
private/           YOUR DATA - never committed (see .gitignore)
server/app/
  models.py          database tables
  filters.py         the one filter object every endpoint accepts
  services/metrics.py  the only place that defines income, spending, savings rate
  routers/           HTTP endpoints, all under /api
  seed.py, cli.py    loading data and maintenance commands
  auth.py            password login
server/migrations/ database schema history (Alembic)
client/src/
  api/               typed API access; schema.d.ts is generated
  lib/               formatting (₹, dates) and filter presets
  components/        layout and shared pieces
  features/          one folder per page: auth, dashboard, transactions
```

Two rules keep the numbers trustworthy:

- **Every figure is defined once**, in `server/app/services/metrics.py`. A group's `kind`
  (`income`, `expense`, `tax`, `invest`, `transfer`, `neutral`) decides how it counts.
- **Balances are never stored.** They are worked out from the account's opening balance
  plus its transactions, so an edit or a late import can never leave them stale.

## Commands

Run from `server/`. Each prints which database it is about to touch.

| Command | What it does |
|---|---|
| `uv run python -m app.cli migrate` | create or upgrade the tables |
| `uv run python -m app.cli seed` | load `private/seed/transactions.csv` (safe to repeat) |
| `uv run python -m app.cli set-password` | make a password hash for the host |
| `uv run python -m app.cli set-password --write-env` | turn the login on locally |
| `uv run python -m app.cli backup` | dump every table to `private/backups/` |
| `uv run pytest` | server tests |
| `uv run ruff check .` | lint |

Run from `client/`:

| Command | What it does |
|---|---|
| `npm run typecheck` / `npm test` / `npm run build` | checks |
| `npm run gen:api` | regenerate API types (after the next two lines) |

After changing a server schema:

```powershell
cd server; uv run python -m app.cli openapi --out ..\client\src\api\openapi.json
cd ..\client; npm run gen:api
```

After changing `models.py`:

```powershell
cd server
uv run alembic revision --autogenerate -m "what changed"
uv run python -m app.cli migrate
```

## Deploy for free (Vercel + Neon)

The client is served as static files, the API runs as a Vercel Function, and the data lives
in Neon Postgres. Both free plans are enough for one person and neither needs a card.

1. Push this folder to a **private** GitHub repository.
2. In Vercel: **Add New → Project**, import the repository. `vercel.json` describes the rest.
3. In the project's **Storage** tab add **Neon** (free plan). It sets `DATABASE_URL`.
   Pick a region near you, then set **Settings → Functions → Region** to the same one.
4. On this PC, create the secrets and add both to **Settings → Environment Variables**:
   ```powershell
   cd server; uv run python -m app.cli set-password
   ```
5. Still on this PC, point the commands at Neon for one session and load the data:
   ```powershell
   $env:DATABASE_URL = "<the Neon connection string>"
   uv run python -m app.cli migrate
   uv run python -m app.cli seed
   Remove-Item Env:\DATABASE_URL
   ```
6. Redeploy. Open the site and sign in.

Later schema changes: run `migrate` against Neon the same way before pushing.

## Privacy

- Everything personal stays in `private/`, which git ignores. Check before any push:
  `git ls-files private` must print nothing.
- Deployed, the app refuses to start without a password. Sessions are HttpOnly cookies;
  five wrong passwords lock that address out for 15 minutes.
- Once deployed, the transactions sit in Neon's database. The password is the only gate,
  so choose a long one.
