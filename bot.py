import requests
import os

API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

HEADERS = {
    "x-apisports-key": API_KEY
}

LEAGUES = [
    363,  # Ethiopia
    585,  # Uganda
    567,  # Tanzania
    400,  # Zambia
    276,  # Kenya
    324,  # India I-League
    398   # Bangladesh
]

def get_fixtures():
    fixtures = []
    for league in LEAGUES:
        url = f"https://v3.football.api-sports.io/fixtures?league={league}&next=5"
        r = requests.get(url, headers=HEADERS)
        data = r.json()
        fixtures.extend(data["response"])
    return fixtures

def get_team_stats(team_id, league, season):
    url = f"https://v3.football.api-sports.io/teams/statistics?team={team_id}&league={league}&season={season}"
    r = requests.get(url, headers=HEADERS)
    return r.json()["response"]

def analyze_match(stats):
    draw_rate = stats["draw_rate"]
    goals_avg = stats["goals_avg"]
    goal_diff = stats["goal_diff"]

    score = 0

    # Criterios relajados SOLO PARA PRUEBA
    if draw_rate >= 0.30:
        score += 1
    if goals_avg <= 3.2:
        score += 1
    if goal_diff <= 1.2:
        score += 1

    # BONUS para que siempre exista ganador
    score += draw_rate

    return score, draw_rate, goals_avg, goal_diff



def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    })

def main():
    fixtures = get_fixtures()
    best = None
    best_score = -1

    for f in fixtures:
        try:
            score, draw, goals, diff = analyze_match(f)
            if score > best_score:
                best_score = score
                best = (f, draw, goals, diff)
        except:
            continue

    if not best:
        send_message("⚠️ No se encontró ningún partido analizable.")
        return

    f, draw, goals, diff = best

    msg = (
        f"🤝 <b>MEJOR PARTIDO PARA EMPATE</b>\n\n"
        f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}\n"
        f"🏆 Liga: {f['league']['name']}\n"
        f"📅 Fecha: {f['fixture']['date'][:10]}\n\n"
        f"📊 Empates combinados: {round(draw*100,1)}%\n"
        f"⚽ Goles promedio: {round(goals,2)}\n"
        f"📉 Diferencia ofensiva: {round(diff,2)}"
    )

    send_message(msg)

if __name__ == "__main__":
    main()
