import requests
import os
from datetime import datetime

API_KEY = os.getenv("76bd4a4b6d1606696eefb7e7054f6f3a")
BOT_TOKEN = os.getenv("8306002599:AAEEcv-o44yX7hv9HqQGwVXQhQ4_MkMtSmUN")
CHAT_ID = os.getenv("2121426726")

LEAGUE_IDS = [363,585,567,400,276,324,398]  # Etiopía y ligas similares
SEASON = 2025

headers = {
    "x-apisports-key": API_KEY
}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg})

def main():
    señales = []
    for league in LEAGUE_IDS:
        url = f"https://v3.football.api-sports.io/fixtures?league={league}&season={SEASON}&next=10"
        r = requests.get(url, headers=headers).json()
        for f in r.get("response", []):
            h = f["teams"]["home"]["name"]
            a = f["teams"]["away"]["name"]
            odds = f.get("odds", {})
            señales.append(f"{h} vs {a}")

    if señales:
        send_telegram("⚽ PARTIDOS CON PERFIL DE EMPATE:\n" + "\n".join(señales))
    else:
        send_telegram("Sin partidos claros de empate.")

if __name__ == "__main__":
    main()
