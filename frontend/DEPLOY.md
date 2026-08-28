# Deploy to Vercel
1. Import repo into Vercel from GitHub.
2. Set Root Directory = `frontend/` (or move `vercel.json` to repo root and set directory to `LeakLens/frontend`).
3. Once deployed, note the URL (e.g. https://leaklens.vercel.app).
4. Set the backend URL in the frontend: either edit `index.html` to set `window.BACKEND_URL = 'https://leaklens-api.onrender.com'`, or configure the backend to serve the static file at `/` (already does via `main.py` `/`).
