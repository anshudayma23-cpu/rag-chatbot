import os
import sys

# Add paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(base_dir, "src", "database"))
sys.path.append(os.path.join(base_dir, "src", "ingestion"))

from chroma_manager import VectorDBManager
from langchain_huggingface import HuggingFaceEmbeddings

def verify():
    print("--- Verifying Vector DB ---")
    
    # Initialize Manager
    manager = VectorDBManager(persist_directory="docs/vectordb")
    stats = manager.get_collection_stats()
    
    print(f"Collection Name: {stats['name']}")
    print(f"Total Chunks: {stats['count']}")
    
    if stats['count'] == 0:
        print("Error: Collection is empty!")
        return

    # Initialize Embeddings for Query
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-en-v1.5",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Test Query
    query_text = "What is the exit load for HDFC Small Cap Fund?"
    print(f"\nTesting Query: '{query_text}'")
    
    query_vector = embeddings.embed_query(query_text)
    results = manager.query(query_embeddings=[query_vector], n_results=3)
    
    print("\nTop 3 Results:")
    for i, (doc, id, metadata) in enumerate(zip(results['documents'][0], results['ids'][0], results['metadatas'][0])):
        print(f"\n[{i+1}] ID: {id}")
        print(f"Scheme: {metadata.get('scheme_name')}")
        print(f"Distance: {results['distances'][0][i] if 'distances' in results else 'N/A'}")
        print(f"Content (first 200 chars): {doc[:200]}...")

if __name__ == "__main__":
    verify()
