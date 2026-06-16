# 🚀 AI Content Studio

<div align="center">

**AI-powered content generation and RAG (Retrieval-Augmented Generation) platform**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=white)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[![Groq](https://img.shields.io/badge/Groq-LLM-FF6F00?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com/)
[![FAISS](https://img.shields.io/badge/FAISS-Vector_Store-0052CC?style=for-the-badge&logo=meta&logoColor=white)](https://faiss.ai/)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)

</div>

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Environment Variables](#-environment-variables)
- [Local Development Setup](#-local-development-setup)
- [API Endpoints](#-api-endpoints)
- [Deployment](#-deployment)
- [Screenshots](#-screenshots)
- [Future Improvements](#-future-improvements)

---

## 🎯 Project Overview

**AI Content Studio** is a full-stack application that combines AI-powered content generation with a complete RAG (Retrieval-Augmented Generation) pipeline. Users can generate social media posts, blog articles, and emails using Groq's LLM, upload and index documents, and ask questions about their documents using semantic search.

### Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React 19 + Vite 8 | Modern, responsive UI |
| **Backend** | FastAPI (Python 3.12) | High-performance REST API |
| **LLM** | Groq (llama-3.3-70b) | AI content generation & RAG answers |
| **Vector Store** | FAISS (IndexFlatIP) | Semantic similarity search |
| **Embeddings** | Sentence-Transformers (all-MiniLM-L6-v2) | Text-to-vector conversion |
| **Text Extraction** | PyMuPDF, Mammoth | PDF/DOCX text extraction |
| **Auth** | API Key (X-API-Key header) | Simple, secure authentication |

---

## ✨ Features

### ✅ AI Content Generation
Generate high-quality content for multiple platforms with custom tone and style control.

| Content Type | Tone Options | Parameters |
|---|---|---|
| LinkedIn Post | Professional, Casual | Max Tokens, Temperature |
| Blog Article | Humorous, Formal | Content length control |
| Twitter/X Post | All tones | 280-char optimized |
| Email | Professional greeting/closing | Subject line generation |
| General Content | Any tone | Fully customizable |

### ✅ Document Upload
Upload PDF, DOCX, and TXT files with automatic text extraction and metadata generation.

- **Formats Supported:** `.pdf`, `.docx`, `.txt`
- **Max File Size:** 10 MB (configurable)
- **Text Extraction:** UTF-8/TXT, Mammoth (DOCX), PyMuPDF (PDF)
- **Metadata:** File size, character count, page estimate, preview

### ✅ Document Indexing
Transform uploaded documents into searchable vector indexes using state-of-the-art embeddings.

- **Chunking:** RecursiveCharacterTextSplitter (configurable size/overlap)
- **Embeddings:** Sentence-Transformers (384-dim vectors)
- **Vector Store:** FAISS IndexFlatIP (cosine similarity)
- **Persistence:** Saved to `/vectors` directory as `.faiss` + `.meta`

### ✅ RAG Chat
Ask natural language questions about your documents and get grounded answers with source citations.

- **Retrieval:** Top-k semantic search across document chunks
- **Generation:** Context-grounded answers via Groq LLM
- **Attribution:** Source chunk references with relevance scores
- **Transparency:** Expandable source details in chat

### ✅ API Key Authentication
All protected endpoints require `X-API-Key` header. Public endpoints available for health checks.

| Public Endpoints | Protected Endpoints |
|---|---|
| `GET /` | `POST /generate/` |
| `GET /healthz` | `POST /upload/` |
| `GET /test-key` | `POST /index/{id}` |
| `GET /docs` | `POST /retrieve/` |
| `GET /openapi.json` | `POST /rag/query` |

### ✅ Document Library
Browse all uploaded documents with indexing status at a glance.

- **Uploaded Documents:** ID, size, upload timestamp
- **Indexed Status:** ✅ Indexed / ⏳ Pending badges
- **Refresh Button:** Manual reload

### ✅ Health Monitoring
Lightweight health check endpoint for Docker/Kubernetes orchestrators.

```
GET /healthz → {"status": "ok"}
```

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React + Vite)                   │
│  ┌──────────┐ ┌──────────────┐ ┌──────────┐ ┌────────────────┐ │
│  │Dashboard │ │  Content Gen │ │Doc Upload│ │   RAG Chat     │ │
│  └──────────┘ └──────────────┘ └──────────┘ └────────────────┘ │
│                         │  Axios API Calls                       │
│                   ┌─────┴─────┐ X-API-Key Auth                   │
└───────────────────┼───────────┼──────────────────────────────────┘
                    │           │
┌───────────────────┼───────────┼──────────────────────────────────┐
│                   ▼           ▼          Backend (FastAPI)        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Auth Middleware                         │   │
│  └──────────┬───────────────┬──────────────┬─────────────────┘   │
│             ▼               ▼              ▼                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐              │
│  │ /generate/   │ │  /upload/    │ │  /rag/query  │              │
│  │ Groq Service │ │ Upload Svc   │ │ RAG Pipeline │              │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘              │
│         │                │                │                       │
│         ▼                ▼                ▼                       │
│  ┌──────────┐    ┌──────────────┐  ┌──────────────────┐          │
│  │  Groq    │    │  File System │  │ FAISS + Metadata │          │
│  │  API     │    │  /uploads    │  │ /vectors         │          │
│  └──────────┘    └──────────────┘  └──────────────────┘          │
└──────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Upload:** File → Validation → Text Extraction → Disk Storage
2. **Index:** Text → Chunking → Embeddings → FAISS Index → Disk Persistence
3. **Generate:** Prompt → System Prompt → Groq API → Formatted Content
4. **RAG Query:** Question → Embedding → FAISS Search → Context Building → Groq API → Answer + Sources

---

## 📁 Project Structure

```
AI-Content-Studio/
├── backend/
│   ├── .env                    # Environment variables (gitignored)
│   ├── .env.example            # Environment template
│   ├── .gitignore
│   ├── Dockerfile              # Production Docker image
│   ├── requirements.txt        # Python dependencies
│   └── app/
│       ├── main.py             # FastAPI app entry point
│       ├── config.py           # Settings & configuration
│       ├── middleware/
│       │   ├── __init__.py
│       │   └── auth.py         # X-API-Key authentication
│       ├── models/
│       │   ├── __init__.py
│       │   ├── request_models.py   # Pydantic request schemas
│       │   ├── response_models.py  # Pydantic response schemas
│       │   └── upload_models.py    # Upload-specific models
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── health.py       # GET /, /healthz, /test-key
│       │   ├── generation.py   # POST/GET /generate/
│       │   ├── upload.py       # GET/POST /upload/
│       │   ├── indexing.py     # GET/POST /index/
│       │   ├── retrieval.py    # POST /retrieve/
│       │   └── rag.py          # POST /rag/query
│       ├── services/
│       │   ├── __init__.py
│       │   ├── groq_service.py     # Groq LLM integration
│       │   └── upload_service.py   # File handling & text extraction
│       └── rag/
│           ├── __init__.py
│           ├── text_splitter.py    # RecursiveCharacterTextSplitter
│           ├── embeddings.py       # HuggingFace embeddings
│           ├── vector_store.py     # FAISS index management
│           ├── indexing_service.py # Indexing orchestrator
│           ├── retrieval_service.py# Semantic search
│           └── rag_service.py      # RAG pipeline orchestrator
├── frontend/
│   ├── .env                   # Frontend env vars (gitignored)
│   ├── .env.development       # Development environment
│   ├── .env.production        # Production environment template
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx           # React entry point
│       ├── App.jsx            # Router configuration
│       ├── index.css          # Full dark theme (700+ lines)
│       ├── api/
│       │   └── client.js      # Axios API client
│       ├── components/
│       │   ├── Layout.jsx     # App shell with sidebar
│       │   └── Sidebar.jsx    # Navigation sidebar
│       └── pages/
│           ├── Dashboard.jsx       # Health + feature cards
│           ├── ContentGenerator.jsx # AI content creation
│           ├── DocumentUpload.jsx   # Upload + index wizard
│           ├── DocumentLibrary.jsx  # Document browser
│           ├── RagChat.jsx          # Q&A interface
│           └── Settings.jsx         # Config reference
├── docker-compose.yml         # Production Docker setup
├── DEPLOYMENT.md              # Full deployment guide
└── README.md                  # This file
```

---

## 🔧 Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | ✅ **Yes** | — | Your Groq API key for LLM access |
| `API_KEY` | ❌ No | `dev-key-change-in-production` | API key for X-API-Key auth |
| `GROQ_MODEL` | ❌ No | `llama-3.3-70b-versatile` | Groq model identifier |
| `CHUNK_SIZE` | ❌ No | `1000` | Text chunk size (characters) |
| `CHUNK_OVERLAP` | ❌ No | `200` | Overlap between chunks |
| `EMBEDDING_MODEL` | ❌ No | `sentence-transformers/all-MiniLM-L6-v2` | HuggingFace embedding model |
| `MAX_FILE_SIZE_MB` | ❌ No | `10` | Max upload file size |

### Frontend (`frontend/.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `VITE_API_URL` | ❌ No | `http://127.0.0.1:8001` | Backend API base URL |
| `VITE_API_KEY` | ❌ No | — | API key for X-API-Key header |

---

## 💻 Local Development Setup

### Prerequisites

- Python 3.12+
- Node.js 20+
- Git

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/AI-Content-Studio.git
cd AI-Content-Studio

# Create environment file
cp backend/.env.example backend/.env

# Edit backend/.env and add your Groq API key
# GROQ_API_KEY=gsk_your_key_here

# Install Python dependencies
pip install -r backend/requirements.txt

# Start the backend server
cd backend
py -3.12 -m uvicorn backend.app.main:app --reload --port 8001
```

The backend will be available at **http://127.0.0.1:8001** with Swagger docs at **http://127.0.0.1:8001/docs**.

### Frontend Setup

```bash
# In a new terminal, from the project root
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at **http://localhost:5173**.

---

## 📡 API Endpoints

### Public Endpoints (no auth required)

| Method | Endpoint | Description | Response |
|---|---|---|---|
| `GET` | `/` | Health check with config status | `{"status": "ok", "groq_configured": true, ...}` |
| `GET` | `/healthz` | Lightweight orchestrator health | `{"status": "ok"}` |
| `GET` | `/test-key` | Check Groq API key status | `{"status": "ok", "message": "API Key Found"}` |
| `GET` | `/docs` | Swagger UI documentation | HTML page |
| `GET` | `/redoc` | ReDoc documentation | HTML page |
| `GET` | `/openapi.json` | OpenAPI schema | JSON schema |

### Protected Endpoints (require `X-API-Key` header)

#### Content Generation

```http
POST /generate/
Content-Type: application/json
X-API-Key: your-api-key

{
  "prompt": "Write a LinkedIn post about AI in healthcare",
  "content_type": "linkedin",
  "tone": "professional",
  "max_tokens": 512,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "success": true,
  "content": "Artificial intelligence is transforming healthcare...",
  "model": "llama-3.3-70b-versatile",
  "content_type": "linkedin",
  "usage": {
    "prompt_tokens": 45,
    "completion_tokens": 156,
    "total_tokens": 201
  }
}
```

#### Document Upload

```http
POST /upload/
Content-Type: multipart/form-data
X-API-Key: your-api-key

file: @document.pdf
```

**Response:**
```json
{
  "success": true,
  "message": "File 'document.pdf' uploaded successfully",
  "document": {
    "id": "upload_a1b2c3d4_document.pdf",
    "file_size_display": "240.00 KB",
    "extension": ".pdf",
    "text_length": 12500,
    "uploaded_at": "2026-06-12T21:30:00.000000"
  }
}
```

#### List Uploaded Documents

```http
GET /upload/
X-API-Key: your-api-key
```

**Response:**
```json
{
  "success": true,
  "total": 3,
  "documents": [
    {
      "id": "upload_a1b2_doc.pdf",
      "file_size_display": "240.00 KB",
      "uploaded_at": "2026-06-12T21:30:00"
    }
  ]
}
```

#### Document Indexing

```http
POST /index/{document_id}
X-API-Key: your-api-key
```

**Response:**
```json
{
  "success": true,
  "message": "3 chunks → 3 vectors (dim=384)",
  "total_chunks": 3,
  "total_vectors": 3,
  "embedding_model": "all-MiniLM-L6-v2"
}
```

#### List Indexed Documents

```http
GET /index/
X-API-Key: your-api-key
```

**Response:**
```json
{
  "success": true,
  "total": 1,
  "indexes": [
    {
      "document_id": "upload_a1b2_doc.pdf",
      "total_chunks": 3,
      "total_vectors": 3
    }
  ]
}
```

#### RAG Query

```http
POST /rag/query
Content-Type: application/json
X-API-Key: your-api-key

{
  "document_id": "upload_a1b2_doc.pdf",
  "question": "What does AI do in healthcare?",
  "top_k": 3
}
```

**Response:**
```json
{
  "success": true,
  "answer": "Based on the document, AI transforms healthcare through... [Source 1]...",
  "retrieved_chunks": [
    {"chunk_index": 0, "score": 0.5819, "text": "..."},
    {"chunk_index": 1, "score": 0.5650, "text": "..."}
  ],
  "model": "llama-3.3-70b-versatile"
}
```

---

## 🚀 Deployment

### Render (Backend)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

1. Push repository to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com) → **New +** → **Web Service**
3. Connect your GitHub repository
4. Configure:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `uvicorn backend.app.main:app --host 0.0.0.0 --port 10000`
5. Add environment variables (see [Environment Variables](#-environment-variables))
6. Click **Create Web Service**

### Vercel (Frontend)

[![Deploy to Vercel](https://vercel.com/button)](https://vercel.com/new)

1. Go to [Vercel Dashboard](https://vercel.com) → **Add New...** → **Project**
2. Import your GitHub repository
3. Configure:
   - **Framework Preset:** `Vite`
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. Add environment variables:
   - `VITE_API_URL` = your Render backend URL
   - `VITE_API_KEY` = your API_KEY
5. Click **Deploy**

### Docker (Alternative)

```bash
# Build and run with Docker Compose
export GROQ_API_KEY=gsk_your_key_here
docker compose up --build -d

# Verify
curl http://localhost:8001/healthz
```

> For detailed deployment instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md).

---

## 📸 Screenshots

> *Screenshots coming soon*

| Page | Preview |
|---|---|
| **Dashboard** | ![Dashboard](https://via.placeholder.com/600x350?text=Dashboard) |
| **Content Generator** | ![Generator](https://via.placeholder.com/600x350?text=Content+Generator) |
| **Document Upload** | ![Upload](https://via.placeholder.com/600x350?text=Document+Upload) |
| **Document Library** | ![Library](https://via.placeholder.com/600x350?text=Document+Library) |
| **RAG Chat** | ![Chat](https://via.placeholder.com/600x350?text=RAG+Chat) |
| **Settings** | ![Settings](https://via.placeholder.com/600x350?text=Settings) |

---

## 🔮 Future Improvements

- [ ] **Multi-document search** — Query across all indexed documents simultaneously
- [ ] **Conversation history** — Persistent chat history with context-aware follow-ups
- [ ] **Cross-encoder re-ranker** — Improve result relevance with Cohere/Cross-encoder
- [ ] **Dark/Light mode toggle** — Theme switching with CSS variables
- [ ] **User authentication** — Login/signup with JWT tokens
- [ ] **Document management** — Delete endpoints, folder organization
- [ ] **Batch upload** — Upload multiple files at once
- [ ] **Export functionality** — Download generated content as .docx/.pdf
- [ ] **Webhook integrations** — Connect to Slack, Discord, Notion
- [ ] **Rate limiting** — Prevent API abuse with slowapi

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <p>Built with ❤️ using FastAPI, React, Groq, and FAISS</p>
  <p>
    <a href="https://github.com/yourusername/AI-Content-Studio/issues">Report Bug</a>
    ·
    <a href="https://github.com/yourusername/AI-Content-Studio/issues">Request Feature</a>
  </p>
</div>