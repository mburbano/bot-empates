import os
import requests
from statistics import mean

API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

HEADERS = {"x-apisports-key": API_KEY}

# Ligas propensas al empate (IDs verificados)
LEAGUES = {
    363: "Ethiopia Premier League",
    585: "Uganda Premier League",
    567: "Tanzania Premier League",
    400: "Zambia Super League",
    276: "Kenya Premier League",
    324: "India I-League",
    398: "Bangladesh Premier League",
}

SEASON = 2024
NEXT_FIXTURES = 20
MIN_DRAW_ODDS = 2.80     # NO cuotas basura
MAX_AVG_GOALS = 2.2      # partidos cerrados
MIN_DRAW_RATE = 0.30     # 30% empates recientes

def tg(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg})

def get(url):
    return requests.get(url, headers=HEADERS, timeout=20).json()

def team_stats(team_id, league_id):
    url = f"https://v3.football.api-sports.io/teams/statistics"
    r = get(url + f"?team={team_id}&league={league_id}&season={SEASON}")
    if not r.get("response"):
        return None
    s = r["response"]
    played = s["fixtures"]["played"]["total"]
    draws = s["fixtures"]["draws"]["total"]
    goals_for = s["goals"]["for"]["total"]["total"]
    goals_against = s["goals"]["against"]["total"]["total"]
    avg_goals = (goals_for + goals_against) / played if played else 9
    draw_rate = draws / played if played else 0
    return avg_goals, draw_rate

def draw_odds(fixture_id):
    url = f"https://v3.football.api-sports.io/odds?fixture={fixture_id}"
    r = get(url)
    for b in r.get("response", []):
        for m in b.get("bookmakers", []):
            for bet in m.get("bets", []):
                if bet["name"] == "Match Winner":
                    for v in bet["values"]:
                        if v["value"] == "Draw":
                            try:
                                return float(v["odd"])
                            except:
                                pass
    return None

def main():
    señales = []

    for lid, lname in LEAGUES.items():
        fx = get(f"https://v3.football.api-sports.io/fixtures?league={lid}&season={SEASON}&next={NEXT_FIXTURES}")
        for f in fx.get("response", []):
            hid = f["teams"]["home"]["id"]
            aid = f["teams"]["away"]["id"]

            hs = team_stats(hid, lid)
            as_ = team_stats(aid, lid)
            if not hs or not as_:
                continue

            avg_goals = mean([hs[0], as_[0]])
            draw_rate = mean([hs[1], as_[1]])

            if avg_goals > MAX_AVG_GOALS or draw_rate < MIN_DRAW_RATE:
                continue

            odds = draw_odds(f["fixture"]["id"])
            if not odds or odds < MIN_DRAW_ODDS:
                continue

            h = f["teams"]["home"]["name"]
            a = f["teams"]["away"]["name"]
            fecha = f["fixture"]["date"][:16].replace("T", " ")
            señales.append(
                f"⚽ {h} vs {a}\n"
                f"📅 {fecha}\n"
                f"🎯 Empate\n"
                f"📊 Avg goles: {avg_goals:.2f}\n"
                f"📈 Draw rate: {draw_rate:.0%}\n"
                f"💰 Cuota: {odds}\n"
                f"🏟️ {lname}\n"
            )

    if señales:
        tg("🔥 SEÑALES DE EMPATE (FILTRADAS)\n\n" + "\n".join(señales))
    else:
        tg("ℹ️ Sin partidos con valor de empate ahora.")

if __name__ == "__main__":
    main()


