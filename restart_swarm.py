import requests
import json
import sys

# Try to find the dashboard port or assume 5000
url = "http://localhost:5000/api/action"
payload = {
    "action": "restart_daemons"
}
headers = {
    "Content-Type": "application/json"
}

print(f"Attempting to restart daemons via {url}...")
try:
    response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
