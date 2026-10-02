import os, json, math, sqlite3, datetime as dt, requests
from flask import Flask, render_template_string, abort
from apscheduler.schedulers.background import BackgroundScheduler

KEY = os.environ["API_FOOTBALL_KEY"]          # free key: dashboard.api-football.com
API = "https://v3.football.api-sports.io"
DB = "tips.db"
MIN_PROB = 0.80      # model probability required to publish a tip
PER_PAGE = 5
MAX_FIXTURES = 44    # free plan = 100 calls/day: 1 fixtures + 2 team-stat calls per match + settling

# One definition per tip: used both for the probability and for grading the result.
TIPS = {
    "1x2": {"Home Win": lambda h, a: h > a, "Draw": lambda h, a: h == a, "Away Win": lambda h, a: a > h},
    "double-chance": {"1X": lambda h, a: h >= a, "X2": lambda h, a: a >= h, "12": lambda h, a: h != a},
    "over": {"Over 1.5": lambda h, a: h + a >= 2, "Over 2.5": lambda h, a: h + a >= 3},
    "handicap": {"Home +1.5": lambda h, a: h - a >= -1, "Away +1.5": lambda h, a: a - h >= -1,
                 "Home -1.5": lambda h, a: h - a >= 2, "Away -1.5": lambda h, a: a - h >= 2},
    "btts": {"BTTS Yes": lambda h, a: h > 0 and a > 0, "BTTS No": lambda h, a: h == 0 or a == 0},
}
TITLES = {"1x2": "1X2", "double-chance": "Double Chance", "over": "Over Goals", "handicap": "Handicap", "btts": "BTTS"}

app = Flask(__name__)


