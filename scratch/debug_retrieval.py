import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "database"))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "ingestion"))
from chroma_manager import VectorDBManager
from processor import DataProcessor
from dotenv import load_dotenv
load_dotenv()

manager = VectorDBManager()
stats = manager.get_collection_stats()
count = stats["count"]
name = stats["name"]
print(f"Collection: {name}, Total Chunks: {count}")

# Get unique scheme names
results = manager.collection.get(include=["metadatas"])
schemes = set(m.get("scheme_name", "?") for m in results["metadatas"])
print(f"\nSchemes in DB ({len(schemes)}):")
for s in sorted(schemes):
    print(f"  - {s}")

# Now test retrieval for HDFC Flexi Cap / Equity Fund
print("\n--- Testing vector search ---")
processor = DataProcessor()
embeddings = processor.embeddings

query = "What is the current NAV of HDFC Flexi Cap Fund Direct Growth?"
query_vector = embeddings.embed_query(query)
results = manager.query(query_embeddings=[query_vector], n_results=3)

print(f"\nQuery: {query}")
print(f"Top 3 results:")
for i, (doc, doc_id, meta) in enumerate(zip(results["documents"][0], results["ids"][0], results["metadatas"][0])):
    scheme = meta.get("scheme_name", "?")
    print(f"\n[{i+1}] ID: {doc_id}")
    print(f"Scheme: {scheme}")
    print(f"Content (first 300 chars): {doc[:300]}")
