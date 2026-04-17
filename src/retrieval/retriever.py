import os
import sys
from typing import List
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

# Add parent directories to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database"))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ingestion"))

from chroma_manager import VectorDBManager
from processor import DataProcessor

class HybridRetriever:
    def __init__(self, persist_directory: str = "docs/vectordb", collection_name: str = "mutual_fund_faqs"):
        self.db_manager = VectorDBManager(persist_directory=persist_directory, collection_name=collection_name)
        
        # 1. Initialize Vector Retriever (Using Free local BGE model)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={'device': 'cpu'}
        )
        
        # 2. Get all documents for BM25 (Sparse Retrieval)
        all_docs_data = self.db_manager.collection.get(include=['documents', 'metadatas'])
        documents = [
            Document(page_content=doc, metadata=meta) 
            for doc, meta in zip(all_docs_data['documents'], all_docs_data['metadatas'])
        ]
        
        if not documents:
            print("Warning: No documents found in Chroma. BM25 initialization failed.")
            self.ensemble_retriever = None
        else:
            # 3. Initialize BM25 Retriever
            self.bm25_retriever = BM25Retriever.from_documents(documents)
            self.bm25_retriever.k = 10
            
            # 4. Initialize LangChain Chroma Retriever
            from langchain_chroma import Chroma
            vectorstore = Chroma(
                client=self.db_manager.client,
                collection_name=collection_name,
                embedding_function=self.embeddings
            )
            vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
            
            # 5. Create Ensemble Retriever (Hybrid)
            # This pair provides high accuracy without needing a local reranker
            self.ensemble_retriever = EnsembleRetriever(
                retrievers=[self.bm25_retriever, vector_retriever],
                weights=[0.3, 0.7]
            )
            
            # 6. Final Pipeline 
            self.pipeline = self.ensemble_retriever

    def retrieve(self, query: str) -> List[Document]:
        if not self.ensemble_retriever:
            return []
        
        print(f"Executing hybrid retrieval + reranking for: {query}")
        return self.pipeline.invoke(query)

if __name__ == "__main__":
    # Test
    retriever = HybridRetriever()
    results = retriever.retrieve("What is the exit load for HDFC Small Cap?")
    for i, res in enumerate(results):
        print(f"\n[{i+1}] {res.metadata.get('scheme_name')}")
        print(f"Content: {res.page_content[:200]}...")
