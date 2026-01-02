import os
import requests
from datetime import datetime

API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": CHAT_ID, "text": text})
    print(r.status_code, r.text)

def main():
    # Mensaje de prueba (si llega, todo está bien)
    send_telegram("✅ Bot activo. Mensaje de prueba OK.")

if __name__ == "__main__":
    main()

