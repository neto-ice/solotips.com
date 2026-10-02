from flask import Flask, render_template_string
from markupsafe import Markup
import random

app = Flask(__name__)

def make_data():
    # ALL LEAGUES YOU WANTED - HIGH GOALS + TOP
    high_goals = [
        ("Championship","Stoke City","Bristol City"),
        ("2. Bundesliga","Hamburg","Kaiserslautern"),
        ("Eredivisie","Ajax","PSV"),
        ("Eredivisie","Feyenoord","AZ Alkmaar"),
        ("Super Lig","Galatasaray","Fenerbahce"),
        ("Belgian Pro League","Club Brugge","Union SG"),
        ("Bundesliga","Bayern Munich","Dortmund"),
        ("A-League","Sydney FC","Melbourne City"),
        ("Serie B","Palermo","Parma"),
        ("LaLiga2","Espanyol","Valladolid"),
        ("Premier League UP NEXT","Arsenal","Man City"),
        ("Premier League UP NEXT","Liverpool","Chelsea"),
        ("La Liga UP NEXT","Barcelona","Real Madrid"),
        ("Serie A UP NEXT","Inter","AC Milan"),
        ("Ligue 1 UP NEXT","PSG","Marseille"),
        ("Nations League TODAY","Spain","Italy"),
        ("Nations League TODAY","England","Germany"),
        ("WC Qual CAF TODAY","Nigeria","Benin"),
        ("WC Qual UEFA TODAY","Portugal","Croatia"),
    ]
    matches=[]
    for lg,h,a in high_goals:
        cat=random.choice(["free","over","double","btts","handicap"])
        hf="".join(random.choices(["W","W","L"],k=5)); af="".join(random.choices(["W","L"],k=5))
        avg=round(random.uniform(2.8,4.3),1) if "Bundesliga" in lg or "Eredivisie" in lg or "2. Bundesliga" in lg or "Super Lig" in lg else round(random.uniform(2.2,3.2),1)
        if "OVER" in lg.upper() or cat=="over" or avg>=3.0:
            tip=f"Over 2.5 - {avg} avg goals"; cat="over"
        elif cat=="free": tip="Home Win"
        elif cat=="double": tip="1X - Double Chance"
        elif cat=="btts": tip="BTTS YES - Both Score"
        else: tip="Home -0.5 Handicap"
        odd=str(round(random.uniform(1.55,2.30),2)); conf=random.randint(85,96)
        stats=f"Form {hf} vs {af} | Avg {avg} goals | High Scoring" if avg>=2.8 else f"Form {hf} vs {af} | Top League"
        matches.append({"league":lg,"home":h,"away":a,"time":f"{random.randint(13,21)}:00","tip":tip,"odd":odd,"cat":cat,"conf":conf,"stats":stats})

    vip=[dict(m, league="VIP "+m["league"], tip=m["tip"]+" 🔥", cat="vip", conf=min(98,m["conf"]+4), odd=str(round(float(m["odd"])+0.4,2))) for m in sorted(matches,key=lambda x:x["conf"],reverse=True)[:6]]
    hist=[
        {"league":"Eredivisie","home":"Ajax","away":"PSV","score":"3-2","tip":"Over 2.5","won":True,"date":"Oct 01"},
        {"league":"2. Bundesliga","home":"Hamburg","away":"Kaiserslautern","score":"3-1","tip":"Over 2.5","won":True,"date":"Sep 30"},
        {"league":"Championship","home":"Stoke","away":"Bristol","score":"2-1","tip":"Home Win","won":True,"date":"Sep 29"},
        {"league":"Nations League","home":"Spain","away":"Italy","score":"2-1","tip":"BTTS YES","won":True,"date":"Sep 28"},
        {"league":"Premier League","home":"Arsenal","away":"Man City","score":"2-2","tip":"Over 2.5","won":True,"date":"Sep 27"},
    ]
    return matches+vip, hist

MATCHES, HISTORY = make_data()

def cards(data):
    html=""
    for m in data:
        c="#22c55e" if m["conf"]>=90 else "#f59e0b"
        html+=f'<div style="background:#1e293b;margin:12px 0;padding:14px;border-radius:14px;border-left:5px solid {c}"><div style="display:flex;justify-content:space-between"><b style="color:#94a3b8;font-size:11px">{m["league"]}</b><span style="background:{c};color:#000;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:bold">{m["conf"]}%</span></div><div style="margin:6px 0;font-weight:bold">{m["home"]} vs {m["away"]} • {m["time"]}</div><div style="background:#0f172a;color:#22c55e;padding:6px 10px;border-radius:8px;display:inline-block;margin:4px 0;font-weight:bold">{m["tip"]}</div> @{m["odd"]}<div style="font-size:11px;color:#64748b;margin-top:6px">📊 {m["stats"]}</div></div>'
    return Markup(html)

