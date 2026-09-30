from flask import Flask, render_template_string
import os, requests, math
from datetime import date

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html><head><title>SoloTips.com</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{font-family:Arial;background:#0f172a;color:white;padding:15px}
.card{background:#1e293b;padding:15px;margin:12px 0;border-radius:12px}
.score{font-size:22px;font-weight:bold;color:#22c55e}</style>
</head><body>
<h1>⚽ SoloTips.com - Today's Predictions</h1>
{% for m in games %}
<div class="card">
<h3>{{m.home}} vs {{m.away}}</h3>
<div class="score">{{m.pred}}</div>
<small>{{m.league}} | Conf: {{m.conf}}%</small>
</div>
{% endfor %}
</body></html>
"""

@app.route("/")
def home():
    # Demo data for now - will be live after you add API key on Render
    games = [
        {"home":"Man City","away":"Arsenal","league":"Premier League","pred":"2-1","conf":78},
        {"home":"Barcelona","away":"Real Madrid","league":"La Liga","pred":"1-1","conf":72},
    ]
    return render_template_string(HTML, games=games)

if __name__ == "__main__":
    app.run()
