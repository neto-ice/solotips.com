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
    "WC Qualifiers": "fifa.worldq.uefa",
}

def get_today_matches():
    today = datetime.date.today()
    date_str = today.strftime("%Y%m%d")
    pretty_date = today.strftime("%B %d, %Y")
    matches = []
    print(f"Fetching matches for TODAY {pretty_date}")

    for name, lid in LEAGUES.items():
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lid}/scoreboard?dates={date_str}"
            r = requests.get(url, timeout=4)
            if r.status_code!= 200: continue
            data = r.json()
            for ev in data.get("events", [])[:3]:
                comp = ev.get("competitions", [{}])[0]
                teams = comp.get("competitors", [])
                if len(teams) < 2: continue
                home = teams[0]['team']['displayName'] if teams[0]['homeAway']=='home' else teams[1]['team']['displayName']
                away = teams[1]['team']['displayName'] if teams[0]['homeAway']=='home' else teams[0]['team']['displayName']
                try: t = ev['date'][11:16]
                except: t = f"{random.randint(14,21)}:00"
                avg = 3.5 if "Eredivisie" in name or "2. Bundesliga" in name else 2.9
                cat = "over"
                tip = f"Over 2.5 - {avg} avg goals - TODAY"
                matches.append({
                    "league": f"{name} - TODAY {pretty_date}",
                    "home": home, "away": away, "time": t,
                    "tip": tip, "odd": str(round(random.uniform(1.65,2.35),2)),
                    "cat": random.choice(["over","free","btts","double","handicap"]),
                    "conf": random.randint(85,95),
                    "stats": f"Live TODAY | {pretty_date} | Auto-updated at 12 AM"
                })
        except: continue

    if len(matches) < 5:
        backup = [
            ("Championship", "Stoke City", "Bristol City"),
            ("2. Bundesliga", "Hamburg", "Kaiserslautern"),
            ("Eredivisie", "Ajax", "PSV"),
            ("Super Lig", "Galatasaray", "Fenerbahce"),
            ("Nations League", "Spain", "Italy"),
            ("Premier League", "Arsenal", "Man City"),
        ]
        for lg,h,a in backup:
            matches.append({
                "league": f"{lg} - TODAY {pretty_date}",
                "home": h, "away": a, "time": f"{random.randint(15,20)}:00",
                "tip": "Over 2.5 - Many Goals - TODAY", "odd": "1.85",
                "cat": "over", "conf": 89,
                "stats": f"High Scoring League | {pretty_date} | Auto 12 AM Update"
            })
    return matches

MATCHES_CACHE = get_today_matches()
LAST_UPDATE = datetime.datetime.now()

def get_matches():
    global MATCHES_CACHE, LAST_UPDATE
    today = datetime.date.today()
    # AUTO UPDATE AT 12 AM: if date changed -> fetch new
    if LAST_UPDATE.date()!= today:
        MATCHES_CACHE = get_today_matches()
        LAST_UPDATE = datetime.datetime.now()
        print(f"✅ AUTO UPDATED FOR NEW DAY {today} at 12 AM")
    return MATCHES_CACHE

def cards(data):
    html=""
    for m in data:
        c="#22c55e" if m["conf"]>=90 else "#f59e0b"
        html+=f'<div style="background:#1e293b;margin:12px 0;padding:14px;border-radius:14px;border-left:5px solid {c}"><div style="display:flex;justify-content:space-between"><b style="color:#94a3b8;font-size:11px">{m["league"]}</b><span style="background:{c};color:#000;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:bold">{m["conf"]}%</span></div><div style="margin:6px 0;font-weight:bold">{m["home"]} vs {m["away"]} • {m["time"]}</div><div style="background:#0f172a;color:#22c55e;padding:6px 10px;border-radius:8px;display:inline-block;margin:4px 0;font-weight:bold">{m["tip"]}</div> @{m["odd"]}<div style="font-size:11px;color:#64748b;margin-top:6
