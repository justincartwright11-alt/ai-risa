import requests
import json

base_url = "http://127.0.0.1:5005/chat/send"

def test_query(msg, timeout=15):
    print(f"Testing: {msg}")
    try:
        response = requests.post(base_url, json={"message": msg}, timeout=timeout)
        print(f"Status: {response.status_code}")
        data = response.json()
        resp_text = data.get('response', '')
        print(f"Action: {resp_text.splitlines()[0] if resp_text else 'No response'}")
        if "Normalized event" in resp_text:
             print(f"Normalized: {resp_text.split('Normalized event: ')[1].splitlines()[0]}")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 30)

test_query("help")
test_query("run something")
