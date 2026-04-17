import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "retrieval"))

from main import RAGSystem

# Force utf-8 encoding for standard output to handle characters like the Rupee symbol (₹)
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def run_e2e_tests():
    print("=== HDFC Mutual Fund RAG System End-to-End Test ===\n")
    print("Testing all 4 Phases: Ingestion, Retrieval+Generation, Security, Multi-Thread Chat\n")
    
    rag = RAGSystem()
    
    test_queries = [
        # Phase 2/3: Greeting
        "Hi there! Who are you?",
        
        # Phase 2/4: Factual with follow-up (tests query enhancement)
        "What is the exit load for HDFC Small Cap Fund?",
        "What about its NAV?",  # Ambiguous - should resolve to HDFC Small Cap
        
        # Phase 2: Factual
        "Could you tell me the current NAV of HDFC Defence Fund?",
        
        # Phase 3: Advisory refusal
        "Is HDFC Mid Cap Fund a good investment for next 5 years?",
        
        # Phase 3: Comparison refusal
        "Which is better: HDFC Small Cap or HDFC Mid Cap?",
        
        # Phase 3: Out of context
        "Who is the Prime Minister of India?",
        
        # Phase 4: Unclear query
        "xyz123",  # Too short - should be rate limited or unclear
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test Case {i}: {query} ---")
        response = rag.handle_query(query)
        print(f"Assistant: {response}")
        print("-" * 50)
    
    # Phase 4: Show conversation history
    print("\n=== Conversation History (Phase 4) ===")
    history = rag.get_conversation_history(limit=5)
    for msg in history:
        print(f"[{msg['role'].upper()}] ({msg['intent']}): {msg['content'][:60]}...")
    
    # Phase 4: Export conversation
    print("\n=== Exporting Conversation (Phase 4) ===")
    export_path = rag.export_conversation(format="markdown")
    print(f"Exported to: {export_path}")

if __name__ == "__main__":
    run_e2e_tests()
