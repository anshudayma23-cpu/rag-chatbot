import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))
sys.path.append(os.path.join(os.getcwd(), "src", "retrieval"))

from security_layer import SecurityLayer

def test_intent():
    load_dotenv()
    security = SecurityLayer()
    query = "Who manages HDFC Defence Fund?"
    print(f"\nQuery: {query}")
    
    intent_res = security.classify_intent(query)
    print(f"\nIntent: {intent_res.intent}")
    print(f"Confidence: {intent_res.confidence}")
    print(f"Reasoning: {intent_res.reasoning}")
    print(f"Detected Fund: {intent_res.detected_fund}")

if __name__ == "__main__":
    test_intent()
