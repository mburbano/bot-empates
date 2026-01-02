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

def get_any_fixture_next_7_days():
    today = datetime.utcnow().date()

    for i in range(1, 8):  # próximos 7 días
        date_str = (today + timedelta(days=i)).strftime("%Y-%m-%d")

        params = {
            "date": date_str,
            "status": "NS"
        }

        r = requests.get(f"{API_URL}/fixtures", headers=HEADERS, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()

        if data.get("response"):
            return data["response"][0], date_str

    return None, None

def main():
    match, date_used = get_any_fixture_next_7_days()

    if not match:
        send_telegram(
            "❌ PRUEBA BOT\n"
            "La API no devolvió partidos en los próximos 7 días.\n"
            "Esto es límite del plan FREE."
        )
        return

    home = match["teams"]["home"]["name"]
    away = match["teams"]["away"]["name"]
    league = match["league"]["name"]
    country = match["league"]["country"]
    kickoff = match["fixture"]["date"]

    message = (
        "✅ PRUEBA REAL — PARTIDO ENCONTRADO\n\n"
        f"🏟 {home} vs {away}\n"
        f"🏆 {league} ({country})\n"
        f"📅 Fecha API: {date_used}\n"
        f"⏰ Kickoff: {kickoff}\n\n"
        "La tubería funciona.\n"
        "Ahora se pueden aplicar filtros de empate."
    )

    send_telegram(message)

if __name__ == "__main__":
    main()
