import os
import requests
from datetime import datetime

# =====================
# VARIABLES DE ENTORNO
# =====================
API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# =====================
# CONFIG
# =====================
API_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-apisports-key": API_KEY
}

# LIGAS A MONITOREAR (IDs que tú confirmaste)
LEAGUE_IDS = [
    363,  # Ethiopia
    585,  # Uganda
    567,  # Tanzania
    400,  # Zambia
    276,  # Kenya
    324,  # India I-League
    398   # Bangladesh
]

# =====================
# TELEGRAM
# =====================
def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    r = requests.post(url, data=payload, timeout=15)
    r.raise_for_status()

# =====================
# API FOOTBALL
# =====================
def get_next_fixtures():
    fixtures = []

    for league_id in LEAGUE_IDS:
        params = {
            "league": league_id,
            "season": 2025,
            "next": 1
        }

        r = requests.get(f"{API_URL}/fixtures", headers=HEADERS, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()

        if data.get("response"):
            fixtures.append(data["response"][0])

    return fixtures

# =====================
# MAIN
# =====================
def main():
    fixtures = get_next_fixtures()

    if not fixtures:
        send_telegram("⚠️ PRUEBA BOT\nNo se encontró ningún partido en las ligas monitoreadas.")
        return

    # TOMAMOS EL PRIMER PARTIDO DISPONIBLE (FORZADO)
    match = fixtures[0]

    home = match["teams"]["home"]["name"]
    away = match["teams"]["away"]["name"]
    league = match["league"]["name"]
    country = match["league"]["country"]
    date_utc = match["fixture"]["date"]

    date_local = datetime.fromisoformat(date_utc.replace("Z", "+00:00"))

    message = (
        "🧪 PRUEBA BOT — PARTIDO DETECTADO\n\n"
        f"🏟 Partido: {home} vs {away}\n"
        f"🏆 Liga: {league} ({country})\n"
        f"📅 Fecha: {date_local}\n\n"
        "Este mensaje confirma que:\n"
        "✅ API-Football responde\n"
        "✅ GitHub Actions ejecuta\n"
        "✅ Telegram notifica\n\n"
        "Luego se vuelven a activar criterios de empate."
    )

    send_telegram(message)

# =====================
# RUN
# =====================
if __name__ == "__main__":
    main()
