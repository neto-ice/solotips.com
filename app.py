from flask import Flask, render_template_string
from markupsafe import Markup
from datetime import datetime
import os, json, requests, random

app = Flask(__name__)
DB_FILE = "matches.json"
API_KEY = os.getenv("API_FOOTBALL_KEY")

def get_tip(cat):
    pools = {
        "free": ["Home Win (1)","Away Win (2)","Draw (X)","1 - Home Win","2 - Away Win"],
        "over": ["Over 1.5","Over 2.5","Under 3.5","Under 4.5","Over 0.5"],
        "double": ["1X Double Chance","X2 Double Chance","12 - No Draw"],
        "btts": ["BTTS YES","BTTS NO","Home to Score"],
        "handicap": ["Home -1 Handicap","Away +1 Handicap","Home +1","Asian Handicap 0.0"]
    }
    return random.choice(pools[cat]), str(round(random.uniform(1.3,2.8),2)), random.randint(80,94)

def fetch_games():
    matches=[]; cid=1
    raw=[]
    today = datetime.now().strftime("%Y-%m-%d")
    today2 = datetime.now().strftime("%Y%m%d")

    # Try API-Football
    if API_KEY:
        try:
            r=requests.get(f"https://v3.football.api-sports.io/fixtures?date={today}", headers={"x-apisports-key":API_KEY}, timeout=10).json()
            raw=r.get("response",[])
        except: pass

    # ESPN backup - all leagues
    if len(raw)<15:
        for code,name in {"uefa.nations":"Nations League","eng.1":"Premier","esp.1":"La Liga","ita.1":"Serie A","ger.1":"Bundesliga","fra.1":"Ligue 1","fifa.worldq":"World Qual"}.items():
            try:
                url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard?dates={today2}"
                d=requests.get(url,timeout=5).json()
                for ev in d.get("events",[])[:6]:
                    comp=ev["competitions"][0]; cs=comp["competitors"]
                    if len(cs)<2: continue
                    h=cs[0]["team"]["displayName"] if cs[0].get("homeAway")=="home" else cs[1]["team"]["displayName"]
                    a=cs[1]["team"]["displayName"] if cs[0].get("homeAway")=="home" else cs[0]["team"]["displayName"]
                    raw.append({"teams":{"home":{"name":h},"away":{"name":a}},"league":{"name":name},"fixture":{"date":ev.get("date","")}})
            except: continue

    seen=set(); cats=["free","over","double","btts","handicap"]
    for f in raw:
        try:
            home=f["teams"]["home"]["name"]; away=f["teams"]["away"]["name"]; league=f["league"]["name"]
            key=home+"-"+away
            if key in seen: continue
            seen.add(key)
            cat=cats[len(matches)%5]
            tip,odd,conf=get_tip(cat)
            matches.append({"id":cid,"league":league,"home":home,"away":away,"time":f"{random.randint(14,21)}:{random.choice(['00','30','45'])}","tip":tip,"odd":odd,"cat":cat,"conf":conf})
            cid+=1
            if len(matches)>=50: break
        except: continue

    vip=[]
    for m in sorted(matches,key=lambda x:x["conf"],reverse=True)[:5]:
        vip.append({"id":cid,"league":"VIP "+m["league"],"home":m["home"],"away":m["away"],"time":m["time"],"tip":m["tip"]+" 🔥","odd":str(round(float(m["odd"])+0.5,2)),"cat":"vip","conf":min(97,m["conf"]+4)}); cid+=1

    final=matches+vip
    with open(DB_FILE,"w") as f: json.dump({"matches":final},f)
    return final

def load():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE) as f: return json.load(f).get("matches",[])
        except: pass
    return fetch_games()

def cards(data):
    if not data: return Markup("<p style='text-align:center'>No games</p>")
    h=""
    for m in data:
        c="#22c55e" if m["conf"]>=88 else "#f59e0b"
        h+=f'<div style="background:#fff;margin:10px 0;padding:12px;border-radius:12px;border-left:5px solid {c}"><b>{m["league"]}</b> <span style="float:right;background:{c};padding:2px 8px;border-radius:10px;font-size:11px">{m["conf"]}%</span><br><b>{m["home"]} vs {m["away"]} • {m["time"]}</b><br><span style="background:#0f172a;color:#22c55e;padding:5px 10px;border-radius:6px;display:inline-block;margin-top:6px">{m["tip"]}</span> @{m["odd"]}</div>'
    return Markup(h)

BASE="""<html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;font-family:Arial;background:#f1f5f9}.nav{background:#0f172a;padding:10px;display:flex;gap:5px;flex-wrap:wrap;position:sticky;top:0}.nav a{color:#fff;text-decoration:none;background:#1e293b;padding:7px 10px;border-radius:15px;font-size:11px}.wrap{max-width:700px;margin:auto;padding:15px}</style></head><body><div class="nav"><a href="/">Home</a><a href="/free">Free</a><a href="/over">Over</a><a href="/double-chance">Double</a><a href="/btts">BTTS</a><a href="/handicap">Handicap</a><a href="/vip">VIP</a></div><div class="wrap"><h3>{{t}}</h3>{{c}}</div></body></html>"""

@app.route("/")
def home(): return render_template_string(BASE,t="50 Unique Games - No Duplicates",c=cards([x for x in load() if x['cat']!='vip']))
@app.route("/free")
def free(): return render_template_string(BASE,t="Free 1X2",c=cards([x for x in load() if x['cat']=='free']))
@app.route("/over")
def over(): return render_template_string(BASE,t="Over / Under",c=cards([x for x in load() if x['cat']=='over']))
@app.route("/double-chance")
def dc(): return render_template_string(BASE,t="Double Chance",c=cards([x for x in load() if x['cat']=='double']))
@app.route("/btts")
def btts(): return render_template_string(BASE,t="BTTS",c=cards([x for x in load() if x['cat']=='btts']))
@app.route("/handicap")
def hp(): return render_template_string(BASE,t="Handicap",c=cards([x for x in load() if x['cat']=='handicap']))
@app.route("/vip")
def vip(): v=[x for x in load() if x['cat']=='vip']; return render_template_string(BASE,t="VIP",c=Markup(f"<div style='filter:blur(5px)'>{cards(v)}</div><p><a href='/vip-ok' style='background:#22c55e;padding:12px;display:block;text-align:center;border-radius:10px;color:#000;text-decoration:none;font-weight:bold'>Unlock VIP ₦2000</a></p>"))
@app.route("/vip-ok")
def vipok(): return render_template_string(BASE,t="VIP Unlocked",c=cards([x for x in load() if x['cat']=='vip']))
@app.route("/force-update")
def fu(): d=fetch_games(); return f"Updated {len(d)} UNIQUE games! No duplicates. <a href='/'>Home</a>"

if __name__=="__main__": app.run(host="0.0.0.0",port=10000)
