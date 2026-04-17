import os
import sys
from dotenv import load_dotenv

# Add paths
sys.path.append(os.path.join(os.getcwd(), 'src', 'retrieval'))
sys.path.append(os.path.join(os.getcwd(), 'src', 'database'))

from security_layer import SecurityLayer

def test_intent_bug():
    load_dotenv()
    security = SecurityLayer()
    
    query = "Which is the best HDFC fund for me to invest in for high returns?"
    print(f"\nTesting Query: {query}")
    
    result = security.classify_intent(query)
    print(f"Detected Intent: {result.intent}")
    print(f"Confidence: {result.confidence}")
    print(f"Reasoning: {result.reasoning}")
    
    if result.intent == "ADVISORY":
        print("\nSUCCESS: Query correctly identified as ADVISORY.")
    else:
        print(f"\nFAILURE: Query identified as {result.intent}. Expected ADVISORY.")

if __name__ == "__main__":
    test_intent_bug()
