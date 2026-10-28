import requests

TOKEN = "257d0c1a03d9e7dd6e87af89042bcdd909d9dc42"

headers = {
    "Authorization": f"Token {TOKEN}",
    "Content-Type": "application/json",
}

url = "http://127.0.0.1:8000/api/chat/conversations/create/"

payload = {
    "participant_id": 2
}

try:
    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=10,
    )

    print("Status Code:", response.status_code)
    print("Response:", response.json())

except requests.RequestException as error:
    print("Request failed:", error)