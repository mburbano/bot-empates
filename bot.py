import os
import requests
from datetime import datetime, timedelta, timezone

# =========================
# VARIABLES (NO CAMBIAR)
# =========================
API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# =========================
# CONFIG
# =========================
API_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-apisports-key": API_KEY
}

# Pesos del score
WEIGHT_DRAW_RATE = 0.5
WEIGHT_GOALS_AVG = 0.3
WEIGHT_GOAL_DIFF = 0.2

# Timezone Ecuador (UTC-5)
ECUADOR_OFFSET = timedelta(hours=-5)

# =========================
# HELPERS
# =========================
def api_get(endpoint, params):
    r = requests.get(f"{API_URL}/{endpoint}", headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json()["response"]

def get_fixtures():
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)

    return api_get("fixtures", {
        "from": today.isoformat(),
        "to": tomorrow.isoformat(),
        "status": "NS"
    })

def get_h2h(home_id, away_id):
    try:
        return api_get("fixtures/headtohead", {
            "h2h": f"{home_id}-{away_id}",
            "last": 10
        })
    except:
        return []

def analyze_match(fixture):
    home = fixture["teams"]["home"]
    away = fixture["teams"]["away"]

    h2h = get_h2h(home["id"], away["id"])

    if len(h2h) == 0:
        draw_rate = 0.0
        goals_avg = 3.0
        goal_diff = 2.0
        forced = True
    else:
        draws = 0
        goals = []
        diffs = []

        for m in h2h:
            gh = m["goals"]["home"]
            ga = m["goals"]["away"]
            if gh == ga:
                draws += 1
            goals.append(gh + ga)
            diffs.append(abs(gh - ga))

        draw_rate = draws / len(h2h)
        goals_avg = sum(goals) / len(goals)
        goal_diff = sum(diffs) / len(diffs)
        forced = False

    score = (
        draw_rate * WEIGHT_DRAW_RATE
        + (1 / (1 + goals_avg)) * WEIGHT_GOALS_AVG
        + (1 / (1 + goal_diff)) * WEIGHT_GOAL_DIFF
    )

    return {
        "score": score,
        "draw_rate": draw_rate,
        "goals_avg": goals_avg,
        "goal_diff": goal_diff,
        "home": home["name"],
        "away": away["name"],
        "league": fixture["league"]["name"],
        "country": fixture["league"]["country"],
        "datetime": fixture["fixture"]["date"],
        "forced": forced
    }

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    }, timeout=20)

def format_datetime_ecuador(utc_str):
    utc_dt = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
    ecu_dt = utc_dt + ECUADOR_OFFSET
    return ecu_dt.strftime("%Y-%m-%d %H:%M")

# =========================
# MAIN
# =========================
def main():
    fixtures = get_fixtures()
    analyzed = []

    for f in fixtures:
        try:
            analyzed.append(analyze_match(f))
        except:
            continue

    # FORZAR SIEMPRE 1 PARTIDO
    if len(analyzed) == 0 and len(fixtures) > 0:
        f = fixtures[0]
        analyzed.append({
            "score": 0.0,
            "draw_rate": 0.0,
            "goals_avg": 3.0,
            "goal_diff": 2.0,
            "home": f["teams"]["home"]["name"],
            "away": f["teams"]["away"]["name"],
            "league": f["league"]["name"],
            "country": f["league"]["country"],
            "datetime": f["fixture"]["date"],
            "forced": True
        })

    best = sorted(analyzed, key=lambda x: x["score"], reverse=True)[0]

    if best["forced"]:
        status = "⚠️ Partido forzado (pocos datos)"
    elif best["draw_rate"] >= 0.3:
        status = "APTO para empate"
    else:
        status = "NO ideal, pero mejor opción del día"

    msg = (
        f"⚽ <b>MEJOR PARTIDO PARA EMPATE</b>\n\n"
        f"🏆 {best['league']} ({best['country']})\n"
        f"👥 {best['home']} vs {best['away']}\n"
        f"🕒 {format_datetime_ecuador(best['datetime'])} (Ecuador)\n\n"
        f"📊 <b>Métricas</b>\n"
        f"• % Empates: {best['draw_rate']*100:.1f}%\n"
        f"• Goles promedio: {best['goals_avg']:.2f}\n"
        f"• Dif. goles: {best['goal_diff']:.2f}\n"
        f"• Score: {best['score']:.3f}\n\n"
        f"🧠 <b>Evaluación:</b> {status}"
    )

    send_telegram(msg)

if __name__ == "__main__":
    main()
