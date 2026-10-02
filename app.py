from flask import Flask, render_template_string
from markupsafe import Markup
import requests, random, datetime

app = Flask(__name__)

LEAGUES = {
    "Championship": "eng.2",
    "2. Bundesliga": "ger.2",
    "Eredivisie": "ned.1",
    "Super Lig": "tur.1",
    "Belgian Pro League": "bel.1",
    "Bundesliga": "ger.1",
    "Premier League": "eng.1",
    "Nations League": "uefa.nations",
}

def get_today_matches():
    today = datetime.date.today()
    date_str = today.strftime("%Y%m%d")
    pretty_date = today.strftime("%B %d, %Y")
    matches = []
    for name, lid in LEAGUES.items():
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lid}/scoreboard?dates={date_str}"
            r = requests.get(url, timeout=3)
            if r.status_code!= 200: continue
            data = r.json()
            for ev in data.get("events", [])[:2]:
                comp = ev.get("competitions", [{}])[0]
                teams = comp.get("competitors", [])
                if len(teams) < 2: continue
                home = teams[0]['team']['displayName'] if teams[0]['homeAway']=='home' else teams[1]['team']['displayName']
                away = teams[1]['team']['displayName'] if teams[0]['homeAway']=='home' else teams[0]['team']['displayName']
                try: t = ev['date'][11:16]
                except: t = f"{random.randint(15,20)}:00"
                matches.append({
                    "league": f"{name} - TODAY {pretty_date}",
                    "home": home, "away": away, "time": t,
                    "tip": "Over 2.5 - Many Goals TODAY", "odd": str(round(random.uniform(1.65,2.25),2)),
                    "cat": "over", "conf": random.randint(85,95),
                    "stats": f"Live TODAY | {pretty_date} | Auto 12 AM"
                })
        except: continue

    if len(matches) < 4:
        backup = [("Championship","Stoke","Bristol"),("2. Bundesliga","Hamburg","Kaiserslautern"),("Eredivisie","Ajax","PSV"),("Super Lig","Galatasaray","Fenerbahce"),("Nations League","Spain","Italy"),("Premier League","Arsenal","Man City")]
        for lg,h,a in backup:
            matches.append({"league": f"{lg} - TODAY {pretty_date}","home": h,"away": a,"time": f"{random.randint(15,20)}:00","tip": "Over 2.5 - Many Goals TODAY","odd": "1.85","cat": "over","conf": 89,"stats": f"Updated Daily {pretty_date} - Auto 12 AM"})
    return matches

# NO FETCH AT STARTUP - This fixes deploy failed
MATCHES_CACHE = []
LAST_UPDATE = datetime.datetime.min

def get_matches():
    global MATCHES_CACHE, LAST_UPDATE
    today = datetime.date.today()
    # Update if empty or date changed
    if not MATCHES_CACHE or LAST_UPDATE.date()!= today:
        try:
            MATCHES_CACHE = get_today_matches()
            LAST_UPDATE = datetime.datetime.now()
        except:
            # fallback if ESPN fails - never crash
            pretty = today.strftime("%B %d, %Y")
            MATCHES_CACHE = [{"league": f"Championship - TODAY {pretty}","home": "Stoke City","away": "Bristol City","time": "19:00","tip": "Over 2.5 TODAY","odd": "1.85","cat": "over","conf": 89,"stats": f"TODAY {pretty}"}]
    return MATCHES_CACHE

def cards(data):
    html=""
    for m in data:
        c="#22c55e" if m["conf"]>=90 else "#f59e0b"
        html+=f'<div style="background:#1e293b;margin:12px 0;padding:14px;border-radius:14px;border-left:5px solid {c}"><div style="display:flex;justify-content:space-between"><b style="color:#94a3b8;font-size:11px">{m["league"]}</b><span style="background:{c};color:#000;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:bold">{m["conf"]}%</span></div><div style="margin:6px 0;font-weight:bold">{m["home"]} vs {m["away"]} • {m["time"]}</div><div style="background:#0f172a;color:#22c55e;padding:6px 10px;border-radius:8px;display:inline-block;margin:4px 0;font-weight:bold">{m["tip"]}</div> @{m["odd"]}<div style="font-size:11px;color:#64748b;margin-top:6px">📊 {m["stats"]}</div></div>'
    return Markup(html)

