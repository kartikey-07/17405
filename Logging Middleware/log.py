import requests
from datetime import datetime

LOGGING_SERVER_URL = "http://20.244.56.144/logging-service/log"

CLIENT_ID = "6a769574-25ec-4552-8b1f-9ffd69efd8ae"
CLIENT_SECRET = "WfpGXZVDRpUNgfqK"

def Log(stack: str, level: str, package: str, message: str):
    payload = {
        "stack": stack,
        "level": level,
        "package": package,
        "message": message,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "clientID": CLIENT_ID,
        "clientSecret": CLIENT_SECRET
    }

    try:
        response = requests.post(LOGGING_SERVER_URL, json=payload, timeout=2)
        if response.status_code != 200:
            print(f"[LOGGING FAILURE] {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[LOGGING ERROR] {e}")
