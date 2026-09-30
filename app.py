from flask import Flask, render_template_string
from datetime import datetime
app = Flask(__name__)

# --- 25 MATCHES, GROUPED BY PAGE ---
MATCHES = [
    # FREE PAGE - 5 matches
    {"league": "Premier League", "home": "Chelsea", "away": "Man United", "time": "15:00", "tip": "Home Win (1)", "odd": "2.10", "cat": "free"},
    {"league": "La Liga", "home": "Sevilla", "away": "Valencia", "time": "17:00", "tip": "Draw (X)", "odd": "3.20", "cat": "free"},
    {"league": "Serie A", "home": "Napoli", "away": "Lazio", "time": "19:00", "tip": "Away Win (2)", "odd": "2.45", "cat": "free"},
    {"league": "Bundesliga", "home": "Leipzig", "away": "Frankfurt", "time": "16:30", "tip": "1X", "odd": "1.40", "cat": "free"},
    {"league": "Eredivisie", "home": "Ajax", "away": "PSV", "time": "18:30", "tip": "Over 1.5", "odd": "1.30", "cat": "free"},

    # OVER PAGE - 5 matches ONLY OVER
    {"league": "Premier League", "home": "Man City", "away": "Arsenal", "time": "15:00", "tip": "Over 2.5 Goals", "odd": "1.85", "cat": "over"},
    {"league": "La Liga", "home": "Barcelona", "away": "Real Madrid", "time": "20:00", "tip": "Over 3.5 Goals", "odd": "2.60", "cat": "over"},
    {"league": "Serie A", "home": "Inter", "away": "AC Milan", "time": "19:45", "tip": "Over 1.5 Goals", "odd": "1.35", "cat": "over"},
    {"league": "Bundesliga", "home": "Bayern", "away": "Dortmund", "time": "17:30", "tip": "Over 2.5 + BTTS", "odd": "2.10", "cat": "over"},
    {"league": "Ligue 1", "home": "PSG", "away": "Marseille", "time": "20:45", "tip": "Over 2.5", "odd": "1.70", "cat": "over"},

    # DOUBLE CHANCE PAGE - 5 matches ONLY DOUBLE
    {"league": "Premier League", "home": "Liverpool", "away": "Tottenham", "time": "14:00", "tip": "1X (Home or Draw)", "odd": "1.30", "cat": "double"},
    {"league": "Championship", "home": "Leeds", "away": "Sunderland", "time": "15:30", "tip": "X2 (Draw or Away)", "odd": "1.55", "cat": "double"},
    {"league": "Serie A", "home": "Juventus", "away": "Roma", "time": "18:00", "tip": "12 (Home or Away)", "odd": "1.28", "cat": "double"},
    {"league": "La Liga", "home": "Atletico", "away": "Villarreal", "time": "16:00", "tip": "1X Double Chance", "odd": "1.25", "cat": "double"},
    {"league": "Bundesliga", "home": "Dortmund", "away": "Stuttgart", "time": "15:30", "tip": "X2 Double Chance", "odd": "1.60", "cat": "double"},

    # BTTS PAGE - 5 matches ONLY BTTS
    {"league": "Premier League", "home": "Brighton", "away": "Brentford", "time": "15:00", "tip": "BTTS YES", "odd": "1.72", "cat": "btts"},
    {"league": "La Liga", "home": "Real Betis", "away": "Ath Bilbao", "time": "18:30", "tip": "BTTS YES", "odd": "1.80", "cat": "btts"},
    {"league": "Serie A", "home": "Atalanta", "away": "Fiorentina", "time": "20:45", "tip": "BTTS YES + Over 2.5", "odd": "2.05", "cat": "btts"},
    {"league": "EPL", "home": "West Ham", "away": "Newcastle", "time": "16:00", "tip": "BTTS NO", "odd": "2.15", "cat": "btts"},
    {"league": "Ligue 1", "home": "Lille", "away": "Lyon", "time": "19:00", "tip": "BTTS YES", "odd": "1.65", "cat": "btts"},

    # VIP PAGE - 5 matches ONLY VIP - HIGH ODDS
    {"league": "VIP 🔒", "home": "Man City", "away": "Arsenal", "time": "21:00", "tip": "2 & Over 1.5", "odd": "3.40", "cat": "vip"},
    {"league": "VIP 🔒", "home": "PSG", "away": "Marseille", "time": "20:45", "tip": "BTTS YES + Over 2.5", "odd": "2.90", "cat": "vip"},
    {"league": "VIP 🔒", "home": "Barcelona", "away": "Bayern", "time": "21:00", "tip": "Over 3.5 + BTTS", "odd": "4.20", "cat": "vip"},
    {"league": "VIP 🔒", "home": "Liverpool", "away": "Chelsea", "time": "19:30", "tip": "Home Win + BTTS", "odd": "3.10", "cat": "vip"},
    {"league": "VIP 🔒", "home": "Real Madrid", "away": "Inter", "time": "21:00", "tip": "Correct Score 2-1", "odd": "8.50", "cat": "vip"},
]

