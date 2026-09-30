from flask import Flask, render_template_string
from datetime import datetime

app = Flask(__name__)

# --- YOUR MONEY ACCOUNTS - CHANGE THESE ---
ADSENSE_CLIENT_ID = "ca-pub-XXXXXXXXXXXXXXXX" # <- Replace with your real AdSense ID
PAYSTACK_PUBLIC_KEY = "pk_live_XXXXXXXXXXXXXXXX" # <- Replace with your real Paystack Public Key

ALL_MATCHES = [
    {"league": "Premier League", "home": "Man City", "away": "Arsenal", "time": "15:00", "tip": "Over 2.5", "odd": "1.85", "type": "over", "confidence": "85%"},
    {"league": "La Liga", "home": "Barcelona", "away": "Real Madrid", "time": "18:00", "tip": "BTTS YES", "odd": "1.70", "type": "btts", "confidence": "80%"},
    {"league": "Serie A", "home": "Juventus", "away": "Inter", "time": "20:45", "tip": "1X Double Chance", "odd": "1.40", "type": "double", "confidence": "90%"},
    {"league": "Bundesliga", "home": "Bayern", "away": "Dortmund", "time": "17:30", "tip": "BTTS YES + Over 2.5", "odd": "2.10", "type": "over", "confidence": "78%"},
    {"league": "VIP GAME", "home": "PSG", "away": "Marseille", "time": "21:00", "tip": "2 & Over 1.5", "odd": "3.20", "type": "vip", "confidence": "95%"},
]

BASE = """
<!DOCTYPE html>
<html>
<head>
<title>Solotips - {{title}}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<!-- Google AdSense -->
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client="""+ADSENSE_CLIENT_ID+"""" crossorigin="anonymous"></script>
<!-- Paystack -->
<script src="https://js.paystack.co/v1/inline.js"></script>
<style>
body{font-family:Arial;background:#0f172a;color:white;margin:0}
.nav{background:#1e293b;padding:12px;display:flex;gap:10px;flex-wrap:wrap;position:sticky;top:0;z-index:10}
.nav a{color:white;text-decoration:none;background:#334155;padding:8px 12px;border-radius:6px;font-size:13px}
.nav a:hover{background:#22c55e;color:black}
.card{background:#1e293b;margin:10px 0;padding:12px;border-radius:10px;display:flex;justify-content:space-between;align-items:center}
.badge{background:#22c55e;color:black;padding:4px 10px;border-radius:4px;font-weight:bold}
.ads{background:#111827;padding:10px;margin:15px 0;border-radius:8px;text-align:center;color:#94a3b8;border:1px dashed #334155}
.btn{background:#22c55e;color:black;padding:12px 22px;border-radius:8px;text-decoration:none;font-weight:bold;display:inline-block;margin:10px 0;cursor:pointer;border:none}
.footer{padding:30px;text-align:center;color:#94a3b8;font-size:12px}
</style>
</head>
<body>
<div class="nav">
<a href="/">Home</a>
<a href="/free">Free</a>
<a href="/over">Over</a>
<a href="/double-chance">Double Chance</a>
<a href="/btts">BTTS</a>
<a href="/vip">VIP 🔒</a>
<a href="/policy">Policy</a>
</div>

<div style="padding:15px;max-width:800px;margin:auto">
<h2>{{title}}</h2>

<!-- ADS TOP -->
<div class="ads">
<ins class="adsbygoogle" style="display:block" data-ad-client="""+ADSENSE_CLIENT_ID+""" data-ad-slot="1234567890" data-ad-format="auto" data-full-width-responsive="true"></ins>
<script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
<p>Advertisement</p>
</div>

{{content}}

<!-- ADS BOTTOM -->
<div class="ads">
<ins class="adsbygoogle" style="display:block" data-ad-client="""+ADSENSE_CLIENT_ID+""" data-ad-slot="0987654321" data-ad-format="auto"></ins>
<script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
</div>
</div>

<div class="footer">
<p>Solotips © 2026 - 18+ Gamble Responsibly</p>
<p><a href="/policy" style="color:#94a3b8">Privacy Policy</a> | <a href="/terms" style="color:#94a3b8">Terms</a></p>
</div>

<script>
function payWithPaystack(){
  var handler = PaystackPop.setup({
    key: '"""+PAYSTACK_PUBLIC_KEY+"""',
    email: prompt("Enter your email to receive VIP access:"),
    amount: 200000, // = ₦2000 in kobo
    currency: "NGN",
    ref: ''+Math.floor((Math.random() * 1000000000) + 1),
    callback: function(response){
      alert('Payment successful! Ref: ' + response.reference + '\\nWe will send VIP to your email/WhatsApp. Screenshot this!');
      window.location.href = "/vip-unlocked?ref=" + response.reference;
    },
    onClose: function(){ alert('Payment cancelled'); }
  });
  handler.openIframe();
}
</script>
</body>
</html>
"""

