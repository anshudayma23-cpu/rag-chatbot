import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))
sys.path.append(os.path.join(os.getcwd(), "src", "database"))

from chroma_manager import VectorDBManager

def check_defence():
    load_dotenv()
    manager = VectorDBManager()
    
    # We can't search by content directly with get(), but we can list metadatas
    # and see if any scheme_name contains "Defence"
    print("--- Checking for Defence Fund in DB ---")
    results = manager.collection.get(include=['metadatas'])
    
    defence_funds = []
    for metadata in results['metadatas']:
        scheme = metadata.get('scheme_name', '')
        if 'Defence' in scheme:
            defence_funds.append(scheme)
    
    unique_defence = sorted(list(set(defence_funds)))
    print(f"Found {len(unique_defence)} unique schemes with 'Defence' in name:")
    for f in unique_defence:
        print(f" - {f}")
    
    if not unique_defence:
        print("\nSearching in documents instead...")
        # Try a semantic query
        from langchain_huggingface import HuggingFaceEmbeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        query_vector = embeddings.embed_query("HDFC Defence Fund")
        results = manager.query(query_embeddings=[query_vector], n_results=5)
        
        print("\nSemantic search results for 'HDFC Defence Fund':")
        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            print(f"\n[{i+1}] Scheme: {metadata.get('scheme_name')}")
            print(f"Content snippet: {doc[:150]}...")

if __name__ == "__main__":
    check_defence()
