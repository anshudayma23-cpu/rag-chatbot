import os
import sys
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
    Reduces initialization latency from ~20s to <1s for warm requests.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SharedRAGState, cls).__new__(cls)
            cls._instance.initialized = False
            cls._instance.security = None
            cls._instance.retriever = None
            cls._instance.generator = None
            cls._instance.conversation_manager = None
        return cls._instance

    def initialize(self):
        """Pre-load all models and retrievers."""
        if self.initialized:
            return
            
        print("\n--- Pre-loading Shared RAG Components (Optimization) ---")
        self.security = SecurityLayer()
        self.retriever = HybridRetriever()
        self.generator = FactualGenerator()
        self.conversation_manager = ConversationManager()
        self.initialized = True
        print("--- All Shared Components Ready ---\n")

    @classmethod
    def get_components(cls):
        instance = cls()
        if not instance.initialized:
            instance.initialize()
        return {
            "security": instance.security,
            "retriever": instance.retriever,
            "generator": instance.generator,
            "conversation_manager": instance.conversation_manager
        }

# Global instance for easy access
shared_state = SharedRAGState()
