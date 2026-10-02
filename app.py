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
        ],
    }
    tip, odd, conf = random.choice(pools[cat_wanted])
    return tip, odd, cat_wanted, conf

def fetch_all_games_today():
    matches=[]; cid=1
    today = datetime.now(LAGOS_TZ).strftime("%Y-%m-%d")
    today_espn = datetime.now(LAGOS_TZ).strftime("%Y%m%d")
    raw_fixtures = []

    if API_KEY:
        try:
            headers={"x-apisports-key": API_KEY}
            url=f"https://v3.football.api-sports.io/fixtures?date={today}"
            r=requests.get(url,headers=headers,timeout=15).json()
            raw_fixtures = r.get("response",[])
            print(f"API returned {len(raw_fixtures)} games")
        except Exception as e:
            print("API error",e)

    if len(raw_fixtures) < 20:
        LEAGUES = {
            "uefa.nations": "UEFA Nations League", "fifa.worldq": "World Cup Qual",
            "uefa.champions":"Champions League","eng.1":"Premier League","esp.1":"La Liga",
            "ita.1":"Serie A","ger.1":"Bundesliga","fra.1":"Ligue 1","ned.1":"Eredivisie",
            "por.1":"Portugal","bra.1":"Brazil"
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
            except: continue

    # NO DUPLICATE LOGIC
    categories = ["free","over","double","btts","handicap"]
    seen_matches = set()

    for fix in raw_fixtures:
        try:
            home=fix["teams"]["home"]["name"]; away=fix["teams"]["away"]["name"]; league=fix["league"]["name"]
            key = f"{home} vs {away}"
            if key in seen_matches:
                continue
            seen_matches.add(key)

            dt_str=fix["fixture"]["date"]
            try:
                dt=datetime.fromisoformat(dt_str.replace("Z","+00:00")).astimezone(LAGOS_TZ)
                time_str=dt.strftime("%H:%M")
            except:
                time_str=f"{random.randint(16,21)}:00"

            cat = categories[len(matches) % len(categories)]
            tip,odd,cat_final,conf = get_tip_for_category(cat, home, away, league)
            matches.append({"id":cid,"league":league,"home":home,"away":away,"time":time_str,"tip":tip,"odd":odd,"cat":cat_final,"conf":conf})
            cid+=1
            if len(matches)>=50:
                break
        except: continue

    # VIP - top confidence
    vip=[]
    for m in sorted(matches, key=lambda x: x["conf"], reverse=True)[:5]:
        vip.append({"id":cid,"league":f"VIP {m['league']}","home":m["home"],"away":m["away"],"time":m["time"],"tip":m["tip"]+" 🔥","odd":str(round(float(m["odd"])+0.6,2)),"cat":"vip","conf":min(97,m["conf"]+5)}); cid+=1

    final = matches + vip
    with open(DB_FILE,"w") as f:
        json.dump({"updated":datetime.now(LAGOS_TZ).isoformat(),"matches":final},f)
    print(f"SAVED {len(final)} unique games")
    return final

def load_matches():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE) as f: return json.load(f).get("matches",[])
        except: pass
    return fetch_all_games_today()

def cards_html(data):
    if not data: return Markup("<p
