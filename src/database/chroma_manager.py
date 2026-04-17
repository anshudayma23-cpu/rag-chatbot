import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import os
import logging

logger = logging.getLogger("ingestion")

class VectorDBManager:
    def __init__(self, persist_directory: str = "docs/vectordb", collection_name: str = "mutual_fund_faqs"):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Load cloud configuration
        self.api_key = os.getenv("CHROMA_API_KEY")
        self.tenant = os.getenv("CHROMA_TENANT", "default_tenant")
        self.database = os.getenv("CHROMA_DATABASE", "default_database")
        
        if self.api_key:
            logger.info(f"Connecting to Chroma Cloud (Tenant: {self.tenant}, DB: {self.database})...")
            # Initialize the cloud client
            self.client = chromadb.CloudClient(
                api_key=self.api_key,
                tenant=self.tenant,
                database=self.database
            )
        else:
            logger.info(f"No API Key found. Falling back to local PersistentClient at {self.persist_directory}...")
            # Initialize the persistent client
            self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Initialize/Get the collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"} # Default for BGE/Normalized vectors
        )

    def upsert_documents(self, ids: List[str], documents: List[str], metadatas: List[Dict[str, Any]], embeddings: Optional[List[List[float]]] = None):
        """
        Upserts documents into the collection. 
        If embeddings are provided, they are used; otherwise, Chroma uses its default (if set) 
        or we expect the caller to handle embeddings if they are using a custom model.
        """
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings
        )

    def delete_by_ids(self, ids: List[str]):
        """Deletes documents by their IDs."""
        self.collection.delete(ids=ids)

    def clear_collection(self):
        """Deletes and recreates the collection for a clean re-ingestion."""
        logger.info(f"Clearing collection '{self.collection_name}'...")
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Collection '{self.collection_name}' cleared and recreated.")

    def get_collection_stats(self) -> Dict[str, Any]:
        """Returns statistics about the collection."""
        return {
            "count": self.collection.count(),
            "name": self.collection_name,
            "metadata": self.collection.metadata
        }

    def query(self, query_embeddings: List[List[float]], n_results: int = 5, where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Queries the collection using embeddings.
        """
        return self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where
        )

    def get_existing_hashes(self, scheme_name: Optional[str] = None) -> List[str]:
        """
        Retrieves all chunk hashes currently stored in the DB.
        Useful for the SHA-256 change detection logic.
        """
        where = {"scheme_name": scheme_name} if scheme_name else None
        results = self.collection.get(
            include=['metadatas'],
            where=where
        )
        return [m.get("chunk_hash") for m in results['metadatas'] if m.get("chunk_hash")]

if __name__ == "__main__":
    # Test initialization
    manager = VectorDBManager()
    stats = manager.get_collection_stats()
    print(f"Collection: {stats['name']}, Count: {stats['count']}")
