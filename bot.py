# bot.py
# BOT DE ALERTA DIARIA – MEJOR PARTIDO PARA EMPATE
# API-Football (FREE) + Telegram
# Siempre envía AL MENOS 1 partido (el mejor disponible)

import requests
import os
from datetime import datetime, timedelta, timezone

# =========================
# VARIABLES (NO CAMBIAR NOMBRES)
# =========================
API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# =========================
# CONFIGURACIÓN
# =========================
API_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

# Zona horaria Ecuador (UTC-5)
ECUADOR_TZ = timezone(timedelta(hours=-5))

# Criterios base (ajustables)
MIN_MATCHES_HISTORY = 5   # mínimo de partidos históricos para analizar
WEIGHT_DRAW_RATE = 0.5
WEIGHT_GOALS_AVG = 0.3
WEIGHT_GOAL_DIFF = 0.2

# =========================
# FUNCIONES
# =========================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    requests.post(url, data=payload, timeout=20)

def get_fixtures(date_str):
    params = {"date": date_str, "status": "NS"}
    r = requests.get(f"{API_URL}/fixtures", headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("response", [])

def get_h2h(home_id, away_id):
    params = {"h2h": f"{home_id}-{away_id}", "last": 10}
    r = requests.get(f"{API_URL}/fixtures", headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("response", [])

def analyze_match(fixture):
    teams = fixture["teams"]
    home = teams["home"]
    away = teams["away"]

    h2h = get_h2h(home["id"], away["id"])
    if len(h2h) < MIN_MATCHES_HISTORY:
        return None

    draws = 0
    goals = []
    goal_diffs = []

    for m in h2h:
        g_home = m["goals"]["home"]
        g_away = m["goals"]["away"]
        if g_home == g_away:
            draws += 1
        goals.append(g_home + g_away)
        goal_diffs.append(abs(g_home - g_away))

    draw_rate = draws / len(h2h)
    goals_avg = sum(goals) / len(goals)
    goal_diff = sum(goal_diffs) / len(goal_diffs)

    # Score de empate (más alto = mejor)
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
    }

# =========================
# MAIN
# =========================
def main():
    today = datetime.utcnow().date()
    dates_to_check = [today, today + timedelta(days=1)]

    candidates = []

    for d in dates_to_check:
        fixtures = get_fixtures(d.isoformat())
        for f in fixtures:
            try:
                analysis = analyze_match(f)
                if analysis:
                    candidates.append(analysis)
            except Exception:
                continue

        if candidates:
            break  # ya hay partidos, no buscar más días

    if not candidates:
        send_telegram("⚠️ No se pudo analizar ningún partido (datos insuficientes).")
        return

    # Elegir el MEJOR partido del día
    best = sorted(candidates, key=lambda x: x["score"], reverse=True)[0]

    # Hora Ecuador
    dt_utc = datetime.fromisoformat(best["datetime"].replace("Z", "+00:00"))
    dt_ec = dt_utc.astimezone(ECUADOR_TZ)
    hora_ec = dt_ec.strftime("%d/%m %H:%M")

    apto = "APTO para empate" if best["draw_rate"] >= 0.3 else "NO ideal, pero mejor opción del día"

    msg = (
        f"⚽ <b>MEJOR PARTIDO PARA EMPATE</b>\n\n"
        f"🏆 {best['league']} ({best['country']})\n"
        f"👥 {best['home']} vs {best['away']}\n"
        f"⏰ {hora_ec} (Ecuador)\n\n"
        f"📊 <b>Métricas</b>\n"
        f"• % Empates H2H: {best['draw_rate']*100:.1f}%\n"
        f"• Prom. goles: {best['goals_avg']:.2f}\n"
        f"• Dif. goles: {best['goal_diff']:.2f}\n"
        f"• Score empate: {best['score']:.3f}\n\n"
        f"✅ <b>{apto}</b>\n"
        f"ℹ️ Odds NO consideradas"
    )

    send_telegram(msg)

if __name__ == "__main__":
    main()
