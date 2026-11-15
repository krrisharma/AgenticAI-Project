# ClearPath Deployment Guide

ClearPath is architected for ultra-low memory consumption (< 512 MB RAM) to easily deploy on free container hosts (Render, Hugging Face Spaces, Railway) and free static web hosts (Vercel, Netlify, Cloudflare Pages).

---

## 1. Local Deployment with Docker Compose

Run both the FastAPI Backend (with LangGraph Agents) and the React Frontend:

```bash
# 1. Clone repository
git clone https://github.com/krrisharma/AgenticAI-Project.git
cd AgenticAI-Project

# 2. Configure environment
cp .env.example .env
# Edit .env and enter your free GROQ_API_KEY (optional: OPENAQ_API_KEY)

# 3. Start containers
docker compose up --build
```

- **Frontend:** http://localhost:5173
- **Backend API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/health

---

## 2. Deploying Backend to Free Tier (Render / Hugging Face Spaces)

### Render (Free Web Service)
1. Fork or push the repo to GitHub.
2. In Render Dashboard, click **New +** -> **Web Service**.
3. Select your repository.
4. **Environment:** `Docker` (Render will use `backend/Dockerfile`).
5. **Root Directory:** `.` or specify `backend` Dockerfile path `backend/Dockerfile`.
6. Add Environment Variables:
   - `GROQ_API_KEY`: Your Groq Cloud API key.
   - `CORS_ORIGINS`: Your frontend URL (e.g. `https://your-frontend.vercel.app`).
   - `NOMINATIM_USER_AGENT`: `clearpath-prod (contact: your-email)`.
7. Click **Create Web Service**.
*Note: Free tier services may spin down after inactivity; initial cold start takes ~30-50s.*

---

## 3. Deploying Frontend to Free Static Host (Vercel / Netlify)

### Vercel
1. In Vercel Dashboard, import git repository.
2. **Root Directory:** `frontend`
3. **Build Command:** `npm run build`
4. **Output Directory:** `dist`
5. **Environment Variable:**
   - `VITE_API_BASE_URL`: The deployed backend URL (e.g. `https://clearpath-api.onrender.com`).
6. Click **Deploy**.

### Netlify
1. New site from Git -> select repo.
2. Base directory: `frontend`
3. Build command: `npm run build`
4. Publish directory: `frontend/dist`
5. Set `VITE_API_BASE_URL` in Site configuration -> Environment variables.
