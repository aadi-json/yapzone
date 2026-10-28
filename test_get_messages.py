import requests

TOKEN = "257d0c1a03d9e7dd6e87af89042bcdd909d9dc42"

headers = {
    "Authorization": f"Token {TOKEN}",
}

url = "http://127.0.0.1:8000/api/chat/conversations/2/messages/"

try:
    response = requests.get(
        url,
        headers=headers,
        timeout=10,
    )

    print("Status Code:", response.status_code)
    print("Messages:")

    if response.ok:
        for message in response.json():
            print(f"\nMessage ID: {message['id']}")
            print(f"Sender: {message['sender_username']}")
            print(f"Content: {message['content']}")
            print(f"Timestamp: {message['timestamp']}")
    else:
        print(response.text)

except requests.RequestException as error:
    print("Request failed:", error)
