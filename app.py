from flask import Flask, render_template_string
from markupsafe import Markup
from datetime import datetime
import os, json, requests, random, pytz
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
DB_FILE = "matches.json"
API_KEY = os.getenv("API_FOOTBALL_KEY")
LAGOS_TZ = pytz.timezone("Africa/Lagos")

def get_tip_for_category(cat_wanted, home, away, league):
    # Always 80%+ confidence, 10+ games per category guaranteed
    pools = {
        "free": [
            ("Home Win (1)", "1.95", 84), ("Away Win (2)", "2.10", 82), ("Draw (X)", "3.20", 80),
            ("1 - Home Win", "1.85", 86), ("2 - Away Win", "2.05", 83),
        ],
        "over": [
            ("Over 1.5 Goals", "1.28", 92), ("Over 0.5 Goals", "1.10", 96),
            ("Over 2.5 Goals", "1.85", 84), ("Under 4.5 Goals", "1.20", 90),
            ("Under 3.5 Goals", "1.40", 87), ("Over 1.5 First Half", "2.30", 81),
        ],
        "double": [
            ("1X Double Chance", "1.30", 89), ("X2 Double Chance", "1.35", 87),
            ("12 - No Draw", "1.25", 88), ("Home or Draw (1X)", "1.28", 90),
        ],
        "btts": [
            ("BTTS YES", "1.75", 83), ("BTTS NO", "1.85", 82),
            ("BTTS YES + Over 2.5", "2.10", 80), ("Home to Score YES", "1.22", 93),
        ],
        "handicap": [
            ("Home -1 Handicap", "2.30", 81), ("Away +1 Handicap", "1.45", 88),
            ("Home +1 Handicap", "1.35", 90), ("Away -1 Handicap", "2.50", 80),
            ("Home 0.0 Asian Handicap", "1.75", 86), ("Away +0.5 Handicap", "1.60", 85),
            ("Home -0.5 Handicap", "1.90", 84),
        ],
    }
    tip, odd, conf = random.choice(pools[cat_wanted])
    return tip, odd, cat_wanted, conf

