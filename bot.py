import os
import requests

API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

HEADERS = {"x-apisports-key": API_KEY}

LEAGUES = {
    363: "Ethiopia Premier League",
    585: "Uganda Premier League",
    567: "Tanzania Premier League",
}

SEASON = 2024

def tg(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text})

def get(url):
    return requests.get(url, headers=HEADERS, timeout=20).json()

def main():
    for lid, lname in LEAGUES.items():
        data = get(
            f"https://v3.football.api-sports.io/fixtures"
            f"?league={lid}&season={SEASON}&next=5"
        )

        if not data.get("response"):
            tg(f"❌ {lname}: sin fixtures")
            continue

        f = data["response"][0]
        h = f["teams"]["home"]["name"]
        a = f["teams"]["away"]["name"]
        fecha = f["fixture"]["date"][:16].replace("T", " ")

        tg(
            f"🧪 TEST OK\n"
            f"⚽ {h} vs {a}\n"
            f"📅 {fecha}\n"
            f"🏟️ {lname}"
        )
        return   # ← este return está BIEN, dentro de main()

    tg("❌ No se pudo leer ningún partido")

if __name__ == "__main__":
    main()



