"""Builds the public GitHub Pages site in ../docs from the dashboard and data/csv.

Run dashboard/generate.py first; this reuses the index.html it writes.
"""
import os, re, shutil
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "docs")
URL = "https://junayedparves.github.io/ronaldo-career-intelligence/"
REPO = "https://github.com/JunayedParves/ronaldo-career-intelligence"
TITLE = "Cristiano Ronaldo Career Intelligence"
BLURB = "The boy from Madeira who conquered world football: every official senior match, goal and trophy in one animated dashboard."
CSVS = ["match_statistics", "goal_statistics", "season_statistics", "club_statistics", "career_overview", "international_statistics", "euro_statistics", "world_cup_statistics",
        "tournament_matches", "trophies", "individual_awards", "career_milestones", "data_quality_report", "data_sources", "career_transfers"]

for sub in ("data", "images"):
    shutil.rmtree(os.path.join(OUT, sub), ignore_errors=True)
    os.makedirs(os.path.join(OUT, sub))

for name in CSVS:
    shutil.copy(os.path.join(ROOT, "data", "csv", name + ".csv"), os.path.join(OUT, "data"))

web = os.path.join(HERE, "images", "web")
keys = {}
for n in sorted(os.listdir(web)):
    shutil.copy(os.path.join(web, n), os.path.join(OUT, "images"))
    keys[n.rsplit(".", 1)[0]] = "images/" + n
pairs = ",".join(f'{k!r}:{v!r}' for k, v in keys.items())

for n in ("style.css", "app.js"):
    shutil.copy(os.path.join(HERE, n), OUT)
for n in ("dash-shim.js", "tokens.css"):
    shutil.copy(os.path.join(HERE, "site", n), OUT)

d3 = os.path.join(OUT, "d3.v7.min.js")
if not os.path.exists(d3):
    req = urllib.request.Request("https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js", headers={"User-Agent": "CareerStatsResearch/1.0 (personal data project)"})
    open(d3, "wb").write(urllib.request.urlopen(req, timeout=60).read())
open(os.path.join(OUT, ".nojekyll"), "w").close()

body = open(os.path.join(HERE, "index.html"), encoding="utf8").read()
body = re.sub(r'<meta name="dash-one-writer">\s*', "", body)
body = re.sub(r'<link rel="stylesheet" href="style.css">\s*', "", body)
body = re.sub(r'<script src="[^"]+"></script>', "", body)
foot = (f'<footer class="site-foot"><p>Unofficial fan project, not connected to any club, federation or to the player. Crests belong to their owners and are used only to identify each team. '
        f'Photo and video credits are at the end of The story.</p><p>Built by M K Junayed Parves. <a href="{REPO}">Data, code and method on GitHub</a>.</p></footer>')
body = body.rstrip()
page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{TITLE}</title>
<meta name="description" content="{BLURB}">
<meta property="og:type" content="website">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{BLURB}">
<meta property="og:url" content="{URL}">
<meta property="og:image" content="{URL}share.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="images/crest_POR.png">
<link rel="stylesheet" href="tokens.css">
<link rel="stylesheet" href="style.css">
</head>
<body>
<div id="dash-root">
<p class="load-error" hidden>The data could not be loaded. Please refresh the page.</p>
{body}
{foot}
</div>
<script src="d3.v7.min.js"></script>
<script>window.CRX_IMG = {{{pairs}}};</script>
<script src="dash-shim.js"></script>
<script src="app.js"></script>
</body>
</html>
"""
open(os.path.join(OUT, "index.html"), "w", encoding="utf8").write(page)
print({n: os.path.getsize(os.path.join(OUT, n)) for n in os.listdir(OUT) if os.path.isfile(os.path.join(OUT, n))})
