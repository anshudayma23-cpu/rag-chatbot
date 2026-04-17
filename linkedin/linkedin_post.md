# 🚀 Building a Compliance-First AI: My HDFC Mutual Fund RAG Assistant

I’m thrilled to share my latest project: a high-performance, **Facts-Only RAG (Retrieval-Augmented Generation) Chatbot** designed specifically for the Indian Mutual Fund space.

**Live Demo:** [https://rag-chatbot-one-delta.vercel.app/](https://rag-chatbot-one-delta.vercel.app/)

In Fintech, the biggest challenge isn't just making an AI talk—it's ensuring it *doesn't* give unauthorized investment advice. I built this system to stay strictly factual while delivering answers in under 3 seconds.

### 🏗️ The 4-Phase RAG Architecture

1.  **Dynamic Ingestion**: Automated daily scraping of official HDFC scheme data, synchronized to **Chroma Cloud** using GitHub Actions.
2.  **Hybrid Retrieval**: A dual-path system combining semantic vector search with keyword-based BM25 retrieval for 100% factual accuracy.
3.  **The "Compliance" Secret Sauce**: A specialized **Intent Router** built on Llama 3 that acts as a secure gatekeeper, blocking advisory baiting or out-of-scope requests before they even reach the database.
4.  **Ultra-Light Deployment**: Optimized for the cloud by offloading embeddings to the **Hugging Face Inference API**, achieving extreme performance with near-zero RAM overhead on Render.

### 🛡️ Compliance & Safety in Action
One of the core features is the **Static Refusal Engine**. The bot is strictly forbidden from providing recommendations or selection advice. 

---
**User**: *"Should I invest in HDFC Small Cap Fund or Mid Cap Fund?"*
**Assistant**: *"I am a facts-only assistant and am not authorized to provide investment advice... Please consult a SEBI-registered investment advisor."*
---

### 🛠️ Tech Stack
*   **LLM Engine**: Llama 3.3 (8B/70B) via **Groq** (Blazing fast!)
*   **Vector Database**: Chroma Cloud
*   **Embeddings**: Hugging Face Inference API
*   **Automation**: GitHub Actions (Daily Sync)
*   **Interface**: Next.js & Tailwind (Deployed on Vercel)
*   **Backend**: Flask (Deployed on Render)

This project demonstrates how RAG can be applied to build safe, regulated, and industrial-grade financial tools.

**Check out the GitHub Repository here:** [Insert your GitHub Repo Link]

#AI #Fintech #GenerativeAI #Python #RAG #MachineLearning #Compliance #MutualFunds #HDFC
