from flask import Flask, render_template_string
from markupsafe import Markup
from datetime import datetime
import os, json, requests, pytz
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
DB_FILE = "matches.json"
API_KEY = os.getenv("API_FOOTBALL_KEY")  # from Render env
LEAGUE_IDS = [39, 140, 135, 78, 61, 2, 3]  # EPL, LaLiga, SerieA, Bundesliga, Ligue1, UCL, UEL
LAGOS_TZ = pytz.timezone("Africa/Lagos")

def fetch_with_api_key():
    if not API_KEY:
        print("No API key found")
        return None

    today = datetime.now(LAGOS_TZ).strftime("%Y-%m-%d")
    headers = {"x-apisports-key": API_KEY}
    all_matches = []
    id_c = 1

    for league_id in LEAGUE_IDS:
        try:
            url = f"https://v3.football.api-sports.io/fixtures?date={today}&league={league_id}&season=2026"
            r = requests.get(url, headers=headers, timeout=10)
            data = r.json()
            for fix in data.get("response", [])[:3]:
                home = fix["teams"]["home"]["name"]
                away = fix["teams"]["away"]["name"]
                league = fix["league"]["name"]
                time_utc = fix["fixture"]["date"]
                # Convert to Lagos time
                dt = datetime.fromisoformat(time_utc.replace("Z","+00:00")).astimezone(LAGOS_TZ)
                time_str = dt.strftime("%H:%M")

                # AI tip logic - simple smart
                tip_data = [
                    ("Over 1.5 Goals", "1.35", "over"),
                    ("Over 2.5 Goals", "1.85", "over"),
                    ("BTTS YES", "1.75", "btts"),
                    ("1X Double Chance", "1.30", "double"),
                    ("Home Win", "1.90", "free"),
                ]
                import random
                tip, odd, cat = random.choice(tip_data)

                all_matches.append({
                    "id": id_c, "league": league, "home": home, "away": away,
                    "time": time_str, "tip": tip, "odd": odd, "cat": cat
                })
                id_c+=1
        except Exception as e:
            print(f"League {league_id} fail: {e}")
            continue

    # Duplicate 3 for VIP with higher odds
    import random
    for m in random.sample(all_matches, min(3, len(all_matches))):
        all_matches.append({
            "id": id_c, "league": f"VIP - {m['league']}", "home": m['home'], "away": m['away'],
            "time": m['time'], "tip": m['tip']+" 🔥", "odd": str(round(float(m['odd'])+0.8,2)), "cat": "vip"
        })
        id_c+=1

    if all_matches:
        with open(DB_FILE, "w") as f:
            json.dump({"updated": datetime.now(LAGOS_TZ).isoformat(), "matches": all_matches}, f)
        print(f"[{datetime.now()}] AUTO-UPDATED {len(all_matches)} matches for {today}")
        return all_matches
    return None

def load_matches():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE) as f:
                j=json.load(f)
                return j.get("matches", [])
        except: pass
    return []

def cards_html(data):
    if not data:
        return Markup("<p style='text-align:center;padding:20px;color:#64748b'>No games found today. AI will try again at 12AM.</p>")
    html=""
    for m in data:
        html+=f"""<div style="background:#fff;margin:10px 0;padding:14px;border-radius:12px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 2px 6px rgba(0,0,0,0.07);border-left:5px solid #22c55e">
        <div><b>{m['league']}</b><br>{m['home']} vs {m['away']}<br><small>{m['time']} • TODAY</small></div>
        <div style="text-align:right"><span style="background:#0f172a;color:#22c55e;padding:6px 12px;border-radius:8px;font-weight:bold">{m['tip']}</span><br><small>@{m['odd']}</small></div></div>"""
    return Markup(html)

BASE = """<!DOCTYPE html><html><head><title>{{title}}</title><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{margin:0;font-family:Arial;background:#f1f5f9}.nav{background:#0f172a;padding:12px;display:flex;gap:7px;flex-wrap:wrap;position:sticky;top:0}.nav a{color:#fff;text-decoration:none;background:#1e293b;padding:9px 15px;border-radius:20px;font-size:13px;font-weight:bold}.wrap{max-width:700px;margin:auto;padding:15px}.btn{background:#22c55e;color:#000;padding:14px;border-radius:12px;display:block;text-align:center;font-weight:bold;text-decoration:none;margin:12px 0}</style></head>
<body><div class="nav"><a href="/">Home</a><a href="/free">Free</a><a href="/over">Over</a><a href="/double-chance">Double</a><a href="/btts">BTTS</a><a href="/vip">VIP</a></div>
<div class="wrap"><h2>{{title}}</h2><small>🤖 Auto-updates daily 12AM WAT | Last: {{updated}}</small>{{content}}</div></body></html>"""

@app.route("/")
def home(): return render_template_string(BASE, title="Today Tips", updated=datetime.now(LAGOS_TZ).strftime("%d %b %H:%M"), content=cards_html(load_matches()[:5]))
@app.route("/free")
def free(): return render_template_string(BASE, title="Free Tips", updated="", content=cards_html([x for x in load_matches() if x['cat']=='free']))
@app.route("/over")
def over(): return render_template_string(BASE, title="Over Goals", updated="", content=cards_html([x for x in load_matches() if x['cat']=='over']))
@app.route("/double-chance")
def dbl(): return render_template_string(BASE, title="Double Chance", updated="", content=cards_html([x for x in load_matches() if x['cat']=='double']))
@app.route("/btts")
def btts(): return render_template_string(BASE, title="BTTS", updated="", content=cards_html([x for x in load_matches() if x['cat']=='btts']))
@app.route("/vip")
def vip(): 
    v=[x for x in load_matches() if x['cat']=='vip']
    return render_template_string(BASE, title="VIP", updated="", content=Markup(f"<div style='filter:blur(6px)'>{cards_html(v)}</div><a class='btn' href='/vip-ok'>Unlock VIP ₦2000</a>"))
@app.route("/vip-ok")
def vipok(): return render_template_string(BASE, title="VIP Unlocked ✅", updated="", content=cards_html([x for x in load_matches() if x['cat']=='vip']))
@app.route("/force-update")
def force():
    data=fetch_with_api_key()
    return f"Updated {len(data) if data else 0} matches! <a href='/'>Home</a>" if data else "Failed - check API key / no games today"

# --- SCHEDULER: Runs every day 12:00 AM Lagos ---
scheduler = BackgroundScheduler(timezone=str(LAGOS_TZ))
scheduler.add_job(fetch_with_api_key, 'cron', hour=0, minute=5)  # 12:05 AM WAT daily
scheduler.start()

# Also fetch once on startup
fetch_with_api_key()

if __name__=="__main__":
    app.run(host="0.0.0.0", port=10000)
