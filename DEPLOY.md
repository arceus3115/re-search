# Deploy re-search (Render + GitHub Pages)

This guide deploys:

- **Backend (FastAPI)** → [Render free tier](https://render.com/docs/free)
- **Frontend (static site)** → GitHub Pages

## Architecture

```
Browser → GitHub Pages (frontend/dist)
       → Render web service (backend API)
       → OpenAlex, PCSAS, Gemini, etc.
```

---

## Step 1 — Deploy backend on Render (free tier)

### Option A: Blueprint (recommended)

1. Push this repo to GitHub.
2. Go to [Render Dashboard](https://dashboard.render.com/) → **New** → **Blueprint**.
3. Connect the `re-search` repository.
4. Render reads [`render.yaml`](render.yaml) and creates the `re-search-api` web service.

### Option B: Manual web service

1. **New** → **Web Service** → connect repo.
2. Settings:
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free
   - **Health Check Path:** `/health`

### Environment variables (Render dashboard)

| Key | Value | Required |
|-----|-------|----------|
| `GEMINI_API_KEY` | Your [Google AI Studio](https://aistudio.google.com/app/apikey) key | Yes (for AI features) |
| `ALLOWED_ORIGINS` | `https://YOUR_GITHUB_USERNAME.github.io` | Yes |
| `PYTHON_VERSION` | `3.11.7` | Set by Blueprint |

**Notes:**

- Free tier services **spin down after ~15 minutes** of inactivity. First request after idle can take 30–60 seconds (cold start).
- Render provides a URL like `https://re-search-api.onrender.com`. Copy this — you need it for GitHub Pages.

### Verify backend

```bash
curl https://YOUR-SERVICE.onrender.com/health
curl https://YOUR-SERVICE.onrender.com/api/v1/programs/stats
```

---

## Step 2 — Configure GitHub Pages frontend

### 2.1 Add GitHub secret

Repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Name | Value |
|------|-------|
| `RENDER_API_URL` | `https://YOUR-SERVICE.onrender.com` (no trailing slash) |

The workflow appends `/api/v1` at build time.

### 2.2 Enable GitHub Pages

1. Repo → **Settings** → **Pages**
2. **Source:** GitHub Actions
3. Push to `main` (or run the **Deploy frontend to GitHub Pages** workflow manually)

### 2.3 Site URL

For a project repo named `re-search`:

`https://YOUR_GITHUB_USERNAME.github.io/re-search/`

If you use a `username.github.io` root repo, change `PUBLIC_PATH` in [`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml) from `/${{ github.event.repository.name }}/` to `/`.

---

## Step 3 — Match CORS to your Pages URL

In Render, set:

```
ALLOWED_ORIGINS=https://YOUR_GITHUB_USERNAME.github.io
```

The browser `Origin` header is the host only (no `/re-search` path), so this is correct for project pages.

For local dev, `http://localhost:9000` is already allowed in [`backend/app/main.py`](backend/app/main.py).

---

## Step 4 — Smoke test

1. Open your GitHub Pages URL.
2. Open DevTools → **Network**.
3. Confirm API calls go to `https://YOUR-SERVICE.onrender.com/api/v1/...` (not `localhost`).
4. Test:
   - Load Programs (Program Discovery)
   - Create/save profile
   - Draft generation (needs valid `GEMINI_API_KEY`)

---

## Local development (unchanged)

**Terminal 1 — backend:**

```bash
cd backend
pipenv install
pipenv run start
```

**Terminal 2 — frontend:**

```bash
cd frontend
npm install
npm start
```

Frontend defaults to `/api/v1` and webpack proxies to `http://127.0.0.1:8000`.

To point local frontend at Render:

```bash
API_BASE_URL=https://YOUR-SERVICE.onrender.com/api/v1 npm start
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| API returns CORS error | Set `ALLOWED_ORIGINS` on Render to your `https://username.github.io` |
| `404` on `/api/v1/...` from Pages | `RENDER_API_URL` secret missing or wrong; rebuild Pages workflow |
| Slow first API call | Render free tier cold start — normal |
| `502` on PCSAS | PCSAS site unreachable or scrape validation failed — check Render logs |
| Port 8000 conflicts locally | Another app (e.g. Docker) may be on 8000; stop it or change backend port |
| AI features fail | Set `GEMINI_API_KEY` on Render and redeploy |

---

## Files added/changed for deployment

| File | Purpose |
|------|---------|
| [`render.yaml`](render.yaml) | Render Blueprint for free web service |
| [`backend/requirements.txt`](backend/requirements.txt) | Python deps for Render build |
| [`backend/app/main.py`](backend/app/main.py) | CORS + `/health` |
| [`frontend/src/config.ts`](frontend/src/config.ts) | Configurable API base URL |
| [`frontend/webpack.config.js`](frontend/webpack.config.js) | Production build → `dist/` |
| [`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml) | GitHub Pages CI |

See also: [GITHUB_PAGES_DEPLOYMENT.md](GITHUB_PAGES_DEPLOYMENT.md) for general Pages notes.
