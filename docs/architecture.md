# Hyper-Detailed RAG Architecture: Mutual Fund FAQ Assistant

---

## 🎯 Project Scope & Data Sources
The system is currently scoped to provide factual data for the following **HDFC Mutual Fund** schemes, sourced directly from **Groww**:

*   [HDFC Multi Cap Fund](https://groww.in/mutual-funds/hdfc-multi-cap-fund-direct-growth)
*   [HDFC Short Term Opportunities Fund](https://groww.in/mutual-funds/hdfc-short-term-opportunities-fund-direct-growth)
*   [HDFC Balanced Advantage Fund](https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth)
*   [HDFC Defence Fund](https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth)
*   [HDFC Small Cap Fund](https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth)
*   [HDFC Nifty 50 Index Fund](https://groww.in/mutual-funds/hdfc-nifty-50-index-fund-direct-growth)
*   [HDFC Gold ETF Fund of Fund](https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth)
*   [HDFC Equity Fund](https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth)
*   [HDFC Silver ETF FoF](https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth)
*   [HDFC Mid Cap Fund](https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth)

**Note**: The system utilized dynamic web scraping for these links. **No PDF documents are used in the current version.**

---

This document provides an exhaustive technical specification of the facts-only RAG system. It is divided into **four granular phases**, detailing the exact logic, algorithms, and configurations for every operational step:

1.  **Phase 1**: Ingestion Pipeline (Data Preparation)
2.  **Phase 2**: Retrieval + Generation (Interactive Querying)
3.  **Phase 3**: Refusal and Security Layer (Compliance & Safety)
4.  **Phase 4**: Multi-Thread Chat (Conversational Context Management)

---

## 🏗️ Phase 1: Ingestion Pipeline (Data Preparation)
Converting raw, unstructured financial documents into a structured, searchable knowledge-base.

### 1.1 📄 Phase 1.1: Web Scraping & Targeted Field Extraction
*   **The Process**: Targeted extraction of specific mutual fund metrics from Groww's scheme pages. Instead of converting entire pages to markdown, we extract only the 16 fields required by the FAQ assistant.
*   **Deep Detail**:
    *   **Dynamic Web Loading**: We use **Playwright** with a headless browser to render the JavaScript-heavy Groww UI. This is essential to capture data like "Current NAV" which is fetched asynchronously.
    *   **Automated Navigation**: The scraper iterates through each of the 10 target URLs, using `domcontentloaded` wait + a 5-second JS rendering delay.
    *   **Targeted Field Extraction**: Using `BeautifulSoup` + regex patterns on the rendered HTML, we extract exactly these fields per fund:
        *   **Key Metrics**: NAV (INR), NAV date, Fund size/AUM (Cr), Expense ratio (%), Groww rating, Risk label
        *   **Scheme Profile**: Category, Sub-category, Plan type, Benchmark index
        *   **Investment Details**: Minimum SIP (INR), Minimum lumpsum (INR), Exit load
        *   **Fund Info**: Fund manager, Launch date, ISIN (if available)
    *   **Extraction Strategy**: Each field uses a dedicated extractor method with try/except fallbacks. Category/sub-category/risk are parsed from Groww's filter link patterns (`?cat=`, `?sub_cat=`, `?risk=`). Numeric values are parsed via regex from label-value pairs in the metrics block. Benchmark, fund manager, and launch date are extracted from their respective page sections.
    *   **Content Summary Generation**: A clean prose summary (~150-200 words) is built from the structured fields for embedding. This replaces the noisy full-page markdown (~40,000 chars) with dense factual text (~800 chars).
    *   **Output Format**: Each fund produces a structured JSON entry:
        ```json
        {
          "url": "source URL",
          "scheme_name": "cleaned fund name",
          "timestamp": "YYYY-MM-DD",
          "structured_data": { ...16 fields... },
          "content": "prose summary for embedding"
        }
        ```

### 1.2 ✂️ Phase 1.2: Section-Based Semantic Chunking
*   **The Process**: Creating focused, semantically coherent chunks from structured fund data. Each fund produces 2-3 purpose-built chunks instead of 10-20 noisy generic chunks.
*   **Deep Detail**:
    *   **Algorithm**: Section-based chunking. Instead of blindly splitting text, the processor creates chunks by semantic topic:
        *   **Chunk 1 "Key Metrics"**: Fund name, category, sub-category, risk, NAV, NAV date, AUM, expense ratio, rating.
        *   **Chunk 2 "Investment Details"**: Min SIP, min lumpsum, exit load, plan type, benchmark.
        *   **Chunk 3 "Fund Profile"**: Fund manager, launch date, ISIN.
    *   **Chunk Prefix**: Each chunk is prefixed with the scheme name for BM25/vector retrieval context.
    *   **Result**: 30 total chunks across 10 funds (3 per fund), each dense and focused on a single topic.
    *   **Fallback**: A `RecursiveCharacterTextSplitter` (800 tokens, 50 overlap) is retained for backward compatibility with legacy markdown data.

    *   **Model**: `BAAI/bge-small-en-v1.5`. A highly efficient open-source embedding model from the Beijing Academy of Artificial Intelligence.
    *   **Mechanism**: The model transforms text into a 384-dimensional vector where semantically similar concepts (e.g., "Exit Load" and "Withdrawal Charges") are mathematically proximal.
    *   **L2 Normalization**: All vectors are normalized to unit length. This simplifies similarity calculations to an efficient **Dot Product** (equivalent to Cosine Similarity for normalized vectors).

### 1.4 💾 Phase 1.4: Vector Indexing & Cloud Persistence
*   **The Process**: Storing vectors in a managed, serverless, and filterable cloud database.
*   **Deep Detail**:
    *   **Storage Engine**: `Chroma Cloud` (Managed Serverless). Vectors are stored on the official [trychroma.com](https://trychroma.com) cloud infrastructure, eliminating the need for local database files.
    *   **Indexing Algorithm**: **HNSW (Hierarchical Navigable Small World)**. Configured with `cosine` similarity to ensure high retrieval speed and accuracy.
    *   **Connectivity Strategy**: The system initializes a `CloudClient` using a `CHROMA_API_KEY`. This ensures that data is accessible from any environment (CI/CD, local, or production) without manual file synchronization.

### 1.5 🗄️ Phase 1.5: Database Schema & Management
*   **The Process**: Defining how data is structured for optimal filtering.
*   **Deep Detail**:
    *   **Collection Name**: `mutual_fund_faqs`.
    *   **Metadata Schema**: 
        ```json
        {
          "scheme_name": "Cleaned fund name",
          "source_url": "Source URL for verification",
          "last_updated": "YYYY-MM-DD extraction date",
          "chunk_hash": "SHA-256 for change detection",
          "chunk_index": 0,
          "section_type": "key_metrics | investment_details | fund_profile",
          "category": "Equity / Debt / Hybrid / Commodities",
          "sub_category": "Flexi Cap / Small Cap / etc.",
          "risk_label": "Very High Risk / High Risk / Moderate Risk"
        }
        ```
    *   **Filtering Capability**: The system supports filtering by `scheme_name`, `section_type`, `category`, and `last_updated`. This allows the retriever to narrow the search space to a specific fund or section type.
    *   **Management Logic**: A dedicated `VectorDBManager` handles collection initialization, batch upserts, and change detection (skipping chunks whose hashes already exist).

---

## 🧠 Phase 2: Retrieval + Generation (Interactive Querying)
Processing user intent to deliver a verifiable, concise answer.

### 2.1 ❓ Phase 2.1: Query Guard & Intent Routing
*   **The Process**: Intercepting the query to ensure compliance.
*   **Deep Detail**:
    *   **Intention Classification**: A fast LLM call (e.g., Llama-3-8B) evaluates: `{"intent": "FACTUAL" | "ADVISORY" | "GREETING"}`.
    *   **The Trap**: If the intent is "ADVISORY" (e.g., "compare these two"), the system halts retrieval immediately and routes to a **Static Refusal Engine**. This prevents the LLM from ever seeing the data and "hallucinating" a recommendation.

### 2.2 🔍 Phase 2.2: Hybrid Retrieval Logic
*   **The Process**: Finding relevant facts using both "meaning" and "keywords."
*   **Deep Detail**:
    *   **Dense Search (Vector)**: Finds chunks conceptually related to the query.
    *   **Sparse Search (BM25)**: Explicitly looks for exact matches of terms like "SIP" or "Lock-in."
    *   **Ensemble Retriever**: Uses **Reciprocal Rank Fusion (RRF)** to combine these lists. This ensures that if a document is high in either semantic or keyword rankings, it moves to the top.

### 2.3 📑 Phase 2.3: Cross-Encoder Reranking
*   **The Process**: A final "reality check" of the retrieved chunks.
*   **Deep Detail**:
    *   **The Mechanism**: We pass the user query + the top 10 retrieved chunks through a `cross-encoder/ms-marco-MiniLM-L-6-v2`. 
    *   **Why**: Vector similarity only measures distance. Reranking measures *relevance*. A document might be semantically "near" (e.g., same scheme) but irrelevant to the specific question (e.g., wrong section). Reranking ensures only the actual "Answer" chunks reach the LLM.

### 2.4 🤖 Phase 2.4: Factual Generation (Prompt Engineering)
*   **The Process**: Synthesis of data into human speech.
*   **Deep Detail**:
    *   **System instructions**: Uses **Chain-of-Thought (CoT)** prompting to force the LLM to find the answer in the text FIRST, then write it.
    *   **Constants**: 
        *   `Temperature`: **0.0** (Deterministic). No creativity allowed.
        *   `Top-p`: **0.9** (Diversity limit).
    *   **Hallucination Check**: The LLM is forced to output the exact source line it used.

### 2.5 ✅ Phase 2.5: Compliance Formatting & Response
*   **The Process**: Final output dressing and verification.
*   **Deep Detail**:
    *   **Post-Processor**: A custom Python function runs a regex check on the LLM output to count sentences.
    *   **Footer Injection**: Dynamically reads the `last_updated_date` from the retrieved chunk's metadata and appends it.
    *   **Disclaimer**: A mandatory pre-set string "Facts-only. No investment advice." is displayed in the UI sidebar and response footer.

---

## 🛡️ Phase 3: Refusal and Security Layer (Compliance & Safety)
Enforcing strict content policies, preventing harmful outputs, and ensuring regulatory compliance for financial advisory systems.

### 3.1 🚫 Phase 3.1: Multi-Layer Intent Classification & Routing
*   **The Process**: Deep semantic analysis of user queries to categorize intent and enforce content boundaries before any data retrieval occurs.
*   **Deep Detail**:
    *   **Intent Categories**:
        *   `FACTUAL`: Objective data queries (NAV, AUM, expense ratio, fund manager, exit load, etc.)
        *   `ADVISORY`: Investment recommendations, "should I invest", "which is better" comparisons, performance predictions
        *   `GREETING`: Salutations, small talk, identity questions
        *   `OUT_OF_SCOPE`: Queries unrelated to HDFC mutual funds (politics, general knowledge, other AMCs)
        *   `UNCLEAR`: Ambiguous queries requiring clarification
    *   **Classification Engine**: Lightweight LLM (Llama-3.1-8B-Instant via Groq) with structured JSON output:
        ```json
        {
          "intent": "FACTUAL|ADVISORY|GREETING|OUT_OF_SCOPE|UNCLEAR",
          "confidence": 0.0-1.0,
          "reasoning": "brief explanation",
          "detected_fund": "extracted fund name or null"
        }
        ```
    *   **Pattern Matching Fallback**: Regex-based keyword detection for common advisory patterns (`"should I"`, `"better than"`, `"invest in"`, `"recommend"`, `"good for"`, `"compare"`)
    *   **Routing Decision Matrix**:
        | Intent | Action | Data Access |
        |--------|--------|-------------|
        | FACTUAL | Proceed to Phase 2.2 (Retrieval) | Full access |
        | ADVISORY | Block + Trigger Refusal Engine | Zero access |
        | GREETING | Static greeting response | No retrieval |
        | OUT_OF_SCOPE | Deflection to greeting | No retrieval |
        | UNCLEAR | Clarification request | No retrieval |

### 3.2 🔒 Phase 3.2: Static Refusal Engine
*   **The Process**: Hard-coded, non-LLM refusal responses that cannot be manipulated or bypassed through prompt injection.
*   **Deep Detail**:
    *   **Refusal Templates** (immutable strings, no LLM generation):
        *   **Advisory Refusal**: "I am a facts-only assistant and am not authorized to provide investment advice, comparisons for selection, or recommendations. Please consult a SEBI-registered investment advisor for personalized guidance."
        *   **Comparison Refusal**: "I cannot compare funds for investment selection purposes. I can only provide factual data about individual schemes. For investment decisions, please consult a SEBI-registered advisor."
        *   **Prediction Refusal**: "I cannot provide performance predictions or future return estimates. Mutual fund investments are subject to market risks. Please read all scheme related documents carefully."
    *   **Anti-Jailbreak Measures**:
        *   Ignore all "pretend" or "roleplay" prefixes in queries
        *   Strip system prompt injection attempts (`"ignore previous instructions"`, `"you are now an advisor"`)
        *   Advisory detection runs BEFORE any context injection
    *   **SEBI Compliance Footer**: All refusal responses include mandatory disclaimer: `"**Disclaimer**: Facts-only. No investment advice."`

### 3.3 🛡️ Phase 3.3: Output Safety Filtering
*   **The Process**: Post-generation validation to ensure LLM outputs adhere to safety policies.
*   **Deep Detail**:
    *   **Content Filters**:
        *   **Advisory Pattern Detection**: Scan output for recommendation language (`"you should"`, `"I recommend"`, `"better choice"`, `"invest now"`)
        *   **Hallucination Check**: Verify all numeric claims against retrieved context (NAV, AUM, ratios must match source)
        *   **Source Attribution**: Enforce that every factual claim is paired with a `Source:` citation
    *   **Enforcement Actions**:
        *   If advisory language detected: Replace with refusal template
        *   If hallucination detected: Log error, return "Data unavailable" message
        *   If source missing: Append retrieved source URL automatically
    *   **Audit Logging**: All refusal events logged with query content, intent classification, and timestamp for compliance auditing

### 3.4 🔐 Phase 3.4: Rate Limiting & Abuse Prevention
*   **The Process**: Protecting system resources and preventing spam or enumeration attacks.
*   **Deep Detail**:
    *   **Per-Session Limits**:
        *   Maximum 50 queries per 10-minute window per user session
        *   Maximum 5 concurrent requests per session
    *   **Suspicious Pattern Detection**:
        *   Rapid-fire queries (< 1 second intervals) trigger temporary throttling
        *   Repeated identical queries return cached response without LLM call
        *   Query length limits: 10-500 characters (reject empty or excessively long)
    *   **IP-Based Protection** (if deployed publicly):
        *   100 requests per minute per IP
        *   Progressive backoff for violations (1min → 5min → 30min bans)

---

## 💬 Phase 4: Multi-Thread Chat (Conversational Context Management)
Managing multi-turn conversations with persistent context, user session isolation, and context-aware follow-up handling.

### 4.1 🧵 Phase 4.1: Session Management & Thread Isolation
*   **The Process**: Creating isolated conversation contexts for each user session with persistent storage.
*   **Deep Detail**:
    *   **Session Identification**:
        *   **Web UI**: UUID generated on first page load, stored in `localStorage`
        *   **API**: `session_id` parameter in request headers or body
        *   **CLI**: Temporary session ID per process instance
    *   **Thread Storage Architecture**:
        ```
        sessions/
        ├── {session_id_1}/
        │   ├── messages.jsonl       # Chronological message history
        │   ├── context_summary.txt  # Condensed context for LLM
        │   └── metadata.json        # Created_at, last_active, message_count
        └── {session_id_2}/
            └── ...
        ```
    *   **Message Schema**:
        ```json
        {
          "message_id": "uuid",
          "timestamp": "ISO-8601",
          "role": "user|assistant|system",
          "content": "message text",
          "intent": "FACTUAL|ADVISORY|...",
          "sources": ["url1", "url2"],
          "retrieved_chunks": ["chunk_id_1", "chunk_id_2"]
        }
        ```
    *   **Session Lifecycle**:
        *   **Creation**: On first user interaction
        *   **Activity Tracking**: `last_active` timestamp updated per message
        *   **Expiration**: Sessions auto-delete after 7 days of inactivity
        *   **Manual Reset**: User can "Clear Chat" to start fresh session

### 4.2 📝 Phase 4.2: Context Window Management
*   **The Process**: Intelligently managing conversation history to stay within LLM token limits while preserving relevant context.
*   **Deep Detail**:
    *   **Context Assembly Strategy**:
        1.  **System Prompt** (fixed, ~200 tokens): Base instructions, SEBI disclaimer, output format rules
        2.  **Context Summary** (dynamic, ~300 tokens): Condensed representation of earlier conversation turns
        3.  **Recent Messages** (sliding window, ~1000 tokens): Last 5-10 message pairs (user + assistant)
        4.  **Retrieved Context** (variable, ~1000 tokens): Current query's RAG chunks
    *   **Summarization Trigger**: When total context exceeds 3000 tokens:
        *   Summarize oldest 50% of messages using lightweight LLM
        *   Replace summarized messages with condensed version
        *   Preserve key facts (mentioned fund names, user preferences, previous clarifications)
    *   **Token Budget Allocation**:
        | Component | Tokens | Priority |
        |-----------|--------|----------|
        | System Prompt | 200 | Critical |
        | Retrieved Context | 1000 | High |
        | Recent Messages | 1000 | High |
        | Context Summary | 300 | Medium |
        | Response Buffer | 1500 | - |

### 4.3 🎯 Phase 4.3: Context-Aware Query Enhancement
*   **The Process**: Using conversation history to improve understanding of follow-up queries and ambiguous references.
*   **Deep Detail**:
    *   **Coreference Resolution**:
        *   Resolve pronouns (`"it"`, `"that fund"`, `"this one"`) to last mentioned fund
        *   Resolve implicit subjects (`"What is its NAV?"` → uses fund from previous turn)
        *   Handle partial references (`"the small cap one"` → matches to HDFC Small Cap Fund if mentioned)
    *   **Query Expansion Engine**:
        ```python
        # Example transformation
        User: "What is the NAV of HDFC Small Cap Fund?"
        Assistant: [provides NAV]
        User: "What about its exit load?"  # Ambiguous
        # Expanded to: "What is the exit load of HDFC Small Cap Fund?"
        ```
    *   **Context Injection Rules**:
        *   If query mentions no fund name → inherit from previous turn
        *   If query is a comparison (`"which is better"`) → expand to include last 2 mentioned funds
        *   If query is ambiguous (`"tell me more"`) → expand based on last discussed topic
    *   **Disambiguation Prompts**: When context expansion fails:
        *   `"I see you've asked about multiple funds. Which one are you referring to?"`
        *   `"Could you clarify which fund you'd like to know about?"`

### 4.4 🔄 Phase 4.4: Multi-Turn RAG Strategy
*   **The Process**: Adapting retrieval strategy based on conversation flow to avoid redundant or conflicting information.
*   **Deep Detail**:
    *   **Retrieval Context Tracking**:
        *   Store IDs of previously retrieved chunks per session
        *   Track which funds have been discussed
        *   Remember user's stated preferences (if any)
    *   **Smart Retrieval Modes**:
        *   **Fresh Retrieval** (default): Full hybrid search for new topics
        *   **Follow-up Retrieval**: Narrow search to previously discussed fund(s) only
        *   **Comparison Block**: If user asks for comparison after individual fund queries, trigger refusal without retrieval
        *   **Context Verification**: If follow-up contradicts previous data, flag for data update check
    *   **Chunk Deduplication**: Prevent same chunk from appearing multiple times in conversation history
    *   **Temporal Awareness**: If user asks "has it changed?" or "what's the latest?", force fresh data retrieval even if cached

### 4.5 💾 Phase 4.5: Persistent Storage & Recovery
*   **The Process**: Ensuring conversation continuity across sessions and system restarts.
*   **Deep Detail**:
    *   **Storage Options**:
        *   **Local**: JSON files in `sessions/` directory (development/single-user)
        *   **Cloud**: Chroma Cloud metadata collection for session storage (multi-user)
        *   **Database**: SQLite/PostgreSQL for production deployments
    *   **Backup Strategy**:
        *   Daily snapshot of all active sessions
        *   Async write operations to prevent UI blocking
    *   **Export Functionality**: User can export chat history as JSON or markdown
    *   **Privacy Controls**:
        *   Automatic purge of expired sessions
        *   User-initiated "Delete All History" option
        *   No PII storage in conversation logs

---

## 🏗️ Detailed Sub-Architecture: Chunking & Embedding Pipeline
This technical sub-architecture describes the transformation of structured fund data into high-dimensional vector representations.

### Step 1: Section-Based Chunking Logic
*   **Input**: Structured fund data dictionary with 16 extracted fields per fund.
*   **Strategy**: **Section-Based Semantic Chunking**.
    1.  **Key Metrics Chunk**: Aggregates fund identity (name, category, sub-category, risk) and primary metrics (NAV, AUM, expense ratio, rating) into a single dense sentence.
    2.  **Investment Details Chunk**: Combines investment requirements (min SIP, min lumpsum) with fund mechanics (exit load, plan type, benchmark).
    3.  **Fund Profile Chunk**: Groups fund management info (manager name, launch date, ISIN).
*   **Result**: Each fund produces exactly 2-3 chunks (~50-100 tokens each), totaling ~30 chunks across 10 funds.
*   **Chunk IDs**: Deterministic format `{scheme_name}_{section_type}` for stable change detection across runs.

### Step 2: Hashing & Change Detection
*   **Mechanism**: Before embedding, a **SHA-256 hash** is generated for each chunk.
*   **Logic**:
    *   Compare the `current_hash` with the `stored_hash` in the Vector DB for that specific Scheme/Index.
    *   If identical: Skip embedding (saves computational resources).
    *   If different: Trigger **Step 3**.

### Step 3: Vectorization (Embedding)
*   **Engine**: `BAAI/bge-small-en-v1.5` (Local Inference via Sentence-Transformers).
*   **Execution**:
    1.  **Batching**: Chunks are processed in efficient batches.
    2.  **Local Processing**: Vectors are computed locally, eliminating API latency and costs.
    3.  **Result**: Each chunk returns a **384-dimensional float vector**.

### Step 4: Metadata Mapping & Sync
Each vector is saved with the following enrichment:
```json
{
  "chunk_id": "scheme_name + section_type",
  "chunk_hash": "sha256_hash",
  "metadata": {
    "source_url": "URL",
    "scheme_name": "Cleaned fund name",
    "last_updated": "YYYY-MM-DD",
    "section_type": "key_metrics / investment_details / fund_profile",
    "category": "Equity / Debt / Hybrid / Commodities",
    "sub_category": "Flexi Cap / Small Cap / etc.",
    "risk_label": "Very High Risk / Moderate Risk / etc."
  }
}
```
*   **Synchronization**: The final step involves a native `upsert` in Chroma Cloud to ensure the index reflects the latest scrape. Since this is cloud-based, it allows for global accessibility and multi-user querying.

---

## 🛠️ Data Scheduler & Synchronization (GitHub Actions)
The ingestion pipeline is orchestrated via GitHub Actions to ensure multi-thread consistency and data freshness.

### 2.1 Pipeline Orchestration
*   **Scheduler**: GitHub Actions (Ubuntu-latest) triggered daily via **`cron: "45 3 * * *"` (9:15 AM IST)**.
*   **Orchestrator**: `src/ingestion/main.py` is the entry point that sequentially triggers:
    1.  **Scraper**: Playwright-based worker performs targeted field extraction from HDFC scheme URLs.
    2.  **Chunking**: Section-based semantic chunking (3 chunks per fund: key metrics, investment details, fund profile).
    3.  **Embedding & Sync**: SHA-256 hash comparison followed by BGE-small-en-v1.5 embedding and upsert to **Chroma Cloud**.
*   **Secrets Management**: All sensitive keys (OpenAI, Chroma Cloud) are managed via GitHub Repository Secrets and injected into the workflow at runtime.

---

## 🛠️ Final Technology Stack
| Layer | Technology |
| :--- | :--- |
| **Scheduler** | GitHub Actions (Ubuntu-latest) |
| **Scraper** | Python (Playwright + BeautifulSoup, targeted field extraction) |
| **Chunking** | Section-based semantic chunking (3 chunks/fund) |
| **Embedding Model** | `BAAI/bge-small-en-v1.5` (384-dim) |
| **Vector DB** | Chroma Cloud (Serverless) |
| **LLM Inference** | Groq (Llama-3.3-70B-Versatile / Llama-3.1-8B-Instant) |
| **Orchestration** | LangChain / LangGraph |
| **Evaluation** | RAGAS (Factual Consistency Benchmarking) |
