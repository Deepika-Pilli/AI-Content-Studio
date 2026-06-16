# AI Content Studio - Deployment Guide

## Local Development Setup

### Prerequisites
- Python 3.12+
- Node.js 20+
- Git

### Backend Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/AI-Content-Studio.git
cd AI-Content-Studio

# Create and configure environment
cp backend/.env.example backend/.env
# Edit backend/.env and set your GROQ_API_KEY

# Install Python dependencies
pip install -r backend/requirements.txt

# Run the backend
cd backend
py -3.12 -m uvicorn backend.app.main:app --reload --port 8001
```

### Frontend Setup
```bash
# In a new terminal, from the project root
cd frontend
npm install

# Run the development server
npm run dev
```

Open http://localhost:5173 in your browser.

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | **Yes** | - | Your Groq API key for LLM access |
| `API_KEY` | No | `dev-key-change-in-production` | API key for frontend-to-backend auth |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Groq model name |
| `CHUNK_SIZE` | No | `1000` | Text chunk size for RAG |
| `CHUNK_OVERLAP` | No | `200` | Chunk overlap for RAG |
| `EMBEDDING_MODEL` | No | `sentence-transformers/all-MiniLM-L6-v2` | HuggingFace embedding model |
| `MAX_FILE_SIZE_MB` | No | `10` | Max upload file size in MB |

### Frontend (`frontend/.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `VITE_API_URL` | No | `http://127.0.0.1:8001` | Backend API URL |
| `VITE_API_KEY` | No | (empty) | API key sent as `X-API-Key` header |

---

## GitHub Setup

### Initialize Repository
```bash
git init
git add .
git commit -m "Initial commit: AI Content Studio"
git branch -M main
git remote add origin https://github.com/yourusername/AI-Content-Studio.git
git push -u origin main
```

### .gitignore
The following are already excluded:
- `backend/.env` - API keys and secrets
- `backend/uploads/` - Uploaded documents
- `backend/vectors/` - FAISS indexes
- `__pycache__/` - Python cache
- `node_modules/` - npm packages
- `.vscode/`, `.idea/` - IDE settings

---

## Render Backend Deployment

### Step 1: Push to GitHub
Ensure your repository is pushed to GitHub.

### Step 2: Create Render Web Service
1. Log in to [Render Dashboard](https://dashboard.render.com)
2. Click **New +** → **Web Service**
3. Connect your GitHub repository
4. Configure:
   - **Name:** `ai-content-studio-backend`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `uvicorn backend.app.main:app --host 0.0.0.0 --port 10000`
   - **Root Directory:** `backend`
5. Add Environment Variables:

| Key | Value |
|---|---|
| `GROQ_API_KEY` | `gsk_your_key_here` |
| `API_KEY` | `generate-a-random-secret` |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` |
| `CHUNK_SIZE` | `1000` |
| `CHUNK_OVERLAP` | `200` |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` |
| `MAX_FILE_SIZE_MB` | `10` |

6. Click **Create Web Service**

> **Note:** On Render's free tier, the embedding model (~80 MB) will be downloaded on every deploy. Consider using a paid plan with persistent disk.

### Step 3: Get Backend URL
After deployment, Render provides a URL like:
```
https://ai-content-studio-backend.onrender.com
```

---

## Vercel Frontend Deployment

### Step 1: Prepare Frontend
The frontend is already configured to work with Vite. No additional build configuration is needed.

### Step 2: Deploy to Vercel
1. Log in to [Vercel Dashboard](https://vercel.com)
2. Click **Add New...** → **Project**
3. Import your GitHub repository
4. Configure:
   - **Framework Preset:** `Vite`
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
5. Add Environment Variables:

| Key | Value |
|---|---|
| `VITE_API_URL` | `https://ai-content-studio-backend.onrender.com` |
| `VITE_API_KEY` | `same-api-key-as-backend` |

6. Click **Deploy**

### Step 3: Get Frontend URL
After deployment, Vercel provides a URL like:
```
https://ai-content-studio.vercel.app
```

---

## Production Environment Variables

### Backend (Render)
| Variable | Production Value |
|---|---|
| `GROQ_API_KEY` | `gsk_...` (your actual key) |
| `API_KEY` | Random UUID or secure token |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` |
| `CHUNK_SIZE` | `1000` |
| `CHUNK_OVERLAP` | `200` |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` |
| `MAX_FILE_SIZE_MB` | `10` |

### Frontend (Vercel)
| Variable | Production Value |
|---|---|
| `VITE_API_URL` | `https://your-backend.onrender.com` |
| `VITE_API_KEY` | Same as backend `API_KEY` |

---

## Verify Deployment

### Backend Health (public)
```bash
curl https://your-backend.onrender.com/healthz
# Response: {"status": "ok"}
```

### Backend Status (public)
```bash
curl https://your-backend.onrender.com/
# Response: {"status": "ok", "message": "AI Content Studio Backend Running", ...}
```

### Protected Endpoint (requires API key)
```bash
curl -H "X-API-Key: your-api-key" https://your-backend.onrender.com/generate/ \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello"}'
```

---

## Docker Deployment (Alternative)

### Build and Run with Docker Compose
```bash
# Set your API key
export GROQ_API_KEY=gsk_your_key_here

# Build and start
docker compose up --build -d

# Check health
curl http://localhost:8001/healthz
```

### Stop
```bash
docker compose down
```

---

## Troubleshooting

### Backend won't start
- Check `GROQ_API_KEY` is set correctly
- Ensure all dependencies are installed: `pip install -r backend/requirements.txt`
- Check Python version: `python --version` (must be 3.12+)

### Frontend shows "Network Error"
- Verify the backend is running: `curl http://localhost:8001/healthz`
- Check `VITE_API_URL` in `frontend/.env.development` matches backend URL
- Check `VITE_API_KEY` matches backend's `API_KEY`
- Verify CORS headers in browser network tab

### CORS errors in browser
- Ensure the backend's `allow_origins` includes your frontend URL
- For Vercel, add your Vercel domain to `allow_origins` in `backend/app/main.py`

### Upload fails with 413
- Increase `MAX_FILE_SIZE_MB` in backend environment
- Default is 10 MB

### RAG query fails with 503
- Check `GROQ_API_KEY` is valid and has sufficient quota
- Check Groq service status at https://status.groq.com