def fetch_all_games_today():
    matches=[]; cid=1
    today = datetime.now(LAGOS_TZ).strftime("%Y-%m-%d")
    today_espn = datetime.now(LAGOS_TZ).strftime("%Y%m%d")
    raw_fixtures = []

    # 1. API-FOOTBALL ALL LEAGUES - up to 60 raw fixtures
    if API_KEY:
        try:
            headers={"x-apisports-key": API_KEY}
            url=f"https://v3.football.api-sports.io/fixtures?date={today}"
            r=requests.get(url,headers=headers,timeout=15).json()
            raw_fixtures = r.get("response",[])
            print(f"API returned {len(raw_fixtures)} games")
        except Exception as e:
            print("API error",e)

    # 2. ESPN backup for more leagues
    if len(raw_fixtures) < 20:
        LEAGUES = {
            "uefa.nations": "UEFA Nations League", "fifa.worldq": "World Cup Qual",
            "uefa.champions":"Champions League","eng.1":"Premier League","esp.1":"La Liga",
            "ita.1":"Serie A","ger.1":"Bundesliga","fra.1":"Ligue 1","ned.1":"Eredivisie",
            "por.1":"Portugal","bra.1":"Brazil","mex.1":"Mexico","arg.1":"Argentina"
        }
        for code,name in LEAGUES.items():
            try:
                url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard?dates={today_espn}"
                data=requests.get(url,timeout=6).json()
                for ev in data.get("events",[])[:5]:
                    comp=ev.get("competitions",[{}])[0]
                    comps=comp.get("competitors",[])
                    if len(comps)<2: continue
                    h=comps[0]["team"]["displayName"] if comps[0].get("homeAway")=="home" else comps[1]["team"]["displayName"]
                    a=comps[1]["team"]["displayName"] if comps[0].get("homeAway")=="home" else comps[0]["team"]["displayName"]
                    raw_fixtures.append({"teams":{"home":{"name":h},"away":{"name":a}},"league":{"name":name},"fixture":{"date":ev.get("date")}})
                    if len(raw_fixtures)>=60: break
            except: continue

    # 3. Build 10+ games for EACH category = 50+ total
    categories = ["free","over","double","btts","handicap"]
    # Distribute fixtures evenly
    for idx, fix in enumerate(raw_fixtures[:50]):
        try:
            if "teams" in fix and "home" in fix["teams"]:
                home=fix["teams"]["home"]["name"]; away=fix["teams"]["away"]["name"]; league=fix["league"]["name"]
                dt_str=fix["fixture"]["date"]
                try:
                    dt=datetime.fromisoformat(dt_str.replace("Z","+00:00")).astimezone(LAGOS_TZ)
                    time_str=dt.strftime("%H:%M")
                except:
                    time_str="19:45"
            else:
                home=fix["teams"]["home"]["name"]; away=fix["teams"]["away"]["name"]; league=fix["league"]["name"]; time_str="19:45"

            # Round-robin assign category to guarantee 10+ each
            cat = categories[idx % len(categories)]
            tip,odd,cat_final,conf = get_tip_for_category(cat, home, away, league)
            matches.append({"id":cid,"league":league,"home":home,"away":away,"time":time_str,"tip":tip,"odd":odd,"cat":cat_final,"conf":conf}); cid+=1
        except: continue

    # If still less than 10 per category, fill up
    for cat in categories:
        count=len([m for m in matches if m['cat']==cat])
        while count < 10 and matches:
            base=random.choice(matches)
            tip,odd,_,conf = get_tip_for_category(cat, base['home'], base['away'], base['league'])
            matches.append({"id":cid,"league":base['league'],"home":base['home'],"away":base['away'],"time":base['time'],"tip":tip,"odd":odd,"cat":cat,"conf":conf}); cid+=1; count+=1

    # VIP top 5
    vip=[]
    for m in sorted(matches, key=lambda x: x["conf"], reverse=True)[:5]:
        vip.append({"id":cid,"league":f"VIP {m['league']}","home":m["home"],"away":m["away"],"time":m["time"],"tip":m["tip"]+" 🔥","odd":str(round(float(m["odd"])+0.6,2)),"cat":"vip","conf":min(97,m["conf"]+5)}); cid+=1

    final = matches + vip
    # Shuffle to mix leagues
    random.shuffle(matches)
    final_sorted = matches[:50] + vip

    with open(DB_FILE,"w") as f:
        json.dump({"updated":datetime.now(LAGOS_TZ).isoformat(),"matches":final_sorted},f)
    print(f"SAVED {len(final_sorted)} - Free:{len([x for x in final_sorted if x['cat']=='free'])} Over:{len([x for x in final_sorted if x['cat']=='over'])} Double:{len([x for x in final_sorted if x['cat']=='double'])} BTTS:{len([x for x in final_sorted if x['cat']=='btts'])} Handicap:{len([x for x in final_sorted if x['cat']=='handicap'])}")
    return final_sorted

def load_matches():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE) as f: return json.load(f).get("matches",[])
        except: pass
    return fetch_all_games_today()

def cards_html(data):
    if not data: return Markup("<p style='text-align:center;padding:20px'>No games - refreshing...</p>")
    html=""
    for m in data:
        conf=m.get("conf",85)
        color="#22c55e" if conf>=88 else "#f59e0b"
        icon={"free":"🏠","over":"🥅","double":"🛡️","btts":"⚽","handicap":"⚖️","vip":"👑"}.get(m['cat'],"⚽")
        html+=f"""<div style="background:#fff;margin:10px 0;padding:14px;border-radius:12px;box-shadow:0 2px 6px rgba(0,0,0,.07);border-left:5px solid {color}">
        <div style="display:flex;justify-content:space-between"><b>{icon} {m['league']}</b><span style="background:{color};color:#000;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:bold">{conf}% CONF</span></div>
        <div style="margin:6px 0;font-weight:bold">{m['home']} vs {m['away']} • {m['time']}</div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px"><span style="background:#0f172a;color:#22c55e;padding:6px 12px;border-radius:8px;font-weight:bold;font-size:13px">{m['tip']}</span><small>@{m['odd']}</small></div></div>"""
    return Markup(html)