def render_matches(matches, locked=False):
    html = ""
    for m in matches:
        if locked:
            tip = "<span class='badge' style='filter:blur(4px)'>LOCKED</span>"
        else:
            tip = f"<span class='badge'>{m['tip']}</span>"
        html += f"<div class='card'><div><b>{m['league']}</b><br>{m['home']} vs {m['away']} - {m['time']}<br><small>Conf: {m['confidence']}</small></div><div>{tip}<br><small>@{m['odd']}</small></div></div>"
    return html

@app.route("/")
def home():
    content = "<p>Today's Predictions - "+datetime.now().strftime("%d %b")+"</p>" + render_matches([m for m in ALL_MATCHES if m['type']!='vip'][:4])
    content += "<br><a class='btn' href='/vip'>Unlock VIP - ₦2000</a>"
    return render_template_string(BASE, title="Home - Today", content=content)

@app.route("/free")
def free(): return render_template_string(BASE, title="Free Predictions", content=render_matches([m for m in ALL_MATCHES if m['type']!='vip']))
@app.route("/over")
def over(): return render_template_string(BASE, title="Over Goals", content=render_matches([m for m in ALL_MATCHES if m['type']=='over']))
@app.route("/double-chance")
def double(): return render_template_string(BASE, title="Double Chance", content=render_matches([m for m in ALL_MATCHES if m['type']=='double']))
@app.route("/btts")
def btts(): return render_template_string(BASE, title="BTTS", content=render_matches([m for m in ALL_MATCHES if m['type']=='btts']))

@app.route("/vip")
def vip():
    content = render_matches([m for m in ALL_MATCHES if m['type']=='vip'], locked=True)
    content += "<h3>VIP - 5 Sure Odds Daily - ₦2000/month</h3><p>90% win rate, high odds. Instant access after payment.</p><button class='btn' onclick='payWithPaystack()'>Pay ₦2000 With Paystack</button><p>Or Pay to: 080XXXXXXXX WhatsApp after payment</p>"
    return render_template_string(BASE, title="VIP 🔒", content=content)

@app.route("/vip-unlocked")
def vip_unlocked():
    content = "<h3 style='color:#22c55e'>Payment Verified! Welcome to VIP</h3>" + render_matches([m for m in ALL_MATCHES if m['type']=='vip'], locked=False)
    return render_template_string(BASE, title="VIP Unlocked", content=content)

@app.route("/policy")
@app.route("/terms")
@app.route("/disclaimer")
def policy():
    c = "<h3>Privacy Policy</h3><p>We use Google AdSense cookies. We don't share personal data.</p><h3>Disclaimer</h3><p>18+ Gamble responsibly. Tips are for information only. No guarantee.</p><h3>Terms</h3><p>VIP payments are non-refundable. Contact WhatsApp for support.</p>"
    return render_template_string(BASE, title="Policy", content=c)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