def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS picks(day TEXT, fid INT, market TEXT, tip TEXT, prob REAL,
                 league TEXT, home TEXT, away TEXT, ko TEXT, result TEXT, score TEXT, PRIMARY KEY(fid, market))""")
    c.execute("CREATE TABLE IF NOT EXISTS stats(key TEXT PRIMARY KEY, js TEXT, day TEXT)")
    return c


def get(path, **params):
    r = requests.get(f"{API}/{path}", headers={"x-apisports-key": KEY}, params=params, timeout=20)
    r.raise_for_status()
    return r.json()["response"]


def rates(c, team, league, season):
    key = f"{team}-{league}-{season}"
    old = str(dt.date.today() - dt.timedelta(days=7))
    row = c.execute("SELECT js FROM stats WHERE key=? AND day>=?", (key, old)).fetchone()
    if row:
        return json.loads(row["js"])
    s = get("teams/statistics", team=team, league=league, season=season)
    g = s["goals"]
    out = {"n": s["fixtures"]["played"]["total"],
           "for_h": float(g["for"]["average"]["home"] or 0), "for_a": float(g["for"]["average"]["away"] or 0),
           "ag_h": float(g["against"]["average"]["home"] or 0), "ag_a": float(g["against"]["average"]["away"] or 0)}
    c.execute("INSERT OR REPLACE INTO stats VALUES(?,?,?)", (key, json.dumps(out), str(dt.date.today())))
    c.commit()
    return out


def pmf(lam, n=10):
    return [math.exp(-lam) * lam ** k / math.factorial(k) for k in range(n)]


def probs(lh, la):
    ph, pa = pmf(lh), pmf(la)
    return {m: {t: sum(ph[i] * pa[j] for i in range(10) for j in range(10) if f(i, j)) for t, f in d.items()}
            for m, d in TIPS.items()}


def generate():
    today = str(dt.datetime.utcnow().date())
    c = db()
    fixtures = [f for f in get("fixtures", date=today) if f["fixture"]["status"]["short"] == "NS"][:MAX_FIXTURES]
    for f in fixtures:
        try:
            lg, season = f["league"]["id"], f["league"]["season"]
            rh = rates(c, f["teams"]["home"]["id"], lg, season)
            ra = rates(c, f["teams"]["away"]["id"], lg, season)
            if min(rh["n"], ra["n"]) < 8:
                continue  # too little data to trust
            lh = (rh["for_h"] + ra["ag_a"]) / 2   # expected home goals
            la = (ra["for_a"] + rh["ag_h"]) / 2   # expected away goals
            for market, d in probs(lh, la).items():
                tip, p = max(d.items(), key=lambda kv: kv[1])
                if p >= MIN_PROB:
                    c.execute("INSERT OR IGNORE INTO picks VALUES(?,?,?,?,?,?,?,?,?,NULL,NULL)",
                              (today, f["fixture"]["id"], market, tip, p,
                               f"{f['league']['country']} - {f['league']['name']}",
                               f["teams"]["home"]["name"], f["teams"]["away"]["name"],
                               f["fixture"]["date"][11:16]))
        except Exception as e:
            print("skipped", f["fixture"]["id"], e)
    c.commit()


def settle():
    c = db()
    today = str(dt.datetime.utcnow().date())
    days = [r[0] for r in c.execute("SELECT DISTINCT day FROM picks WHERE result IS NULL AND day<?", (today,))]
    for d in days:
        for f in get("fixtures", date=d):
            status, fid = f["fixture"]["status"]["short"], f["fixture"]["id"]
            pending = c.execute("SELECT market, tip FROM picks WHERE fid=? AND result IS NULL", (fid,)).fetchall()
            if not pending:
                continue
            if status in ("PST", "CANC", "ABD", "AWD", "WO"):
                c.execute("UPDATE picks SET result='void' WHERE fid=?", (fid,))
            elif status in ("FT", "AET", "PEN"):
                h, a = f["score"]["fulltime"]["home"], f["score"]["fulltime"]["away"]  # 90-minute score
                for r in pending:
                    win = TIPS[r["market"]][r["tip"]](h, a)
                    c.execute("UPDATE picks SET result=?, score=? WHERE fid=? AND market=?",
                              ("win" if win else "loss", f"{h}-{a}", fid, r["market"]))
    c.commit()


def daily():
    for job in (settle, generate):
        try:
            job()
        except Exception as e:
            print(job.__name__, "failed", e)


PAGE = """<html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{t}}</title>
<style>body{margin:0;font-family:Arial;background:#0f172a;color:#e2e8f0}.nav{background:#020617;padding:10px;display:flex;gap:6px;flex-wrap:wrap;position:sticky;top:0}
.nav a,.m a{color:#94a3b8;text-decoration:none;background:#1e293b;padding:8px 14px;border-radius:20px;font-size:13px}
.m{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}.wrap{max-width:700px;margin:auto;padding:15px}
.c{background:#1e293b;margin:10px 0;padding:12px;border-radius:12px;border-left:5px solid #f59e0b}
.s{font-size:11px;color:#94a3b8}.tip{background:#0f172a;color:#22c55e;padding:4px 10px;border-radius:8px;font-weight:bold;display:inline-block;margin-top:6px}
.f{font-size:11px;color:#64748b;margin-top:24px}</style></head><body>
<div class="nav"><a href="/">Home</a>{% for k,v in titles.items() %}<a href="/{{k}}">{{v}}</a>{% endfor %}<a href="/history">History</a></div>
<div class="wrap"><h2>{{t}}</h2>
{% if home %}<div class="m">{% for k,v in titles.items() %}<a href="/{{k}}">{{v}}</a>{% endfor %}<a href="/history">Full history</a></div>{% endif %}
{% if stats %}<p class="s">{% for s in stats %}{{s.market}}: {{s.w}}/{{s.n}} won ({{(100*s.w/s.n)|round(0)|int}}%) &nbsp; {% endfor %}</p>{% endif %}
{% for r in rows %}<div class="c" style="border-color:{{ '#22c55e' if r.result=='win' else '#ef4444' if r.result=='loss' else '#f59e0b' }}">
<div class="s">{{r.league}} &middot; {{r.day}} {{r.ko}} UTC</div><div><b>{{r.home}} vs {{r.away}}</b></div>
<span class="tip">{{r.tip}}</span> <span class="s">model {{(100*r.prob)|round(0)|int}}%</span>
{% if r.result %}<span class="s"> &middot; {{r.result}}{% if r.score %} ({{r.score}}){% endif %}</span>{% endif %}</div>
{% else %}<p>No matches reach {{min}}% today. We only publish tips that clear the bar.</p>{% endfor %}
<p class="f">Model estimates from team scoring averages, not guarantees. Results above are real. 18+, gamble responsibly.</p></div></body></html>"""


def render(t, rows, **kw):
    return render_template_string(PAGE, t=t, rows=rows, titles=TITLES, min=int(MIN_PROB * 100), home=False, stats=None, **kw)


def summary(c):
    return c.execute("""SELECT market, SUM(result='win') w, COUNT(*) n FROM picks
                        WHERE result IN ('win','loss') GROUP BY market""").fetchall()


@app.route("/")
def home():
    c = db()
    rows = c.execute("SELECT * FROM picks WHERE result IN ('win','loss') ORDER BY day DESC, prob DESC LIMIT 20").fetchall()
    return render("Football Tips", rows, home=True, stats=summary(c))


@app.route("/history")
def history():
    c = db()
    rows = c.execute("SELECT * FROM picks WHERE result IS NOT NULL ORDER BY day DESC, prob DESC LIMIT 300").fetchall()
    return render("Results History", rows, stats=summary(c))


@app.route("/<market>")
def market(market):
    if market not in TIPS:
        abort(404)
    today = str(dt.datetime.utcnow().date())
    rows = db().execute("SELECT * FROM picks WHERE day=? AND market=? ORDER BY prob DESC LIMIT ?",
                        (today, market, PER_PAGE)).fetchall()
    return render(f"{TITLES[market]} - Today", rows)


sched = BackgroundScheduler(timezone="UTC")
sched.add_job(daily, "cron", hour=6)
if not db().execute("SELECT 1 FROM picks WHERE day=?", (str(dt.datetime.utcnow().date()),)).fetchone():
    sched.add_job(daily)  # first run on startup
sched.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)  # run a single worker so the scheduler fires once
