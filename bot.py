import os
import requests
from datetime import datetime, timedelta

API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

API_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-apisports-key": API_KEY
}

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    r = requests.post(url, data=payload, timeout=15)
    r.raise_for_status()

def get_fixture_by_date():
    target_date = (datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d")

    params = {
        "date": target_date,
        "status": "NS"
    }

    r = requests.get(f"{API_URL}/fixtures", headers=HEADERS, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    if not data.get("response"):
        return None

    return data["response"][0]

def main():
    match = get_fixture_by_date()

    if not match:
        send_telegram("❌ No hay partidos NS para la fecha consultada.")
        return

    home = match["teams"]["home"]["name"]
    away = match["teams"]["away"]["name"]
    league = match["league"]["name"]
    country = match["league"]["country"]
    date_utc = match["fixture"]["date"]

    date_local = datetime.fromisoformat(date_utc.replace("Z", "+00:00"))

    message = (
        "✅ PRUEBA OK — PARTIDO ENCONTRADO\n\n"
        f"🏟 {home} vs {away}\n"
        f"🏆 {league} ({country})\n"
        f"📅 {date_local}\n\n"
        "Confirmado:\n"
        "✔ API responde\n"
        "✔ Hay fixtures\n"
        "✔ Telegram funciona\n"
    )

    send_telegram(message)

if __name__ == "__main__":
    main()