HTML = """
<!DOCTYPE html><html><head><title>Solotips - {{title}}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{font-family:Arial;background:#0f172a;color:#fff;margin:0}
.nav{background:#1e293b;padding:10px;display:flex;gap:6px;flex-wrap:wrap;position:sticky;top:0}
.nav a{color:#fff;text-decoration:none;background:#334155;padding:8px 10px;border-radius:6px;font-size:12px}
.nav a.active{background:#22c55e;color:#000}
.card{background:#1e293b;margin:10px 0;padding:14px;border-radius:10px;display:flex;justify-content:space-between;align-items:center}
.badge{background:#22c55e;color:#000;padding:5px 10px;border-radius:5px;font-weight:bold;font-size:12px}
.btn{background:#22c55e;color:#000;padding:12px 20px;border-radius:8px;text-decoration:none;font-weight:bold;display:inline-block;border:none;cursor:pointer}
.lock{filter:blur(6px)}
</style>
<script src="https://js.paystack.co/v1/inline.js"></script>
</head><body>
<div class="nav">
<a href="/" class="{{'active' if title=='Home' else ''}}">Home</a>
<a href="/free" class="{{'active' if title=='Free Tips' else ''}}">Free</a>
<a href="/over" class="{{'active' if title=='Over Goals' else ''}}">Over</a>
<a href="/double-chance" class="{{'active' if title=='Double Chance' else ''}}">Double</a>
<a href="/btts" class="{{'active' if title=='BTTS Tips' else ''}}">BTTS</a>
<a href="/vip" class="{{'active' if title=='VIP' else ''}}">VIP 🔒</a>
</div>
<div style="padding:15px;max-width:800px;margin:auto">
<h2>{{title}} - """+datetime.now().strftime("%d %b")+"""</h2>
{{content}}
</div>
<script>
function pay(){
 var h=PaystackPop.setup({key:'pk_test_xxxxxxxx',email:prompt('Enter email:'),amount:200000,currency:'NGN',
 callback:function(r){alert('Paid! '+r.reference); location.href='/vip-ok';},
 onClose:function(){}}); h.openIframe();
}
</script>
</body></html>
"""

def show(data, blur=False):
    s=""
    for m in data:
        badge = f"<span class='badge {'lock' if blur else ''}'>{m['tip']}</span>" if not blur else "<span class='badge lock'>LOCKED - PAY</span>"
        # blur for vip page
        if blur:
            s+=f"<div class='card'><div><b>{m['league']}</b><br>{m['home']} vs {m['away']}<br><small>{m['time']}</small></div><div>{badge}<br><small>@{m['odd']}</small></div></div>"
        else:
            s+=f"<div class='card'><div><b>{m['league']}</b><br>{m['home']} vs {m['away']} - {m['time']}</div><div>{badge}<br>@{m['odd']}</div></div>"
    return s

@app.route("/")
def home():
    c="<h3>Today Best 3</h3>"+show(MATCHES[:3])+"<br><a class='btn' href='/vip'>Unlock VIP ₦2000</a>"
    return render_template_string(HTML, title="Home", content=c)
@app.route("/free")
def free(): return render_template_string(HTML, title="Free Tips", content=show([m for m in MATCHES if m
