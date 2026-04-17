# Deployment Plan: HDFC Mutual Fund RAG Chatbot

This document outlines the multi-platform deployment strategy for the RAG assistant, ensuring scalability, data freshness, and high performance.

## 🏗️ Architecture Overview

The system is split into three main operational layers:
1.  **Frontend**: Interactive UI built with Next.js.
2.  **Backend**: RAG Orchestration API built with Flask.
3.  **Data Ingestion**: Automated pipelines for daily knowledge updates.

---

## ☁️ Platform Mapping

| Component | Platform | URL (Example) | Role |
| :--- | :--- | :--- | :--- |
| **Frontend** | Vercel | `fundbot.vercel.app` | UI Delivery & SEO |
| **Backend** | Render | `fundbot-api.onrender.com` | RAG Logic & Inference |
| **Scheduler** | GitHub Actions | N/A (Internal) | Daily Data Refresh |
| **Vector DB** | Chroma Cloud | Managed | Serverless Vector Storage |
| **LLM Inference**| Groq | Managed | High-speed LLM execution |

---

## 🚀 Deployment Steps

### 1. Backend (Render)
The Flask application handles all RAG queries and connects to Chroma Cloud and Groq.

*   **Service Type**: Web Service (Python).
*   **Build Command**: `pip install -r requirements.txt`
*   **Start Command**: `gunicorn --chdir src/ui app:app --timeout 120` (Timeout added for model loading).
*   **Root Directory**: Leave as root `/`.
*   **Included Files**: The system uses `Procfile` and `runtime.txt` located in the root to configure the environment automatically.
*   **Environment Variables**:
    *   `GROQ_API_KEY`: Required for Llama-3 inference.
    *   `CHROMA_API_KEY`: Required for cloud collection access.
    *   `CHROMA_TENANT`: (e.g., `default_tenant`)
    *   `CHROMA_DATABASE`: (e.g., `default_database`)
    *   `PORT`: Automatically set by Render (the app is configured to listen on `os.environ.get("PORT")`).

### 2. Frontend (Vercel)
The Next.js application provides the user interface and communicates with Render.

*   **Framework Preset**: Next.js.
*   **Root Directory**: `frontend/`
*   **Build Command**: `next build`
*   **Environment Variables**:
    *   `NEXT_PUBLIC_API_URL`: The full URL of your Render backend (e.g., `https://fundbot-api.onrender.com`). **Note**: Ensure this does NOT have a trailing slash.

### 3. Scheduler & Data Ingestion (GitHub Actions)
The "Ground Truth" is refreshed daily at **9:15 AM IST** via the `ingest_data.yml` workflow.

*   **Action Secrets** (GitHub Repo -> Settings -> Secrets and variables -> Actions):
    *   Add `CHROMA_API_KEY`, `CHROMA_TENANT`, `CHROMA_DATABASE`, and `GROQ_API_KEY`.
*   **Playwright**: The workflow automatically installs browser dependencies (`playwright install chromium --with-deps`) on the Ubuntu runner.

---

## 🔐 Security & Production Optimizations

*   **CORS**: Currently set to `CORS(app)` (Open). For production, update `src/ui/app.py` to:
    ```python
    CORS(app, resources={r"/api/*": {"origins": "https://your-vercel-domain.vercel.app"}})
    ```
*   **Resource Management**: The backend pre-loads embedding models into memory on startup (`shared_state.initialize()`). On Render's Free Tier, ensure you have at least 512MB RAM; otherwise, the process may OOM.
*   **Database**: Ensure the `CHROMA_API_KEY` has `write` permissions for the ingestion pipeline and `read` permissions for the backend service.

---

## 🔐 Security & Optimization

*   **CORS Configuration**: In `src/ui/app.py`, ensure `flask-cors` is configured to only allow requests from your Vercel domain in production.
*   **Health Checks**: Render will monitor `/` to ensure the service is active.
*   **Concurrency**: Render's free tier spins down after inactivity. Use a "keep-alive" cron (like [Cron-job.org](https://cron-job.org)) if immediate responsiveness is required for demo purposes.
*   **Cold Starts**: The `shared_state.py` in the backend caches the embedding models in memory to reduce latency after the initial cold start.

---

## 🛠️ Post-Deployment Checklist

- [ ] Verify Frontend can reach Backend API via `NEXT_PUBLIC_API_URL`.
- [ ] Confirm GitHub Action runs successfully and updates Chroma Cloud.
- [ ] Test the "Facts-only" refusal logic to ensure no advice is given.
- [ ] Validate mobile responsiveness on Vercel preview links.
