import requests
import time
import uuid

API_URL = "http://localhost:5000/api/chat"
SESSION_ID = "linkedin_demo_" + str(uuid.uuid4())[:8]

QUERIES = [
    "Who manages HDFC Defence Fund?",
    "What is the latest NAV of HDFC Small Cap Fund?",
    "What is the expense ratio for HDFC NIFTY 50 Index Fund?",
    "Is there an exit load for HDFC Multi Cap Fund?",
    "What is the risk level of HDFC Mid Cap Fund?",
    "What is the minimum SIP for HDFC Balanced Advantage Fund?",
    "When was HDFC Silver ETF FoF launched?",
    "Who is the Prime Minister of India?",
    "Should I invest in HDFC Small Cap Fund or Mid Cap Fund?",
    "What is the benchmark index for HDFC Short Term Opportunities Fund?"
]

def run_test():
    print(f"--- Starting LinkedIn Sample Q&A Test (Session: {SESSION_ID}) ---\n")
    start_time = time.time()
    
    for i, query in enumerate(QUERIES, 1):
        print(f"[{i}/10] Query: {query}")
        try:
            # We hit the backend directly since it's already running
            res = requests.post(API_URL, json={"message": query, "session_id": SESSION_ID})
            if res.status_code == 200:
                data = res.json()
                print(f"Answer: {data.get('response')}")
            else:
                print(f"Error: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"Connection Error: {e}")
        
        # Small delay between questions for readability
        print("-" * 80)
        time.sleep(3) 
    
    # Total runtime goal is 120 seconds
    elapsed = time.time() - start_time
    remaining = 120 - elapsed
    if remaining > 0:
        print(f"\nAll 10 queries processed in {elapsed:.1f}s.")
        print(f"Keeping chatbot session active for remaining {remaining:.1f}s to fulfill '2 minutes' request...")
        time.sleep(remaining)
    
    print(f"\n--- Demo Complete. Total duration: {time.time() - start_time:.1f}s ---")

if __name__ == "__main__":
    run_test()
