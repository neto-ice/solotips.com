from flask import Flask, render_template_string
from markupsafe import Markup
import datetime, random, requests

app = Flask(__name__)

# Cache - empty at startup so deploy never fails
CACHE = []
CACHE_DATE = None

def get_live_matches():
    today = datetime.date.today()
    date_str = today.strftime("%Y%m%d")
    pretty = today.strftime("%B %d, %Y")

    # Seed random with TODAY date so tips change everyday at 12 AM
    random.seed(int(date_str))

    all_data = []

    LEAGUES_BY_CAT = {
        "over": [("Eredivisie","ned.1"), ("2. Bundesliga","ger.2"), ("Championship","eng.2"), ("Super Lig","tur.1")],
        "free": [("Premier League","eng.1"), ("Bundesliga","ger.1"), ("Super Lig","tur.1")],
        "double": [("Belgian Pro League","bel.1"), ("Nations League","uefa.nations"), ("Championship","eng.2")],
        "btts": [("Eredivisie","ned.1"), ("Super Lig","tur.1"), ("Championship","eng.2")],
        "handicap": [("Bundesliga","ger.1"), ("Premier League","eng.1")]
    }

    TIPS = {
        "over": ["Over 2.5 - Many Goals TODAY", "Over 3.5 Goals TODAY", "Over 2.5 - High Scoring TODAY"],
        "free": ["Home Win TODAY", "Away Win TODAY", "Home Win TODAY"],
        "double": ["1X Double Chance TODAY", "X2 Double Chance TODAY", "1X Double Chance TODAY"],
        "btts": ["BTTS YES - Both Score TODAY", "BTTS YES TODAY", "BTTS YES + Over 2.5 TODAY"],
        "handicap": ["Home -1 Handicap TODAY", "Home -0.5 Handicap TODAY", "Away +1 Handicap TODAY"]
    }

    # Try live ESPN - 2 sec timeout only
    for cat, leagues in LEAGUES_BY_CAT.items():
        for league_name, league_id in leagues:
            try:
                url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_id}/scoreboard?dates={date_str}"
                r = requests.get(url, timeout=2)
                if r.status_code == 200:
                    events = r.json().get("events", [])[:1]
                    for ev in events:
                        comp = ev.get("competitions", [{}])[0]
                        teams = comp.get("competitors", [])
                        if len(teams) < 2: continue
                        home = teams[0]['team']['displayName'] if teams[0]['homeAway']=='home' else teams[1]['team']['displayName']
                        away = teams[1]['team']['displayName'] if teams[0]['homeAway']=='home' else teams[0]['team']['displayName']
                        all_data.append({
                            "league": f"{league_name} - TODAY {pretty}",
                            "home": home, "away": away, "time": ev['date'][11:16] if 'date' in ev else f"{random.randint(15,21)}:00",
                            "tip": random.choice(TIPS[cat]),
                            "odd": str(round(random.uniform(1.70,2.40),2)),
                            "cat": cat, "conf": random.randint(87,96),
                            "stats": f"LIVE TODAY {pretty} | Auto 12 AM Update"
                        })
            except: continue

    # If ESPN gave nothing (no games today for those leagues), use rotating backup that CHANGES DAILY
    if len(all_data) < 10:
        backup_pool = {
            "free": [("Arsenal","Man City"), ("Leeds","Southampton"), ("Galatasaray","Besiktas"), ("Bayern","Leverkusen"), ("Liverpool","Chelsea")],
            "over": [("Ajax","PSV"), ("Hamburg","Schalke"), ("Stoke","Bristol"), ("Bayern","Dortmund"), ("Feyenoord","AZ"), ("Trabzonspor","Fenerbahce")],
            "double": [("Club Brugge","Anderlecht"), ("Spain","Italy"), ("England","Germany"), ("Ajax","Twente")],
            "btts": [("Fenerbahce","Galatasaray"), ("PSV","Feyenoord"), ("Man City","Arsenal"), ("St Pauli","Hamburg")],
            "handicap": [("Man City","West Ham"), ("Leverkusen","Frankfurt"), ("Middlesbrough","Hull")]
        }
        for cat, games in backup_pool.items():
            # pick 2-3 games based on TODAY date - so different tomorrow
            random.shuffle(games)
            for h,a in games[:2]:
                if len([x for x in all_data if x['cat']==cat]) >=3: break
                if any(h in x['home'] for x in all_data): continue
                all_data.append({
                    "league": f"{cat.upper()} League - TODAY {pretty}",
                    "home": h, "away": a, "time": f"{random.randint(
