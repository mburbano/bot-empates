
import os
import requests
from datetime import datetime, timedelta

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
HEADERS = {"x-apisports-key": API_KEY}

# Pesos del score (empate)
W_DRAW = 0.55
W_GOALS = 0.25
W_DIFF  = 0.20

# Umbral de “buena calidad” (no bloquea, solo etiqueta)
QUALITY_THRESHOLD = 0.45

# Ecuador UTC-5
ECUADOR_OFFSET = timedelta(hours=-5)

# =========================
# HELPERS
# =========================
def api_get(endpoint, params):
    r = requests.get(f"{API_URL}/{endpoint}", headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("response", [])

def get_fixtures_next_days(days=7):
    start = datetime.utcnow().date()
    end = start + timedelta(days=days)
    return api_get("fixtures", {
        "from": start.isoformat(),
        "to": end.isoformat(),
        "status": "NS"
    })

def get_h2h(home_id, away_id, last=10):
    try:
        return api_get("fixtures/headtohead", {
            "h2h": f"{home_id}-{away_id}",
            "last": last
        })
    except:
        return []

def analyze_fixture(fx):
    home = fx["teams"]["home"]
    away = fx["teams"]["away"]

    h2h = get_h2h(home["id"], away["id"], last=10)

    # Métricas reales; si no hay H2H suficientes, se penaliza (no se fuerza)
    if len(h2h) >= 5:
        draws = 0
        goals_sum = 0
        diffs = 0

        for m in h2h:
            gh, ga = m["goals"]["home"], m["goals"]["away"]
            if gh == ga:
                draws += 1
            goals_sum += gh + ga
            diffs += abs(gh - ga)

        draw_rate = draws / len(h2h)
        goals_avg = goals_sum / len(h2h)
        goal_diff = diffs / len(h2h)
        data_quality = "OK"
    else:
        # Penalización por pocos datos (NO forzar)
        draw_rate = 0.10
        goals_avg = 3.2
        goal_diff = 2.2
        data_quality = "BAJA"

    score = (
        draw_rate * W_DRAW
        + (1 / (1 + goals_avg)) * W_GOALS
        + (1 / (1 + goal_diff)) * W_DIFF
    )

    return {
        "score": score,
        "draw_rate": draw_rate,
        "goals_avg": goals_avg,
        "goal_diff": goal_diff,
        "quality": data_quality,
        "home": home["name"],
        "away": away["name"],
        "league": fx["league"]["name"],
        "country": fx["league"]["country"],
        "datetime": fx["fixture"]["date"]
    }

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }, timeout=20)

def to_ecuador(utc_iso):
    dt = datetime.fromisoformat(utc_iso.replace("Z", "+00:00"))
    return (dt + ECUADOR_OFFSET).strftime("%Y-%m-%d %H:%M")

# =========================
# MAIN
# =========================
def main():
    fixtures = get_fixtures_next_days(days=7)

    # Si la API devuelve algo (normalmente siempre), se analiza TODO
    analyzed = []
    for fx in fixtures:
        try:
            analyzed.append(analyze_fixture(fx))
        except:
            continue

    # Si por algún motivo extremo no hubo análisis válidos,
    # NO inventamos partidos: tomamos el mejor score calculado disponible.
    if not analyzed:
        send_telegram(
            "⚠️ <b>Sin análisis válido hoy</b>\n"
            "La API respondió sin datos analizables.\n"
            "El bot reintenta automáticamente."
        )
        return

    best = max(analyzed, key=lambda x: x["score"])

    status = (
        "APTO para empate"
        if best["score"] >= QUALITY_THRESHOLD and best["quality"] == "OK"
        else "MEJOR OPCIÓN DISPONIBLE (confianza moderada)"
    )

    msg = (
        f"⚽ <b>MEJOR PARTIDO PARA EMPATE</b>\n\n"
        f"🏆 {best['league']} ({best['country']})\n"
        f"👥 {best['home']} vs {best['away']}\n"
        f"🕒 {to_ecuador(best['datetime'])} (Ecuador)\n\n"
        f"📊 <b>Métricas</b>\n"
        f"• % Empates (H2H): {best['draw_rate']*100:.1f}%\n"
        f"• Goles promedio: {best['goals_avg']:.2f}\n"
        f"• Dif. goles: {best['goal_diff']:.2f}\n"
        f"• Score: {best['score']:.3f}\n"
        f"• Datos: {best['quality']}\n\n"
        f"🧠 <b>Evaluación:</b> {status}"
    )

    send_telegram(msg)

if __name__ == "__main__":
    main()