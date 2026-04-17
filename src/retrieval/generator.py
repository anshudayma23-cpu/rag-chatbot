import os
import re
from typing import List, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

class FactualGenerator:
    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        self.llm = ChatGroq(
            model_name=model_name,
            temperature=0, # Deterministic (Phase 2.4)
            model_kwargs={"top_p": 0.9},
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", 
             "You are a Factual Mutual Fund Assistant for HDFC Mutual Funds.\n"
             "Your goal is to provide accurate, concise answers based ONLY on the provided context.\n\n"
             "STRICT RULES:\n"
             "1. Use ONLY the provided context. If the answer is not in the context, say 'I do not have factual information regarding this query.'\n"
             "2. Do NOT provide investment advice or recommendations.\n"
             "3. Always cite the SCHEME NAME and the specific section used (e.g., 'Source: HDFC Small Cap - Fees').\n"
             "4. Use Chain-of-Thought: Mentally identify the relevant facts in the text before writing the final response.\n"
             "5. Maintain a deterministic and professional tone.\n\n"
             "CONTEXT:\n{context}"),
            ("user", "{query}")
        ])
        
        self.chain = self.prompt | self.llm | StrOutputParser()

    def _post_process(self, response: str) -> str:
        """Compliance Formatting (Phase 2.5)"""
        # Ensure mandatory disclaimer
        disclaimer = "\n\n**Disclaimer**: Facts-only. No investment advice. Please refer to official SID/KIM documents for complete details."
        
        if disclaimer.strip() not in response:
            response += disclaimer
            
        # Optional: Regex check for sentence count if needed (currently just ensuring footer)
        return response

    def generate(self, query: str, context_docs: List[Any]) -> str:
        # Format context
        context_text = "\n\n".join([
            f"--- Document: {doc.metadata.get('scheme_name')} ---\n{doc.page_content}"
            for doc in context_docs
        ])
        
        print("Generating factual response...")
        try:
            response = self.chain.invoke({"query": query, "context": context_text})
            return self._post_process(response)
        except Exception as e:
            print(f"Error in FactualGenerator: {e}")
            return "Error: Unable to generate response at this time."

if __name__ == "__main__":
    # Mock documents for test
    from langchain_core.documents import Document
    mock_docs = [
        Document(
            page_content="HDFC Small Cap Fund has an exit load of 1% if redeemed within 1 year. The current NAV is 120.50.",
            metadata={"scheme_name": "HDFC Small Cap Fund"}
        )
    ]
    generator = FactualGenerator()
    answer = generator.generate("What is the exit load?", mock_docs)
    print(f"Answer:\n{answer}")
