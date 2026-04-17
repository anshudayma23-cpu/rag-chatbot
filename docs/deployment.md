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
*   **Start Command**: `gunicorn --chdir src/ui app:app`
*   **Environment Variables**:
    *   `GROQ_API_KEY`: For Llama-3 inference.
    *   `CHROMA_API_KEY`: For cloud vector storage access.
    *   `CHROMA_TENANT` / `CHROMA_DATABASE`: For multi-tenant isolation.
    *   `PYTHON_VERSION`: `3.10.x` or higher.

### 2. Frontend (Vercel)
The Next.js application provides a premium user experience and communicates with Render.

*   **Framework Preset**: Next.js.
*   **Root Directory**: `frontend/`
*   **Environment Variables**:
    *   `NEXT_PUBLIC_API_URL`: The URL of your Render backend.
*   **Build Command**: `npm run build`

### 3. Scheduler (GitHub Actions)
Automates the "Ground Truth" updates every morning.

*   **Trigger**: Daily at 9:15 AM IST (`3:45 AM UTC`).
*   **Actions Workflow**: `.github/workflows/ingest_data.yml`.
*   **Required Secrets** (Repo Settings -> Secrets):
    *   `CHROMA_API_KEY`
    *   `CHROMA_TENANT`
    *   `CHROMA_DATABASE`
    *   `GROQ_API_KEY` (if used for summerization during ingestion).

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
