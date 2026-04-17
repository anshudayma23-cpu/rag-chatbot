import time
import requests
import json

BASE_URL = "http://localhost:3000" # Testing via frontend proxy is not ideal, let's hit backend directly
API_URL = "http://localhost:5000/api/chat"

def test_performance():
    queries = [
        "Who manages HDFC Defence Fund?",
        "What is the exit load for HDFC Small Cap Fund?",
        "Which fund should I buy?", # This should be fast as it's a refusal
        "Who is the fund manager for HDFC Top 100 Fund?",
    ]
    
    session_id = "test_perf_session_" + str(int(time.time()))
    print(f"Testing with session: {session_id}\n")
    
    for query in queries:
        print(f"User: {query}")
        start_time = time.time()
        
        try:
            response = requests.post(API_URL, json={
                "message": query,
                "session_id": session_id
            })
            
            latency = time.time() - start_time
            if response.status_code == 200:
                res_json = response.json()
                print(f"Assistant: {res_json['response'][:100]}...")
                print(f"Request Latency (API side): {latency:.2f}s")
            else:
                print(f"Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error connecting to backend: {e}")
        
        print("-" * 30)

if __name__ == "__main__":
    # Wait a bit for backend to be fully ready
    time.sleep(2)
    test_performance()
