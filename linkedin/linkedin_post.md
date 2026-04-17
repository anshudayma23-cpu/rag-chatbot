# 🚀 Building a Compliance-First AI: My HDFC Mutual Fund RAG Assistant

I’m excited to share a project I’ve been working on: a high-performance, **Facts-Only RAG (Retrieval-Augmented Generation) Chatbot** specifically designed for the Indian Mutual Fund space.

In the world of Fintech, the biggest challenge isn't just getting an AI to talk—it's ensuring it *doesn't* give unauthorized investment advice. Here’s how I built a system that stays strictly factual while delivering answers in under 3 seconds.

### 🏗️ The Architecture
The system uses a sophisticated 4-Phase RAG Pipeline:

1.  **Ingestion**: Dynamic web scraping of official HDFC scheme data from Groww, transformed into dense semantic chunks using `BAAI/bge-small-en-v1.5`.
2.  **Hybrid Retrieval**: Combines semantic vector search with keyword-based BM25 retrieval, followed by a **Cross-Encoder Reranker** (`ms-marco-MiniLM`) to ensure only the most relevant facts reach the AI.
3.  **The Security Layer (Our Secret Sauce)**: A specialized Intent Router built on Llama 3 that acts as a gatekeeper. It classifies every query before retrieval to block advisory or out-of-scope requests.
4.  **Performance Optimization**: By implementing a shared state singleton for heavy models, I reduced the query latency from **20 seconds down to ~2.5 seconds**.

### 🛡️ Compliance in Action
One of the core features is the **Static Refusal Engine**. The bot is strictly forbidden from providing recommendations or comparisons for selection. 

Check out how it handles "Advisory Baiting" and "Out-of-Scope" queries:

---
#### 📸 Demo 1: The Out-of-Scope Block
**User**: *"Who is the Prime Minister of India?"*
**Assistant**: *"Hello! I am your HDFC Mutual Fund Factual Assistant. I can only provide factual information about HDFC Mutual Fund schemes. How can I help you today with fund data?"*

#### 📸 Demo 2: The Advisory Refusal (Compliance)
**User**: *"Should I invest in HDFC Small Cap Fund or Mid Cap Fund?"*
**Assistant**: *"I am a facts-only assistant and am not authorized to provide investment advice, comparisons for selection, or recommendations. Please consult a SEBI-registered investment advisor for personalized guidance. **Disclaimer**: Facts-only. No investment advice."*
---

### 🛠️ Tech Stack
*   **LLM Engine**: Llama 3.3 via Groq (Incredible speed!)
*   **Vector DB**: Chroma Cloud (Serverless persistence)
*   **Orchestration**: LangChain & Python
*   **Frontend**: Next.js & Vanilla CSS for a premium, responsive UI.

This project demonstrates how RAG can be used not just for knowledge, but for building safe, regulated, and industrial-grade financial tools.

**Check out the repo here:** [Link to your repo]

#AI #Fintech #GenerativeAI #Python #RAG #MachineLearning #Compliance #MutualFunds