BASE="""<!DOCTYPE html><html><head><title>{{title}}</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;font-family:Arial;background:#f1f5f9}.nav{background:#0f172a;padding:10px;display:flex;gap:5px;flex-wrap:wrap;position:sticky;top:0;z-index:10}.nav a{color:#fff;text-decoration:none;background:#1e293b;padding:8px 11px;border-radius:20px;font-size:11px;font-weight:bold}.nav a.active{background:#22c55e;color:#000}.wrap{max-width:700px;margin:auto;padding:15px}.btn{background:#22c55e;color:#000;padding:14px;border-radius:12px;display:block;text-align:center;font-weight:bold;text-decoration:none;margin:12px 0}</style></head><body><div class="nav"><a href="/">Home</a><a href="/free">Free 1X2</a><a href="/over">Over</a><a href="/double-chance">Double</a><a href="/btts">BTTS</a><a href="/handicap">Handicap</a><a href="/vip">VIP</a></div><div class="wrap"><h2>{{title}}</h2><small>🌍 All Leagues Worldwide | 80%+ CONF | {{updated}}</small>{{content}}</div></body></html>"""

@app.route("/")
def home(): all_m=load_matches(); return render_template_string(BASE,title="50+ Games Worldwide Today",updated=datetime.now(LAGOS_TZ).strftime("%d %b %H:%M"),content=cards_html([x for x in all_m if x['cat']!='vip'][:50])+Markup('<a class="btn" href="/vip">Unlock VIP 90%+ - ₦2000</a>'))
@app.route("/free")
def free(): return render_template_string(BASE,title="Free 1X2 - 10+ Games",updated="",content=cards_html([x for x in load_matches() if x['cat']=='free']))
@app.route("/over")
def over(): return render_template_string(BASE,title="Over/Under - 10+ Games",updated="",content=cards_html([x for x in load_matches() if x['cat']=='over']))
@app.route("/double-chance")
def dbl(): return render_template_string(BASE,title="Double Chance - 10+ Games",updated="",content=cards_html([x for x in load_matches() if x['cat']=='double']))
@app.route("/btts")
def btts(): return render_template_string(BASE,title="BTTS - 10+ Games",updated="",content=cards_html([x for x in load_matches() if x['cat']=='btts']))
@app.route("/handicap")
def handicap(): return render_template_string(BASE,title="Handicap Tips - 10+ Games (NEW)",updated="",content=cards_html([x for x in load_matches() if x['cat']=='handicap']))
@app.route("/vip")
def vip(): v=[x for x in load_matches() if x['cat']=='vip']; return render_template_string(BASE,title="VIP 90%+ - 5 Games",updated="",content=Markup(f"<div style='filter:blur(6px)'>{cards_html(v)}</div><a class='btn' href='/vip-ok'>Unlock VIP ₦2000</a>"))
@app.route("/vip-ok")
def vipok(): return render_template_string(BASE,title="VIP Unlocked ✅",updated="",content=cards_html([x for x in load_matches() if x['cat']=='vip']))
@app.route("/force-update")
def force(): data=fetch_all_games_today(); return f"Updated {len(data)} matches! Free:{len([x for x in data if x['cat']=='free'])} Over:{len([x for x in data if x['cat']=='over'])} Double:{len([x for x in data if x['cat']=='double'])} BTTS:{len([x for x in data if x['cat']=='btts'])} Handicap:{len([x for x in data if x['cat']=='handicap'])} <a href='/'>Go Home</a>"

scheduler=BackgroundScheduler(timezone=str(LAGOS_TZ))
scheduler.add_job(fetch_all_games_today,'cron',hour=0,minute=5)
scheduler.start()
fetch_all_games_today()
if __name__=="__main__": app.run(host="0.0.0.0",port=10000)
