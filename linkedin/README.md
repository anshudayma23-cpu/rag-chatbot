# FundBot | HDFC Mutual Fund RAG Assistant

A robust Retrieval-Augmented Generation (RAG) system designed to provide facts-only answers for HDFC Mutual Fund schemes. Built with a focus on compliance, speed, and accuracy.

## 🚀 Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+
- [Groq API Key](https://console.groq.com/)
- [Chroma Cloud API Key](https://trychroma.com/)

### Backend Setup
1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure `.env`:
   ```env
   GROQ_API_KEY=your_key
   CHROMA_API_KEY=your_key
   CHROMA_TENANT=your_tenant
   CHROMA_DATABASE=demo
   ```
4. Start the Flask server:
   ```bash
   python src/ui/app.py
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```

## 🎯 Scope
- **Asset Management Company (AMC)**: Primarily HDFC Mutual Fund.
- **Schemes**: Covers 10 major HDFC schemes including Multi Cap, Small Cap, Defence, Nifty 50 Index, and more.
- **Data Points**: NAV, AUM (Fund Size), Expense Ratio, Exit Load, Fund Manager, Launch Date, and Risk Classification.

## 🚫 Known Limits & Compliance
- **Facts-Only**: The system is strictly forbidden from providing investment advice, recommendations, or predictions.
- **Schema Lock**: Only answers queries related to available HDFC fund data. Out-of-scope or advisory queries are automatically intercepted by a **Static Refusal Engine**.
- **Rate Limiting**: Integrated abuse prevention (max 50 queries per 10 minutes per session).
- **No PDF Processing**: Currently relies on real-time web-scraped structured data from Groww for maximum accuracy.
