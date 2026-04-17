import os
from typing import Literal
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

class IntentResponse(BaseModel):
    intent: Literal["FACTUAL", "ADVISORY", "GREETING"] = Field(
        description="The classified intent of the user query."
    )
    reasoning: str = Field(description="Brief explanation for the classification.")

class IntentRouter:
    def __init__(self, model_name: str = "llama-3.1-8b-instant"):
        self.llm = ChatGroq(
            model_name=model_name,
            temperature=0,
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
        
        self.output_parser = JsonOutputParser(pydantic_object=IntentResponse)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", 
             "You are a specialized router for a Mutual Fund FAQ Assistant.\n"
             "Your task is to classify the user's intent into exactly one of these categories:\n"
             "1. GREETING: General pleasantries, hello, who are you, etc.\n"
             "2. FACTUAL: Questions about specific fund data, NAV, expense ratios, holdings, fees, or how funds work.\n"
             "3. ADVISORY: Requests for investment advice, recommendations, comparisons for the purpose of choosing a fund, or 'should I buy' type questions.\n\n"
             "{format_instructions}"),
            ("user", "{query}")
        ]).partial(format_instructions=self.output_parser.get_format_instructions())
        
        self.chain = self.prompt | self.llm | self.output_parser

    def route(self, query: str) -> IntentResponse:
        print(f"Routing query: {query}")
        try:
            response = self.chain.invoke({"query": query})
            return IntentResponse(**response)
        except Exception as e:
            print(f"Error in IntentRouter: {e}")
            # Fallback to FACTUAL to be safe, or GREETING if it looks like one
            return IntentResponse(intent="FACTUAL", reasoning="Fallback due to error.")

if __name__ == "__main__":
    # Test
    router = IntentRouter()
    queries = [
        "Hello!",
        "What is the current NAV of HDFC Small Cap?",
        "Should I invest in HDFC Defence fund for long term?",
        "Compare HDFC Mid Cap vs Small Cap for me."
    ]
    for q in queries:
        res = router.route(q)
        print(f"Query: {q} -> Intent: {res.intent} ({res.reasoning})")
