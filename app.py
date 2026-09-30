from flask import Flask, render_template_string
from markupsafe import Markup
from datetime import datetime
app = Flask(__name__)

MATCHES = [
    {"league": "Premier League", "home": "Chelsea", "away": "Man United", "time": "15:00", "tip": "Home Win", "odd": "2.10", "cat": "free"},
    {"league": "La Liga", "home": "Sevilla", "away": "Valencia", "time": "17:00", "tip": "Draw", "odd": "3.20", "cat": "free"},
    {"league": "Bundesliga", "home": "Leipzig", "away": "Frankfurt", "time": "16:30", "tip": "1X", "odd": "1.40", "cat": "free"},
    {"league": "Premier League", "home": "Man City", "away": "Arsenal", "time": "15:00", "tip": "Over 2.5 Goals", "odd": "1.85", "cat": "over"},
    {"league": "La Liga", "home": "Barcelona", "away": "Real Madrid", "time": "20:00", "tip": "Over 3.5 Goals", "odd": "2.60", "cat": "over"},
    {"league": "Bundesliga", "home": "Bayern", "away": "Dortmund", "time": "17:30", "tip": "Over 2.5 + BTTS", "odd": "2.10", "cat": "over"},
    {"league": "Premier League", "home": "Liverpool", "away": "Tottenham", "time": "14:00", "tip": "1X Double Chance", "odd": "1.30", "cat": "double"},
    {"league": "Championship", "home": "Leeds", "away": "Sunderland", "time": "15:30", "tip": "X2 Double Chance", "odd": "1.55", "cat": "double"},
    {"league": "Serie A", "home": "Juventus", "away": "Roma", "time": "18:00", "tip": "12 (Home/Away)", "odd": "1.28", "cat": "double"},
    {"league": "Premier League", "home": "Brighton", "away": "Brentford", "time": "15:00", "tip": "BTTS YES", "odd": "1.72", "cat": "btts"},
    {"league": "La Liga", "home": "Real Betis", "away": "Ath Bilbao", "time": "18:30", "tip": "BTTS YES", "odd": "1.80", "cat": "btts"},
    {"league": "Serie A", "home": "Atalanta", "away": "Fiorentina", "time": "20:45", "tip": "BTTS YES + Over", "odd": "2.05", "cat": "btts"},
    {"league": "VIP", "home": "Man City", "away": "Arsenal", "time": "21:00", "tip": "2 & Over 1.5", "odd": "3.40", "cat": "vip"},
    {"league": "VIP", "home": "PSG", "away": "Marseille", "time": "20:45", "tip": "BTTS + Over 2.5", "odd": "2.90", "cat": "vip"},
]

def cards_html(data):
    html = ""
    for m in data:
        html += f"""
        <div style="background:#ffffff;margin:10px 0;padding:14px;border-radius:12px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 2px 6px rgba(0,0,0,0.07);border-left:5px solid #22c55e">
            <div><b>{m['league']}</b><br>{m['home']} vs {m['away']}<br><small style="color:#64748b">{m['time']}</small></div>
            <div style="text-align:right"><span style="background:#0f172a;color:#22c55e;padding:6px 12px;border-radius:8px;font-weight:bold;font-size:13px">{m['tip']}</span><br><small style="color:#64748b">@{m['odd']}</small></div>
        </div>"""
    return Markup(html)

TEMPLATE = """
<!DOCTYPE html>
<html><head><title>Solotips - {{title}}</title><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{margin:0;font-family:Arial;background:#f1f5f9;color:#0f172a}
.nav{background:#0f172a;padding:12px;display:flex;gap:7px;flex-wrap:wrap;position:sticky;top:0}
.nav a{color:#fff;text-decoration:none;background:#1e293b;padding:9px 15px;border-radius:20px;font-size:13px;font-weight:bold}
.nav a.active{background:#22c55e;color:#000}
.wrap{max-width:700px;margin:auto;padding:15px}
.btn{background:#22c55e;color:#000;padding:15px;border-radius:12px;display:block;text-align:center;font-weight:bold;text-decoration:none;margin:20px 0;font-size:16px}
</style></head><body>
<div class="nav"><a href="/">Home</a><a href="/free">Free</a><a href="/over">Over</a><a href="/double-chance">Double</a><a href="/btts">BTTS</a><a href="/vip">VIP 🔒</a></div>
<div class="wrap"><h2>{{title}}</h2><p style="color:#64748b;font-size:12px">Updated: {{date}}</p>{{cards}}</div>
</body></html>
"""

@app.route("/")
def home():
    return render_template_string(TEMPLATE, title="Today Best Tips", date=datetime.now().strftime("%d %b %Y"), cards=cards_html(MATCHES[:3]) + Markup('<a class="btn" href="/vip">Unlock VIP Tips - ₦2000</a>'))
@app.route("/free")
def free(): return render_template_string(TEMPLATE, title="Free Tips", date=datetime.now().strftime("%d %b"), cards=cards_html([m for m in MATCHES if m['cat']=='free']))
@app.route("/over")
def over(): return render_template_string(TEMPLATE, title="Over Goals - Different Tips", date=datetime.now().strftime("%d %b"), cards=cards_html([m for m in MATCHES if m['cat']=='over']))
@app.route("/double-chance")
def dbl(): return render_template_string(TEMPLATE, title="Double Chance - Different Tips", date=datetime.now().strftime("%d %b"), cards=cards_html([m for m in MATCHES if m['cat']=='double']))
@app.route("/btts")
def btts(): return render_template_string(TEMPLATE, title="BTTS Tips - Different Tips", date=datetime.now().strftime("%d %b"), cards=cards_html([m for m in MATCHES if m['cat']=='btts']))
@app.route("/vip")
def vip():
    locked = Markup(f"<div style='filter:blur(5px)'>{cards_html([m for m in MATCHES if m['cat']=='vip'])}</div><a class='btn' href='/vip-ok'>Pay ₦2000 to Unlock</a>")
    return render_template_string(TEMPLATE, title="VIP Locked", date="", cards=locked)
@app.route("/vip-ok")
def vipok(): return render_template_string(TEMPLATE, title="VIP Unlocked ✅", date="", cards=cards_html([m for m in MATCHES if m['cat']=='vip']))

if __name__=="__main__":
    app.run(host="0.0.0.0", port=10000)
