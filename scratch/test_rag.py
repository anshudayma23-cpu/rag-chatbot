import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))
sys.path.append(os.path.join(os.getcwd(), "src", "retrieval"))

from retrieval.main import RAGSystem

def test_query():
    load_dotenv()
    rag = RAGSystem()
    query = "Who manages HDFC Defence Fund?"
    print(f"\nUser: {query}")
    response = rag.handle_query(query)
    print(f"\nAssistant: {response}\n")

if __name__ == "__main__":
    test_query()