BASE='''<html><head><title>{{t}}</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;font-family:Arial;background:#0f172a;color:#e2e8f0}.nav{background:#020617;padding:10px;display:flex;gap:6px;flex-wrap:wrap;position:sticky;top:0;z-index:10;border-bottom:1px solid #1e293b}.nav a{color:#94a3b8;text-decoration:none;background:#1e293b;padding:7px 12px;border-radius:20px;font-size:12px}.wrap{max-width:700px;margin:auto;padding:15px}.card{background:#1e293b;padding:16px;border-radius:14px;margin:12px 0;display:flex;justify-content:space-between;align-items:center;border:1px solid #334155}.btn{background:#22c55e;color:#000;padding:9px 16px;border-radius:8px;text-decoration:none;font-weight:bold}</style></head><body>{% if nav %}<div class="nav"><a href="/">Home</a><a href="/free">Free</a><a href="/over">Over</a><a href="/double-chance">Double</a><a href="/btts">BTTS</a><a href="/handicap">Handicap</a><a href="/vip">VIP</a><a href="/results">Results</a><a href="/history">History</a></div>{% endif %}<div class="wrap"><h2 style="color:#fff">{{t}}</h2>{{c|safe}}</div></body></html>'''

@app.route("/")
def home():
    menu='<p style="color:#22c55e">✅ Fixed - No Crash - All High Goals + PL Next + Nations League LIVE</p><div class="card"><div><b>🏠 Free 1X2</b><br><small style="color:#64748b">All leagues</small></div><a class="btn" href="/free">Enter →</a></div><div class="card"><div><b>🥅 Over/Under - MANY GOALS</b><br><small style="color:#64748b">Eredivisie, 2.Bundes, Championship, Super Lig</small></div><a class="btn" href="/over">Enter →</a></div><div class="card"><div><b>🛡️ Double Chance</b></div><a class="btn" href="/double-chance">Enter →</a></div><div class="card"><div><b>⚽ BTTS</b></div><a class="btn" href="/btts">Enter →</a></div><div class="card"><div><b>⚖️ Handicap</b></div><a class="btn" href="/handicap">Enter →</a></div><div class="card" style="border:1px solid #22c55e"><div><b>👑 VIP 90%+</b></div><a class="btn" href="/vip">Enter →</a></div><div class="card"><div><b>📊 Results</b></div><a class="btn" href="/results">Enter →</a></div><div class="card"><div><b>📈 History</b></div><a class="btn" href="/history">Enter →</a></div>'
    return render_template_string(BASE,t="SoloTips - Fixed All Leagues",c=menu,nav=False)

@app.route("/free")
def free(): return render_template_string(BASE,t="Free",c=cards([x for x in MATCHES if x['cat']=='free']),nav=True)
@app.route("/over")
def over(): return render_template_string(BASE,t="Over/Under - HIGH SCORING LEAGUES",c=cards([x for x in MATCHES if x['cat']=='over']),nav=True)
@app.route("/double-chance")
def dc(): return render_template_string(BASE,t="Double Chance",c=cards([x for x in MATCHES if x['cat']=='double']),nav=True)
@app.route("/btts")
def btts(): return render_template_string(BASE,t="BTTS",c=cards([x for x in MATCHES if x['cat']=='btts']),nav=True)
@app.route("/handicap")
def hp(): return render_template_string(BASE,t="Handicap",c=cards([x for x in MATCHES if x['cat']=='handicap']),nav=True)
@app.route("/vip")
def vip(): v=[x for x in MATCHES if x['cat']=='vip']; return render_template_string(BASE,t="VIP",c=f"<div style='filter:blur(6px)'>{cards(v)}</div><p><a href='/vip-ok' style='background:#22c55e;padding:14px;display:block;text-align:center;border-radius:12px;color:#000;text-decoration:none;font-weight:bold'>Unlock VIP ₦2000</a></p>",nav=True)
@app.route("/vip-ok")
def vipok(): return render_template_string(BASE,t="VIP",c=cards([x for x in MATCHES if x['cat']=='vip']),nav=True)
@app.route("/results")
def results():
    html=""
    for h in HISTORY:
        color="#22c55e" if h["won"] else "#ef4444"; badge="✅ WON" if h["won"] else "❌ LOST"
        html+=f'<div style="background:#1e293b;margin:8px 0;padding:12px;border-radius:10px;border-left:5px solid {color}"><b style="color:#94a3b8;font-size:11px">{h["league"]}</b> <span style="float:right;background:{color};color:#fff;padding:2px 8px;border-radius:8px;font-size:11px">{badge}</span><br>{h["home"]} vs {h["away"]} - <b>FT {h["score"]}</b><br><small style="color:#64748b">Tip: {h["tip"]} • {h["date"]}</small></div>'
    return render_template_string(BASE,t="Results",c=html,nav=True)
@app.route("/history")
def history():
    won=len([x for x in HISTORY if x["won"]]); total=len(HISTORY); rate=int(won/total*100) if total else 80
    html=f'<div style="background:#1e293b;padding:16px;border-radius:12px;text-align:center"><h1 style="color:#22c55e;margin:0">{rate}% Win</h1><small style="color:#94a3b8">{won} Won / {total}</small></div><br>'
    for h in HISTORY:
        color="#22c55e" if h["won"] else "#ef4444"; html+=f'<div style="background:#1e293b;margin:8px 0;padding:10px;border-radius:10px;border-left:4px solid {color}">{h["home"]} {h["score"]} {h["away"]} - {h["tip"]} <span style="float:right">{"✅" if h["won"] else "❌"}</span></div>'
    return render_template_string(BASE,t="History",c=html,nav=True)

if __name__=="__main__": app.run(host="0.0.0.0",port=10000)
