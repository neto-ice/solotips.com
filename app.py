from flask import Flask, render_template_string
from datetime import datetime
app = Flask(__name__)

MATCHES = [
    {"league": "Premier League", "home": "Chelsea", "away": "Man United", "time": "15:00", "tip": "Home Win (1)", "odd": "2.10", "cat": "free"},
    {"league": "La Liga", "home": "Sevilla", "away": "Valencia", "time": "17:00", "tip": "Draw (X)", "odd": "3.20", "cat": "free"},
    {"league": "Serie A", "home": "Napoli", "away": "Lazio", "time": "19:00", "tip": "Away Win (2)", "odd": "2.45", "cat": "free"},
    {"league": "Eredivisie", "home": "Ajax", "away": "PSV", "time": "18:30", "tip": "Over 1.5", "odd": "1.30", "cat": "free"},
    {"league": "Premier League", "home": "Man City", "away": "Arsenal", "time": "15:00", "tip": "Over 2.5 Goals", "odd": "1.85", "cat": "over"},
    {"league": "La Liga", "home": "Barcelona", "away": "Real Madrid", "time": "20:00", "tip": "Over 3.5 Goals", "odd": "2.60", "cat": "over"},
    {"league": "Serie A", "home": "Inter", "away": "AC Milan", "time": "19:45", "tip": "Over 1.5 Goals", "odd": "1.35", "cat": "over"},
    {"league": "Bundesliga", "home": "Bayern", "away": "Dortmund", "time": "17:30", "tip": "Over 2.5 + BTTS", "odd": "2.10", "cat": "over"},
    {"league": "Premier League", "home": "Liverpool", "away": "Tottenham", "time": "14:00", "tip": "1X (Home or Draw)", "odd": "1.30", "cat": "double"},
    {"league": "Championship", "home": "Leeds", "away": "Sunderland", "time": "15:30", "tip": "X2 (Draw or Away)", "odd": "1.55", "cat": "double"},
    {"league": "Serie A", "home": "Juventus", "away": "Roma", "time": "18:00", "tip": "12 (Home or Away)", "odd": "1.28", "cat": "double"},
    {"league": "Bundesliga", "home": "Dortmund", "away": "Stuttgart", "time": "15:30", "tip": "X2 Double Chance", "odd": "1.60", "cat": "double"},
    {"league": "Premier League", "home": "Brighton", "away": "Brentford", "time": "15:00", "tip": "BTTS YES", "odd": "1.72", "cat": "btts"},
    {"league": "La Liga", "home": "Real Betis", "away": "Ath Bilbao", "time": "18:30", "tip": "BTTS YES", "odd": "1.80", "cat": "btts"},
    {"league": "Serie A", "home": "Atalanta", "away": "Fiorentina", "time": "20:45", "tip": "BTTS YES + Over 2.5", "odd": "2.05", "cat": "btts"},
    {"league": "Ligue 1", "home": "Lille", "away": "Lyon", "time": "19:00", "tip": "BTTS YES", "odd": "1.65", "cat": "btts"},
    {"league": "VIP", "home": "Man City", "away": "Arsenal", "time": "21:00", "tip": "2 & Over 1.5", "odd": "3.40", "cat": "vip"},
    {"league": "VIP", "home": "PSG", "away": "Marseille", "time": "20:45", "tip": "BTTS YES + Over 2.5", "odd": "2.90", "cat": "vip"},
    {"league": "VIP", "home": "Barcelona", "away": "Bayern", "time": "21:00", "tip": "Over 3.5 + BTTS", "odd": "4.20", "cat": "vip"},
]

TEMPLATE = """
<!DOCTYPE html>
<html><head><title>{{title}} - Solotips</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{margin:0;font-family:Arial, sans-serif;background:#f1f5f9;color:#0f172a}
.nav{background:#0f172a;padding:10px;display:flex;gap:6px;flex-wrap:wrap;position:sticky;top:0;z-index:10}
.nav a{color:#fff;text-decoration:none;background:#1e293b;padding:9px 14px;border-radius:20px;font-size:13px;font-weight:bold}
.nav a.active{background:#22c55e;color:#000}
.wrap{max-width:700px;margin:auto;padding:15px}
.card{background:#fff;margin:10px 0;padding:14px;border-radius:12px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 1px 3px rgba(0,0,0,0.1);border-left:4px solid #22c55e}
.badge{background:#0f172a;color:#22c55e;padding:6px 12px;border-radius:6px;font-weight:bold;font-size:13px}
.btn{background:#22c55e;color:#000;padding:14px 24px;border-radius:10px;text-decoration:none;font-weight:bold;display:block;text-align:center;margin:20px 0;border:none;width:100%;font-size:16px}
.small{color:#64748b;font-size:12px}
h2{color:#0f172a}
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
<div class="wrap">
<h2>{{title}}</h2>
<p class="small">Updated: """+datetime.now().strftime("%d %b %Y")+"</p>
{{content|safe}}
</div>
<script>
function pay(){
 var h=PaystackPop.setup({key:'pk_test_xxx',email:prompt('Email for VIP access:'),amount:200000,currency:'NGN',
 callback:function(r){location.href='/vip-ok';}, onClose:function(){}}); h.openIframe();
}
</script>
</body></html>
"""

def render_list(data):
    html=""
    for m in data:
        html+=f"<div class='card'><div><b>{m['league']}</b><br>{m['home']} vs {m['away']}<br><span class='small'>{m['time']} • {m['cat'].upper()}</span></div><div style='text-align:right'><span class='badge'>{m['tip']}</span><br><span class='small'>@{m['odd']}</span></div></div>"
    return html

@app.route("/")
def home():
    c="<h3>🔥 Today Best</h3>"+render_list(MATCHES[:4])+"<a class='btn' href='/vip'>Unlock VIP Tips - ₦2000</a>"
    return render_template_string(TEMPLATE, title="Home", content=c)
@app.route("/free")
def free(): return render_template_string(TEMPLATE, title="Free Tips", content=render_list([m for m in MATCHES if m['cat']=='free']))
@app.route("/over")
def over(): return render_template_string(TEMPLATE, title="Over Goals", content=render_list([m for m in MATCHES if m['cat']=='over']))
@app.route("/double-chance")
def dbl(): return render_template_string(TEMPLATE, title="Double Chance", content=render_list([m for m in MATCHES if m['cat']=='double']))
@app.route("/btts")
def btts(): return render_template_string(TEMPLATE, title="BTTS Tips", content=render_list([m for m in MATCHES if m['cat']=='btts']))
@app.route("/vip")
def vip():
    c="<div style='filter:blur(5px);pointer-events:none'>"+render_list([m for m in MATCHES if m['cat']=='vip'])+"</div><h3>VIP - 5 High Odds</h3><p>Pay to unlock today VIP games. 90% win rate.</p><button class='btn' onclick='pay()'>Pay ₦2000 with Paystack</button>"
    return render_template_string(TEMPLATE, title="VIP", content=c)
@app.route("/vip-ok")
def vipok(): return render_template_string(TEMPLATE, title="VIP Unlocked", content="<h3 style='color:green'>✅ Payment Success</h3>"+render_list([m for m in MATCHES if m['cat']=='vip']))
@app.route("/policy")
def pol(): return render_template_string(TEMPLATE, title="Policy", content="<p>18+ Gamble responsibly. Tips are for information only, no guarantee.</p>")

if __name__=="__main__":
    app.run(host="0.0.0.0", port=10000)
