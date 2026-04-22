import hashlib
import os
import json
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv
import sys
import logging

logger = logging.getLogger("ingestion")

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.database.chroma_manager import VectorDBManager

load_dotenv()

try:
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-small-en-v1.5")
    def token_len(text: str) -> int:
        return len(tokenizer.encode(text, add_special_tokens=False))
except Exception as e:
    logger.warning(f"Could not load tokenizer: {e}. Using character length for splitting.")
    token_len = len


class DataProcessor:
    def __init__(self, persist_directory: str = "docs/vectordb"):
        # Fallback text splitter for legacy data
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=50,
            length_function=token_len,
            is_separator_regex=False,
        )

        # Phase 1.3: Hugging Face Inference API (Zero RAM for Render)
        from langchain_huggingface import HuggingFaceEndpointEmbeddings
        self.embeddings = HuggingFaceEndpointEmbeddings(
            model="BAAI/bge-small-en-v1.5",
            huggingfacehub_api_token=os.getenv("HUGGINGFACE_API_KEY")
        )
        self.persist_directory = persist_directory

        # Phase 1.4 & 1.5: Dedicated DB Manager
        self.db_manager = VectorDBManager(persist_directory=self.persist_directory)

    def _generate_hash(self, text: str) -> str:
        """SHA-256 hashing for change detection."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def _create_structured_chunks(self, entry: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create 2-3 semantic chunks from structured fund data."""
        sd = entry.get("structured_data", {})
        scheme_name = entry.get("scheme_name", "Unknown")
        url = entry.get("url", "")
        timestamp = entry.get("timestamp", "")

        chunks = []

        # --- Chunk 1: Key Metrics ---
        metrics_parts = [f"{scheme_name} - Key Metrics and Overview."]
        if sd.get("category"):
            metrics_parts.append(f"Category: {sd['category']}.")
        if sd.get("sub_category"):
            metrics_parts.append(f"Sub-category: {sd['sub_category']}.")
        if sd.get("risk_label"):
            metrics_parts.append(f"Risk classification: {sd['risk_label']}.")
        if sd.get("nav_value") and sd.get("nav_date"):
            metrics_parts.append(f"Current NAV: ₹{sd['nav_value']} as of {sd['nav_date']}.")
        if sd.get("fund_size_aum"):
            metrics_parts.append(f"Fund size (AUM): ₹{sd['fund_size_aum']} Cr.")
        if sd.get("expense_ratio"):
            metrics_parts.append(f"Expense ratio: {sd['expense_ratio']}% per annum.")
        if sd.get("rating"):
            metrics_parts.append(f"Groww rating: {sd['rating']} out of 5.")

        chunks.append({
            "text": " ".join(metrics_parts),
            "section_type": "key_metrics",
            "metadata": {
                "source_url": url,
                "scheme_name": scheme_name,
                "last_updated": timestamp,
                "section_type": "key_metrics",
                "category": sd.get("category", ""),
                "sub_category": sd.get("sub_category", ""),
                "risk_label": sd.get("risk_label", ""),
            }
        })

        # --- Chunk 2: Investment Details ---
        inv_parts = [f"{scheme_name} - Investment Details."]
        if sd.get("min_sip"):
            inv_parts.append(f"Minimum SIP amount: ₹{sd['min_sip']}.")
        if sd.get("min_lumpsum"):
            inv_parts.append(f"Minimum lumpsum investment: ₹{sd['min_lumpsum']}.")
        if sd.get("exit_load"):
            inv_parts.append(f"Exit load: {sd['exit_load']}.")
        if sd.get("plan_type"):
            inv_parts.append(f"Plan type: {sd['plan_type']}.")
        if sd.get("benchmark"):
            inv_parts.append(f"Benchmark index: {sd['benchmark']}.")

        chunks.append({
            "text": " ".join(inv_parts),
            "section_type": "investment_details",
            "metadata": {
                "source_url": url,
                "scheme_name": scheme_name,
                "last_updated": timestamp,
                "section_type": "investment_details",
                "category": sd.get("category", ""),
                "sub_category": sd.get("sub_category", ""),
                "risk_label": sd.get("risk_label", ""),
            }
        })

        # --- Chunk 3: Fund Profile ---
        profile_parts = [f"{scheme_name} - Fund Profile."]
        if sd.get("fund_manager"):
            profile_parts.append(f"Fund manager: {sd['fund_manager']}.")
        if sd.get("launch_date"):
            profile_parts.append(f"Launch date: {sd['launch_date']}.")
        if sd.get("isin"):
            profile_parts.append(f"ISIN: {sd['isin']}.")

        # Only add this chunk if we have at least one profile field
        if len(profile_parts) > 1:
            chunks.append({
                "text": " ".join(profile_parts),
                "section_type": "fund_profile",
                "metadata": {
                    "source_url": url,
                    "scheme_name": scheme_name,
                    "last_updated": timestamp,
                    "section_type": "fund_profile",
                    "category": sd.get("category", ""),
                    "sub_category": sd.get("sub_category", ""),
                    "risk_label": sd.get("risk_label", ""),
                }
            })

        return chunks

    def process_data(self, raw_data: List[Dict[str, Any]]):
        """
        Processes raw scraped data through chunking, hashing, and embedding.
        Supports both new structured format and legacy markdown format.

        IMPORTANT: Structured chunks (NAV data) are ALWAYS upserted by ID so
        that the `last_updated` date and NAV value stay current every day.
        Hash-dedup is intentionally skipped for structured chunks — the upsert
        overwrites the old record in-place which is exactly what we want for
        daily live data.

        Legacy markdown chunks still use hash-dedup to avoid redundant embeds.
        """
        # --- Structured (live NAV) chunks — always upsert ---
        structured_ids, structured_docs, structured_metas = [], [], []

        # --- Legacy markdown chunks — hash-deduped ---
        legacy_ids, legacy_docs, legacy_metas = [], [], []
        existing_hashes = set(self.db_manager.get_existing_hashes())

        logger.info(f"Processing {len(raw_data)} funds...")
        
        # --- Step 1: Cleanup old structured data ---
        # To satisfy "remove/delete previous day data", we purge any chunks
        # that have a source_url before inserting the new batch.
        # This ensures that if a fund is removed from our list, its stale data
        # doesn't stick around.
        if any("structured_data" in entry for entry in raw_data):
            logger.info("Purging old live NAV records to ensure fresh state...")
            # We target anything that has a 'section_type' metadata, 
            # which is unique to our structured fund chunks.
            try:
                # Chroma $in filter can sometimes fail on delete, so we delete each explicitly
                for stype in ["key_metrics", "investment_details", "fund_profile"]:
                    try:
                        self.db_manager.delete_by_filter(where={"section_type": stype})
                    except Exception:
                        pass
            except Exception as e:
                 logger.warning(f"Cleanup failed (possibly empty collection): {e}")

        for entry in raw_data:
            scheme_name = entry.get("scheme_name", "Unknown")

            if "structured_data" in entry:
                # ---- New structured format: ALWAYS upsert by ID ----
                # Rationale: NAV, AUM and expense ratio change every market day.
                # Skipping an upsert based on hash sameness would leave the
                # `last_updated` field stale, so we unconditionally refresh.
                chunks = self._create_structured_chunks(entry)
                for chunk in chunks:
                    chunk_text = chunk["text"]
                    section_type = chunk["section_type"]
                    chunk_hash = self._generate_hash(chunk_text)
                    chunk_id = f"{scheme_name}_{section_type}"

                    metadata = chunk["metadata"]
                    metadata["chunk_hash"] = chunk_hash
                    metadata["chunk_index"] = 0

                    structured_ids.append(chunk_id)
                    structured_docs.append(chunk_text)
                    structured_metas.append(metadata)

                logger.info(
                    f"  -> {scheme_name}: queued {len(chunks)} structured chunks for upsert"
                )

            else:
                # ---- Legacy markdown format: hash-deduped ----
                url = entry.get("url")
                content = entry.get("content")
                timestamp = entry.get("timestamp")
                chunks = self.text_splitter.split_text(content)

                new_count = 0
                for i, chunk_text in enumerate(chunks):
                    chunk_hash = self._generate_hash(chunk_text)
                    if chunk_hash in existing_hashes:
                        continue  # unchanged — skip embedding
                    new_count += 1
                    chunk_id = f"{scheme_name}_{i}"
                    metadata = {
                        "source_url": url,
                        "scheme_name": scheme_name,
                        "last_updated": timestamp,
                        "chunk_hash": chunk_hash,
                        "chunk_index": i,
                    }
                    legacy_ids.append(chunk_id)
                    legacy_docs.append(chunk_text)
                    legacy_metas.append(metadata)

                if new_count:
                    logger.info(
                        f"  -> {scheme_name}: {new_count}/{len(chunks)} legacy chunks changed"
                    )

        # --- Embed & upsert structured data (always) ---
        if structured_docs:
            logger.info(
                f"Embedding and upserting {len(structured_docs)} structured (live NAV) chunks..."
            )
            embeddings = self.embeddings.embed_documents(structured_docs)
            self.db_manager.upsert_documents(
                ids=structured_ids,
                documents=structured_docs,
                metadatas=structured_metas,
                embeddings=embeddings,
            )
            logger.info("Structured data upsert complete.")

        # --- Embed & upsert changed legacy chunks ---
        if legacy_docs:
            logger.info(
                f"Embedding and upserting {len(legacy_docs)} changed legacy chunks..."
            )
            embeddings = self.embeddings.embed_documents(legacy_docs)
            self.db_manager.upsert_documents(
                ids=legacy_ids,
                documents=legacy_docs,
                metadatas=legacy_metas,
                embeddings=embeddings,
            )
            logger.info("Legacy data upsert complete.")

        if not structured_docs and not legacy_docs:
            logger.info("No structured data returned from scraper — check scraper logs.")

        logger.info("Vector DB update complete.")


if __name__ == "__main__":
    raw_data_path = 'data/raw_scraped_data.json'
    if os.path.exists(raw_data_path):
        with open(raw_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        processor = DataProcessor()
        processor.process_data(data)
    else:
        print("Raw data not found. Please run scraper first.")
