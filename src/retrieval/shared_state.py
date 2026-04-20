import os
import sys
import threading
from datetime import datetime
from typing import Optional

# Add retrieval to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from security_layer import SecurityLayer
from retriever import HybridRetriever
from generator import FactualGenerator
from conversation_manager import ConversationManager


class SharedRAGState:
    """
    Singleton manager for sharing heavy RAG components across sessions.

    Supports live reload — calling reload() re-fetches ALL documents from
    Chroma Cloud and rebuilds the BM25 keyword index so the running server
    immediately reflects whatever the daily scraper just stored. The old
    in-memory index is completely discarded.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SharedRAGState, cls).__new__(cls)
            cls._instance.initialized = False
            cls._instance.security = None
            cls._instance.retriever = None
            cls._instance.generator = None
            cls._instance.conversation_manager = None
            cls._instance.last_loaded_at = None
        return cls._instance

    def initialize(self):
        """Pre-load all models and retrievers (runs once at startup)."""
        if self.initialized:
            return
        self._load()

    def reload(self):
        """
        Force a full reload of the retriever from the latest Chroma data.

        - Discards the old in-memory BM25 index entirely.
        - Re-fetches ALL documents from Chroma Cloud.
        - Rebuilds the BM25 + vector ensemble retriever from scratch.
        - Security / Generator / ConversationManager are NOT reloaded
          (they have no stale state).

        Thread-safe: uses a lock so concurrent requests don't double-reload.
        """
        with self._lock:
            print("\n--- 🔄 Reloading retriever from Chroma (flush old BM25 index) ---")
            old_retriever = self.retriever
            try:
                self.retriever = HybridRetriever()
                self.last_loaded_at = datetime.utcnow().isoformat() + "Z"
                print(f"--- ✅ Retriever reloaded at {self.last_loaded_at} ---\n")
                # Help GC collect the old BM25 index
                del old_retriever
            except Exception as e:
                # Roll back to the old retriever so the server keeps working
                self.retriever = old_retriever
                print(f"--- ❌ Reload failed, keeping old retriever: {e} ---\n")
                raise

    def _load(self):
        """Internal: load all components fresh."""
        print("\n--- Pre-loading Shared RAG Components ---")
        self.security = SecurityLayer()
        self.retriever = HybridRetriever()
        self.generator = FactualGenerator()
        self.conversation_manager = ConversationManager()
        self.initialized = True
        self.last_loaded_at = datetime.utcnow().isoformat() + "Z"
        print(f"--- All Shared Components Ready (loaded at {self.last_loaded_at}) ---\n")

    @classmethod
    def get_components(cls):
        instance = cls()
        if not instance.initialized:
            instance.initialize()
        return {
            "security": instance.security,
            "retriever": instance.retriever,
            "generator": instance.generator,
            "conversation_manager": instance.conversation_manager,
        }


# Global instance for easy access
shared_state = SharedRAGState()
