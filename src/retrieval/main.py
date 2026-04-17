import sys
import os
import uuid
import time
from dotenv import load_dotenv

# Add paths to allow imports
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "database"))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from retriever import HybridRetriever
from generator import FactualGenerator
from security_layer import SecurityLayer, ExtendedIntentResponse
from conversation_manager import ConversationManager
from shared_state import shared_state

load_dotenv()

class RAGSystem:
    def __init__(self, session_id: str = None, use_shared: bool = True):
        # Session management first
        self.session_id = session_id or str(uuid.uuid4())
        
        if use_shared:
            components = shared_state.get_components()
            self.security = components["security"]
            self.retriever = components["retriever"]
            self.generator = components["generator"]
            self.conversation = components["conversation_manager"]
            print(f"--- RAGSystem using Shared Components (Session: {self.session_id}) ---")
        else:
            print("--- Initializing New RAGSystem Components (Heavy) ---")
            self.security = SecurityLayer()
            self.retriever = HybridRetriever()
            self.generator = FactualGenerator()
            self.conversation = ConversationManager()
        
        print(f"--- Session ID: {self.session_id} ---")

    def handle_query(self, query: str, session_id: str = None) -> str:
        t_start = time.time()
        current_session = session_id or self.session_id
        
        # Phase 3.4: Rate Limiting Check
        allowed, reason = self.security.check_rate_limit(current_session, query)
        if not allowed:
            return f"Request blocked: {reason}"
        
        # Phase 3.1: Query Guard & Intent Routing
        t_intent_start = time.time()
        intent_res = self.security.classify_intent(query)
        intent = intent_res.intent
        detected_fund = intent_res.detected_fund
        t_intent = time.time() - t_intent_start
        
        # Phase 4.3: Context-Aware Query Enhancement
        t_enhance_start = time.time()
        enhanced_query, was_modified = self.conversation.enhance_query(query, current_session)
        t_enhance = time.time() - t_enhance_start
        
        if self.conversation.needs_disambiguation(query, current_session):
            disambiguation_msg = "I see you've asked about multiple funds. Which one are you referring to? Please specify the fund name clearly."
            self.conversation.log_message(current_session, "assistant", disambiguation_msg, "UNCLEAR")
            return disambiguation_msg
        
        # Handlers for non-factual intents
        if intent != "FACTUAL":
            response = self.security.get_refusal(intent)
            self.conversation.log_message(current_session, "user", query, intent)
            self.conversation.log_message(current_session, "assistant", response, intent)
            print(f"  -> Total Latency (Non-Factual): {time.time() - t_start:.2f}s")
            return response
            
        # Phase 2.2 & 2.3: Retrieval
        self.conversation.log_message(current_session, "user", query, intent)
        
        t_retrieval_start = time.time()
        try:
            context_docs = self.retriever.retrieve(enhanced_query)
            t_retrieval = time.time() - t_retrieval_start
            
            if not context_docs:
                response = "I couldn't find any relevant factual data in our database to answer your query."
                self.conversation.log_message(current_session, "assistant", response, intent)
                return response
            
            # Phase 2.4 & 2.5: Generation
            t_gen_start = time.time()
            raw_response = self.generator.generate(enhanced_query, context_docs)
            t_gen = time.time() - t_gen_start
            
            # Safety filter
            filtered_response = self.security.filter_output(raw_response, context_docs, enhanced_query, intent)
            
            # Message Logging
            chunk_ids = [f"{doc.metadata.get('scheme_name', 'unknown')}_{doc.metadata.get('section_type', 'unknown')}" for doc in context_docs]
            sources = list(set(doc.metadata.get('source_url', '') for doc in context_docs if doc.metadata.get('source_url')))
            
            self.conversation.log_message(current_session, "assistant", filtered_response, intent, sources=sources, retrieved_chunks=chunk_ids)
            
            t_total = time.time() - t_start
            print(f"--- PERFORMANCE LOG ---")
            print(f"  Intent Classify:  {t_intent:.2f}s")
            print(f"  Query Enhance:    {t_enhance:.2f}s")
            print(f"  Retrieval:        {t_retrieval:.2f}s")
            print(f"  Generation:       {t_gen:.2f}s")
            print(f"  TOTAL LATENCY:    {t_total:.2f}s")
            print(f"----------------------")
            
            return filtered_response
                
        except Exception as e:
            print(f"Error during factual processing: {e}")
            return "An error occurred while retrieving information."
        
        return "I'm sorry, I couldn't understand the intent of your query."
    
    def get_conversation_history(self, limit: int = 10) -> list:
        """Get conversation history for current session."""
        messages = self.conversation.get_session_history(self.session_id, limit)
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "intent": msg.intent
            }
            for msg in messages
        ]
    
    def export_conversation(self, format: str = "json") -> str:
        """Export current session conversation. Returns file path."""
        return self.conversation.export_session(self.session_id, format)
    
    def clear_conversation(self) -> str:
        """Clear current conversation but keep session."""
        return self.conversation.clear_session(self.session_id)

def main():
    rag = RAGSystem()
    print("\nWelcome to the HDFC Mutual Fund Assistant!")
    print("Type 'exit' to quit.\n")
    
    while True:
        user_input = input("User: ")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        response = rag.handle_query(user_input)
        print(f"\nAssistant: {response}\n")

if __name__ == "__main__":
    main()
