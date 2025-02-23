import requests

BOT_TOKEN = "7093173596:AAEzNaEEnB5cu8E7q9C_GGiLDXOKfbUHg_E"
'''response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates")
print(response.json())  # Look for "chat": {"id": ...} in the response'''
CHAT_ID = "-1002492776476"

def send_message_to_telegram(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"  # Optional: for bold/italic formatting
    }
    response = requests.post(url, data=payload)
    return response.json()

