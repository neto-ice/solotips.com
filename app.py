from flask import Flask, render_template_string
from datetime import datetime, date
import random, requests

app = Flask(__name__)

# Fallback if API fails
FALLBACK = [
    {"match": "Arsenal vs Crystal Palace", "league": "Premier League", "time": "19:45"},
    {"match": "Barcelona vs Getafe", "league": "La Liga", "time": "20:00"},
    {"match": "Bayern Munich vs Union Berlin", "league": "Bundesliga", "time": "19:30"},
    {"match": "Inter Milan vs Torino", "league": "Serie A", "time": "19:45"},
    {"match": "PSG vs Rennes", "league": "Ligue 1", "time": "20:00"},
    {"match": "Ajax vs Feyenoord", "league": "Eredivisie", "time": "19:00"},
]

TIP_TYPES = [
    ("BTTS YES", "1.65", "BTTS"),
    ("Over 2.5 Goals", "1.75", "Goals"),
    ("Over 1.5 Goals", "1.35", "Goals"),
    ("Home Win", "1.85", "1X2"),
    ("BTTS NO", "1.90", "BTTS"),
    ("Double Chance 1X", "1.30", "Double"),
    ("Under 2.5", "1.80", "Goals"),
]

def get_live_fixtures():
    today_str = date.today().strftime("%Y-%m-%d")
    try:
        # Free API - Today's matches
        url = f"https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={today_str}&s=Soccer"
        r = requests.get(url, timeout=5).json()
        events = r.get('events') or []
        matches = []
        for e in events[:20]: # Take 20 real matches
            matches.append({
                "match": f"{e['strHomeTeam']} vs {e['strAwayTeam']}",
                "league": e['strLeague'],
                "time": e['strTime'][:5] if e.get('strTime') else "19:45"
            })
        if matches:
            return matches
    except:
        pass
    return FALLBACK

def make_tips():
    random.seed(date.today().isoformat())
    fixtures = get_live_fixtures()
    tips = []
    for f in fixtures:
        tip, odd, market = random.choice(TIP_TYPES)
        conf = random.randint(68, 89)
        tips.append({**f, "tip": tip, "odd": odd, "market": market, "conf": f"{conf}%"})
    return tips

HTML = """
<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SoloTips - Live Today's Matches</title>
<style>
body{margin:0;background:#080c1a;color:#fff;font-family:system-ui}
.header{background:#10162f;padding:18px;text-align:center;position:sticky;top:0;z-index:10}
.header h1{margin:0;font-size:24px}
.header p{color:#22c55e;margin:5px 0 0}
.container{padding:12px;max-width:600px;margin:auto}
.card{background:#151c35;border-radius:14px;padding:14px;margin:12px 0;display:flex;justify-content:space-between;align-items:center;border:1px solid #1e274a}
.left{flex:1}
.league{font-size:11px;color:#8a94b5;text-transform:uppercase}
.match{font-weight:700;margin:4px 0;font-size:16px}
.meta{font-size:12px;color:#8a94b5}
.right{text-align:right}
.odd{background:#22c55e;color:#000;font-weight:800;padding:6px 12px;border-radius:20px;display:inline-block}
.tip{margin-top:6px;font-size:13px;background:#1e274a;padding:4px 8px;border-radius:6px;display:inline-block}
.btts{color:#60a5fa} .goals{color:#4ade80} .x2{color:#facc15}
.live-dot{display:inline-block;width:8px;height:8px;background:#ef4444;border-radius:50%;margin-right:5px;animation:blink 1s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}
</style>
</head><body>
<div class="header">
<h1>⚽ SoloTips.com</h1>
<p><span class="live-dot"></span>LIVE - {{ today }} - {{ count }} Matches Today</p>
</div>
<div class="container">
{% for t in tips %}
<div class="card">
<div class="left">
<div class="league">{{ t.league }} • {{ t.time }}</div>
<div class="match">{{ t.match }}</div>
<div class="tip">👉 {{ t.tip }} <span style="color:#888">| Conf: {{ t.conf }}</span></div>
</div>
<div class="right">
<div class="odd">{{ t.odd }}</div>
<div class="meta" style="margin-top:6px">{{ t.market }}</div>
</div>
</div>
{% endfor %}
</div>
</body></html>
"""

@app.route('/')
def home():
    tips = make_tips()
    return render_template_string(HTML, tips=tips, today=datetime.now().strftime("%A %d %B %Y"), count=len(tips))

if __name__ == '__main__':
    app.run()
