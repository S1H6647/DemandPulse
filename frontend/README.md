# DemandPulse frontend

Next.js App Router with TypeScript. A responsive forecast form uses dataset-backed
store/category choices and shows the exact calendar window before the selected
date. Results come from FastAPI; no predictions or data ranges are mocked.

Start the backend from the repository root:

```sh
uv run uvicorn app.main:app --reload
```

In another terminal:

```sh
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. The backend needs the CSVs and model described in the
root README. Node.js 20.9 or newer is required.

The Next.js server proxies `/api/options` and `/api/forecast` to FastAPI, avoiding
browser CORS setup. Set `BACKEND_URL` in `frontend/.env.local` if the backend runs
elsewhere (see `.env.example`). This variable is server-only. Restart Next.js after
changing it. Requests time out after 30 seconds and display a retryable error.

```sh
npm run typecheck
npm run build
npm start
```

The date panel shows the intended history window, not a guarantee of complete
observations for a store/family. Beyond-history and historical dates carry explicit
context. Editing inputs clears the previous result to avoid showing stale forecasts.
