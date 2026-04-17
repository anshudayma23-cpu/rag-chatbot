import sys
import os
from dotenv import load_dotenv

# Add paths for imports
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(base_dir, "src", "retrieval"))
sys.path.append(os.path.join(base_dir, "src", "database"))

from main import RAGSystem

load_dotenv()

def run_test(rag, query):
    print(f"\nQUERY: {query}")
    print("-" * 50)
    response = rag.handle_query(query)
    print(f"RESPONSE:\n{response}")
    print("-" * 50)

def main():
    try:
        rag = RAGSystem()
        
        test_queries = [
            "Hi there! Who are you?", # GREETING
            "What is the exit load for HDFC Small Cap Fund?" # FACTUAL
        ]
        
        for q in test_queries:
            run_test(rag, q)
            
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