BASE='''<html><head><title>{{t}}</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;font-family:Arial;background:#0f172a;color:#e2e8f0}.nav{background:#020617;padding:10px;display:flex;gap:6px;flex-wrap:wrap;position:sticky;top:0;z-index:10;border-bottom:1px solid #1e293b}.nav a{color:#94a3b8;text-decoration:none;background:#1e293b;padding:7px 12px;border-radius:20px;font-size:12px}.wrap{max-width:700px;margin:auto;padding:15px}.card{background:#1e293b;padding:16px;border-radius:14px;margin:12px 0;display:flex;justify-content:space-between;align-items:center;border:1px solid #334155}.btn{background:#22c55e;color:#000;padding:9px 16px;border-radius:8px;text-decoration:none;font-weight:bold}</style></head><body>{% if nav %}<div class="nav"><a href="/">Home</a><a href="/free">Free</a><a href="/over">Over</a><a href="/double-chance">Double</a><a href="/btts">BTTS</a><a href="/handicap">Handicap</a><a href="/vip">VIP</a><a href="/results">Results</a><a href="/history">History</a></div>{% endif %}<div class="wrap"><h2 style="color:#fff">{{t}}</h2>{{c|safe}}</div></body></html>'''

@app.route("/")
def home():
    m=get_matches(); today_str=datetime.date.today().strftime("%B %d, %Y")
    menu=f'<p style="color:#22c55e">✅ Live TODAY {today_str} - Auto 12 AM Update - {len(m)} games</p><div class="card"><div><b>🏠 Free TODAY</b></div><a class="btn" href="/free">Enter →</a></div><div class="card"><div><b>🥅 Over TODAY - Many Goals</b></div><a class="btn" href="/over">Enter →</a></div><div class="card"><div><b>🛡️ Double Chance TODAY</b></div><a class="btn" href="/double-chance">Enter →</a></div><div class="card"><div><b>⚽ BTTS TODAY</b></div><a class="btn" href="/btts">Enter →</a></div><div class="card"><div><b>👑 VIP TODAY</b></div><a class="btn" href="/vip">Enter →</a></div>'
    return render_template_string(BASE,t=f"SoloTips TODAY {today_str}",c=menu,nav=False)

@app.route("/free")
def free(): return render_template_string(BASE,t=f"Free TODAY {datetime.date.today()}",c=cards(get_matches()),nav=True)
@app.route("/over")
def over(): return render_template_string(BASE,t=f"Over TODAY {datetime.date.today()}",c=cards(get_matches()),nav=True)
@app.route("/double-chance")
def dc(): return render_template_string(BASE,t=f"Double TODAY {datetime.date.today()}",c=cards(get_matches()),nav=True)
@app.route("/btts")
def btts(): return render_template_string(BASE,t=f"BTTS TODAY {datetime.date.today()}",c=cards(get_matches()),nav=True)
@app.route("/handicap")
def hp(): return render_template_string(BASE,t=f"Handicap TODAY {datetime.date.today()}",c=cards(get_matches()),nav=True)
@app.route("/vip")
def vip(): m=get_matches(); return render_template_string(BASE,t="VIP TODAY",c=f"<div style='filter:blur(6px)'>{cards(m[:6])}</div><p><a href='/vip-ok' style='background:#22c55e;padding:14px;display:block;text-align:center;border-radius:12px;color:#000;text-decoration:none;font-weight:bold'>Unlock VIP</a></p>",nav=True)
@app.route("/vip-ok")
def vipok(): return render_template_string(BASE,t="VIP TODAY",c=cards(get_matches()),nav=True)
@app.route("/results")
def results(): return render_template_string(BASE,t=f"Results {datetime.date.today()}",c=Markup("<div style='background:#1e293b;padding:12px;border-radius:10px'>✅ TODAY games loaded - check Over page</div>"),nav=True)
@app.route("/history")
def history(): return render_template_string(BASE,t="History",c=Markup(f"<h1 style='color:#22c55e'>Win Today {datetime.date.today()}</h1>"),nav=True)
@app.route("/force-update")
def fu():
    global MATCHES_CACHE, LAST_UPDATE
    MATCHES_CACHE=get_today_matches(); LAST_UPDATE=datetime.datetime.now()
    return f"Updated {datetime.date.today()} - {len(MATCHES_CACHE)} games - <a href='/'>Home</a>"

if __name__=="__main__": app.run(host="0.0.0.0",port=10000)
