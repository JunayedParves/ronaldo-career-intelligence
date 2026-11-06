#!/usr/bin/env python3
"""Cristiano Ronaldo Career Intelligence Database - reproducible build.

Reads the raw snapshots in data/raw (retrieved 2026-11-06) and writes every CSV in data/csv.
Standard library only. Run:  python scripts/build_dataset.py
NULL policy: unavailable values are written as empty cells, never as zero.
"""
import collections, csv, datetime as dt, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wikitable as W

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW, OUT = os.path.join(ROOT, "data", "raw"), os.path.join(ROOT, "data", "csv")
os.makedirs(OUT, exist_ok=True)
RETRIEVED, LAST_MATCH = "2026-11-06", "2026-10-29"
DOB = dt.date(1985, 2, 5)
PLAYER_ID = "CR7"


def feed(name):
    return json.load(open(os.path.join(RAW, "feeds", name), encoding="utf8"))


def wiki(name):
    return open(os.path.join(RAW, "wikipedia", name), encoding="utf8").read()


def write(name, rows, cols=None):
    cols = cols or list(rows[0].keys())
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="raise")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in cols})
    print(f"  {name:34} {len(rows):>6} rows  {len(cols):>3} cols")


def num(v, f=int):
    """Numeric or None. '-', '', None and '#DIV/0!' are unavailable, not zero."""
    if v in (None, "", "-"):
        return None
    try:
        return f(float(v))
    except (TypeError, ValueError):
        return None


def ratio(a, b, n=3):
    return round(a / b, n) if a is not None and b else None


# ---------------------------------------------------------------- sources
SOURCES = [
    ("S01", "MessivsRonaldo.app - match history feed", "Tier 2 - statistical database", "https://www.messivsronaldo.app/match-histories/ronaldo-match-history/", "Accessed", "Match-level spine: 1,343 official senior matches, minutes, starts, goals, Opta assists, penalties, free kicks, body part, shots", "Compiled from Opta and club/competition data. Assists default to the Opta definition (last touch before a team-mate scores). Club friendlies excluded. Shots and ratings are partial before 2009-10."),
    ("S02", "MessivsRonaldo.app - every-goal feed", "Tier 2 - statistical database", "https://www.messivsronaldo.app/ronaldo-all-goals/", "Accessed", "Goal-level detail: minute, situation, body part, assister, goalkeeper, venue", "Facts only were kept; the site's written commentary and video links were not copied."),
    ("S03", "MessivsRonaldo.app - honours feed", "Tier 2 - statistical database", "https://www.messivsronaldo.app/honours-and-achievements/", "Accessed", "Second source for trophies and awards", "Counts 37 team trophies including three with no recorded appearance."),
    ("S04", "MessivsRonaldo.app - decisive goals feed", "Tier 2 - statistical database", "https://www.messivsronaldo.app/detailed-stats/match-winning-goals/", "Accessed", "Winning-goal flags", "'Match winner' is the goal that put the team ahead for good when level. The site's second tag covers winners scored when already ahead. Definition is inferred from page filters."),
    ("S05", "Wikipedia - Cristiano Ronaldo (Career statistics, Honours)", "Tier 3 - reference aggregate", "https://en.wikipedia.org/wiki/Cristiano_Ronaldo", "Accessed", "Independent season and year tables for reconciliation; biography; honours", "Table states updated to match played 29 October 2026; cites WorldFootball, Soccerway, FPF and eu-football.info."),
    ("S06", "Wikipedia - List of senior career goals by Cristiano Ronaldo", "Tier 3 - reference aggregate", "https://en.wikipedia.org/wiki/List_of_senior_career_goals_by_Cristiano_Ronaldo", "Accessed", "Independent goal-by-goal cross-check of all 985 goals", "Cites FBref goal log."),
    ("S07", "Wikipedia - List of international goals scored by Cristiano Ronaldo", "Tier 3 - reference aggregate", "https://en.wikipedia.org/wiki/List_of_international_goals_scored_by_Cristiano_Ronaldo", "Accessed", "Cap numbers for every international goal", "Goal and cap numbers cited match by match."),
    ("S08", "Wikipedia - List of career achievements by Cristiano Ronaldo", "Tier 3 - reference aggregate", "https://en.wikipedia.org/wiki/List_of_career_achievements_by_Cristiano_Ronaldo", "Accessed", "Awards, nominations, placings and records", "Rows the source marks 'citation needed' are flagged in verification_status."),
    ("S09", "Wikipedia - tournament group and knockout pages (23 pages)", "Tier 3 - reference aggregate", "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_knockout_stage", "Accessed", "Line-ups: yellow cards and captaincy for World Cup and Euro matches", "Line-ups transcribed from FIFA and UEFA match reports."),
    ("S10", "Ronaldo Stats (ronaldostats.app)", "Tier 2 - statistical database", "https://ronaldostats.app/", "Accessed", "Independent totals check; alternate assists count (291)", "Credits assists goal by goal, a broader definition than Opta. Updated 30 October 2026."),
    ("S11", "CR7 Counter (cr7counter.com)", "Tier 3 - unofficial tracker", "https://www.cr7counter.com/", "Accessed", "Independent goal total check", "Manually verified 2 November 2026; confirms Ronaldo did not play on 2 November 2026."),
    ("S12", "UEFA - Champions League all-time top scorers", "Tier 1 - official", "https://www.uefa.com/uefachampionsleague/history/rankings/players/goals_scored/", "Accessed", "Official UEFA Champions League goals: 141", "UEFA's total includes qualifying matches."),
    ("S13", "Real Madrid - official player history", "Tier 1 - official", "https://www.realmadrid.com/en-US/the-club/history/football-legends/cristiano-ronaldo-dos-santos-aveiro", "Accessed via search result", "Official club totals: 451 goals in 438 matches", "Read through a search summary, not the full page."),
    ("S14", "FIFA - player feature", "Tier 1 - official", "https://www.fifa.com/en/articles/26-superstars-cristiano-ronaldo", "Accessed via search result", "Real Madrid total of 450 in 438", "Read through a search summary, not the full page."),
    ("S15", "Guinness World Records - most international caps (male)", "Tier 1 - official", "https://www.guinnessworldrecords.com/world-records/64289-most-international-caps-for-football-soccer-by-an-individual-male", "Accessed via search result", "233 caps to 6 July 2026; first man to 200 caps", "Page predates the 24 September 2026 Wales match."),
    ("S16", "Guinness World Records - most international goals (male)", "Tier 1 - official", "https://www.guinnessworldrecords.com/world-records/81337-most-goals-scored-in-international-football-soccer-matches-by-an-individual-ma", "Accessed via search result", "146 goals, 12 June 2004 to 2 July 2026", "Read through a search summary."),
    ("S17", "ESPN - All 14 Cristiano Ronaldo red cards", "Tier 2 - press", "https://africa.espn.com/football/story/_/id/46962434/all-cristiano-ronaldo-14-red-cards-portugal-man-united-real-madrid-more", "Accessed", "Dated list of red cards", "Published 14 November 2025. Includes one card for Portugal U17, excluded here as youth football."),
    ("S18", "Planet Football - Messi and Ronaldo disciplinary records", "Tier 2 - press", "https://www.planetfootball.com/stats-tables/messi-ronaldo-red-cards-yellow-cards-disciplinary-record", "Accessed", "Career yellow cards (162) and reds (13: 9 straight, 4 second yellow)", "Published 14 November 2025. Own compilation; scope of the yellow total is not stated."),
    ("S19", "ESPN - Ronaldo retires from international duty", "Tier 2 - press", "https://www.espn.com/soccer/story/_/id/49266866/cristiano-ronaldo-portugal-jorge-jesus-retires-international", "Accessed via search result", "International retirement announced 5 November 2026", "Corroborated by Al Jazeera and Forbes; effective after the November 2026 break."),
    ("S20", "FIFA - first man to score in six World Cups", "Tier 1 - official", "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/cristiano-ronaldo-portugal-goal-record", "Accessed via search result", "Six-World-Cup scoring record", "Direct fetch returned an empty page; the claim was read from the search summary and agrees with Yahoo Sports and Wikipedia."),
    ("S21", "football.co.uk - Juventus confirm Ronaldo sale", "Tier 2 - press", "https://www.football.co.uk/news/juventus-confirm-cristiano-ronaldo-sale-to-man-utd/745199", "Accessed via search result", "2021 fee: EUR 15m over five years plus up to EUR 8m add-ons", "Secondary report of the Juventus statement."),
    ("S22", "Transfermarkt", "Tier 2 - statistical database", "https://www.transfermarkt.com/cristiano-ronaldo/leistungsdatendetails/spieler/8198", "Blocked", "Requested in the brief; would supply season cards", "Site presents a human-verification check. Not bypassed."),
    ("S23", "FBref", "Tier 2 - statistical database", "https://fbref.com/en/players/dea698d9/Cristiano-Ronaldo", "Blocked", "Requested in the brief; would supply season cards", "Site presents a Cloudflare challenge. Not bypassed. Wikipedia's goal list (S06) cites FBref."),
    ("S24", "WorldFootball.net", "Tier 2 - statistical database", "https://www.worldfootball.net/player_summary/cristiano-ronaldo/", "Blocked", "Requested in the brief", "HTTP 403 to automated requests."),
    ("S25", "11v11", "Tier 2 - statistical database", "https://www.11v11.com/players/cristiano-ronaldo-243138/", "Blocked", "Requested in the brief", "HTTP 403 to automated requests."),
    ("S26", "Statto", "Tier 2 - statistical database", "", "Not used", "Requested in the brief", "Not reached in this build."),
    ("S27", "Manchester United, Juventus and Saudi Pro League official sites", "Tier 1 - official", "", "Not used", "Requested in the brief", "No figures were taken from these sites in this build; a gap in Tier 1 coverage."),
]

# ---------------------------------------------------------------- reference maps
TEAMS = {
    "SPO": ("Sporting CP", "Club", "Portugal", "Primeira Liga", 1),
    "MU1": ("Manchester United (2003-09)", "Club", "England", "Premier League", 2),
    "RMA": ("Real Madrid", "Club", "Spain", "La Liga", 3),
    "JUV": ("Juventus", "Club", "Italy", "Serie A", 4),
    "MU2": ("Manchester United (2021-22)", "Club", "England", "Premier League", 5),
    "NAS": ("Al Nassr", "Club", "Saudi Arabia", "Saudi Pro League", 6),
    "POR": ("Portugal", "National team", "Portugal", "", 7),
}
COMP = {  # feed name: id, display, type, group, organiser, scope, bucket used against Wikipedia
    "Primeira Liga": ("PRI", "Primeira Liga", "Domestic league", "Club", "Liga Portugal", "Domestic", "League"),
    "Premier League": ("EPL", "Premier League", "Domestic league", "Club", "Premier League", "Domestic", "League"),
    "La Liga": ("LAL", "La Liga", "Domestic league", "Club", "LaLiga", "Domestic", "League"),
    "Serie A": ("SEA", "Serie A", "Domestic league", "Club", "Lega Serie A", "Domestic", "League"),
    "Saudi Pro League": ("SPL", "Saudi Pro League", "Domestic league", "Club", "Saudi Pro League", "Domestic", "League"),
    "Taça de Portugal": ("TDP", "Taça de Portugal", "Domestic cup", "Club", "FPF", "Domestic", "NatCup"),
    "FA Cup": ("FAC", "FA Cup", "Domestic cup", "Club", "The FA", "Domestic", "NatCup"),
    "Copa del Rey": ("CDR", "Copa del Rey", "Domestic cup", "Club", "RFEF", "Domestic", "NatCup"),
    "Coppa Italia": ("COI", "Coppa Italia", "Domestic cup", "Club", "Lega Serie A", "Domestic", "NatCup"),
    "Saudi King Cup": ("SKC", "King's Cup (Saudi Arabia)", "Domestic cup", "Club", "SAFF", "Domestic", "NatCup"),
    "League Cup": ("ELC", "Football League Cup", "Domestic league cup", "Club", "EFL", "Domestic", "LeagueCup"),
    "FA Community Shield": ("FCS", "FA Community Shield", "Domestic super cup", "Club", "The FA", "Domestic", "Other"),
    "Supercopa de Espana": ("SCE", "Supercopa de España", "Domestic super cup", "Club", "RFEF", "Domestic", "Other"),
    "Supercoppa Italiana": ("SCI", "Supercoppa Italiana", "Domestic super cup", "Club", "Lega Serie A", "Domestic", "Other"),
    "Saudi Super Cup": ("SSC", "Saudi Super Cup", "Domestic super cup", "Club", "SAFF", "Domestic", "Other"),
    "Champions League": ("UCL", "UEFA Champions League", "UEFA club competition", "Club", "UEFA", "Continental", "Continental"),
    "Champions League Qualifying": ("UCQ", "UEFA Champions League qualifying", "UEFA club competition", "Club", "UEFA", "Continental", "Continental"),
    "UEFA Cup": ("UEC", "UEFA Cup", "UEFA club competition", "Club", "UEFA", "Continental", "Continental"),
    "Europa League": ("UEL", "UEFA Europa League", "UEFA club competition", "Club", "UEFA", "Continental", "Continental"),
    "UEFA Super Cup": ("USC", "UEFA Super Cup", "UEFA club competition", "Club", "UEFA", "Continental", "Other"),
    "AFC Champions League": ("ACL", "AFC Champions League / Elite", "AFC club competition", "Club", "AFC", "Continental", "Continental"),
    "AFC Champions League 2": ("AC2", "AFC Champions League Two", "AFC club competition", "Club", "AFC", "Continental", "Continental"),
    "Arab Club Champions Cup": ("ARC", "Arab Club Champions Cup", "Regional club competition", "Club", "UAFA", "Regional", "Other"),
    "Club World Cup": ("CWC", "FIFA Club World Cup", "FIFA club competition", "Club", "FIFA", "Global", "Other"),
    "World Cup": ("WC", "FIFA World Cup", "International tournament", "International", "FIFA", "Global", None),
    "World Cup Qualifier": ("WCQ", "FIFA World Cup qualifiers", "International qualifier", "International", "FIFA / UEFA", "Global", None),
    "UEFA European Championships": ("EUR", "UEFA European Championship", "International tournament", "International", "UEFA", "Continental", None),
    "Euros Qualifier": ("EUQ", "UEFA European Championship qualifiers", "International qualifier", "International", "UEFA", "Continental", None),
    "UEFA Nations League": ("UNL", "UEFA Nations League", "International league", "International", "UEFA", "Continental", None),
    "Confederations Cup": ("CFC", "FIFA Confederations Cup", "International tournament", "International", "FIFA", "Global", None),
    "International Friendly": ("FRI", "International friendly", "International friendly", "International", "National associations", "Friendly", None),
}


def historical_name(feed_name, season):
    if feed_name == "AFC Champions League":
        return "AFC Champions League Elite" if int(season[:4]) >= 2024 else "AFC Champions League"
    return COMP[feed_name][1]


HIST_NOTE = {
    "UEC": "Renamed UEFA Europa League from 2009-10; he played it only in 2002-03.",
    "UEL": "Successor to the UEFA Cup.",
    "ACL": "AFC Champions League until 2023-24; AFC Champions League Elite from 2024-25.",
    "AC2": "Second-tier AFC club competition, launched 2024-25.",
    "UNL": "First edition 2018-19.",
    "CFC": "Discontinued; last edition 2017.",
    "ARC": "Run by UAFA; not an AFC competition.",
    "UCQ": "UEFA includes these matches in its all-time Champions League totals; many databases do not.",
    "FRI": "Senior caps recognised by FIFA; held apart from competitive totals with is_competitive.",
}
CONF = {
    "CAF": "Algeria,Angola,Cameroon,Cape Verde,DR Congo,Egypt,Ghana,Ivory Coast,Morocco,Mozambique,Nigeria,South Africa",
    "AFC": "China,Iran,North Korea,Qatar,Saudi Arabia,South Korea,Uzbekistan",
    "CONCACAF": "Canada,Mexico,Panama,USA",
    "CONMEBOL": "Argentina,Brazil,Chile,Colombia,Ecuador,Uruguay",
    "OFC": "New Zealand",
    "UEFA": "Albania,Andorra,Armenia,Austria,Azerbaijan,Belgium,Bosnia and Herzegovina,Bulgaria,Croatia,Cyprus,Czech Republic,Denmark,England,Estonia,Faroe Islands,Finland,France,Georgia,Germany,Greece,Hungary,Iceland,Israel,Italy,Kazakhstan,Latvia,Liechtenstein,Lithuania,Luxembourg,Netherlands,North Macedonia,Northern Ireland,Norway,Poland,Republic of Ireland,Russia,Scotland,Serbia,Slovakia,Slovenia,Spain,Sweden,Switzerland,Turkey,Ukraine,Wales",
}
CONF_OF = {n: k for k, v in CONF.items() for n in v.split(",")}
CONF_REGION = {"UEFA": "Europe", "AFC": "Asia", "CAF": "Africa", "CONCACAF": "North America", "CONMEBOL": "South America", "OFC": "Oceania"}
STAGE = {"Group": "Group stage", "R32": "Round of 32", "R16": "Round of 16", "QF": "Quarter-final", "SF": "Semi-final", "F": "Final", "3rd Place Play-off": "Third-place play-off", "Play-off": "Play-off", "R64": "Round of 64", "R96": "Round of 96"}
STAGE_ORDER = {"Group stage": 1, "Round of 32": 2, "Round of 16": 3, "Quarter-final": 4, "Semi-final": 5, "Third-place play-off": 6, "Final": 7}
EURO_EDITION = {"2004": "Euro 2004", "2008": "Euro 2008", "2012": "Euro 2012", "2016": "Euro 2016", "2021": "Euro 2020", "2024": "Euro 2024"}
HOST = {"Euro 2004": "Portugal", "Euro 2008": "Austria and Switzerland", "Euro 2012": "Poland and Ukraine", "Euro 2016": "France", "Euro 2020": "Pan-European", "Euro 2024": "Germany", "2006 World Cup": "Germany", "2010 World Cup": "South Africa", "2014 World Cup": "Brazil", "2018 World Cup": "Russia", "2022 World Cup": "Qatar", "2026 World Cup": "Canada, Mexico and USA"}

# ---------------------------------------------------------------- spine: matches
raw = [e["node"] for e in feed("pd_match-histories_ronaldo-match-history.json")["result"]["data"]["allSheetRonaldoMatchHistory"]["edges"]]
decisive = {}
for e in feed("pd_detailed-stats_match-winning-goals.json")["result"]["data"]["allSheetRonaldoMatchHistory"]["edges"]:
    n = e["node"]
    d, m = n["date"].split("-")
    decisive[f'{n["year"]}-{m}-{d}'] = n["goalTimes"] or ""
RED = ["2004-05-15", "2006-01-14", "2007-08-15", "2008-11-30", "2009-12-05", "2010-01-24", "2013-05-17", "2014-02-02", "2015-01-24", "2017-08-13", "2018-09-19", "2024-04-08", "2025-11-13"]


def team_id(x, d):
    t = x["team"]
    if t == "Manchester United":
        return "MU1" if d.year < 2015 else "MU2"
    return {"Sporting CP": "SPO", "Real Madrid": "RMA", "Juventus": "JUV", "Al Nassr": "NAS", "Portugal": "POR"}[t]


M = []
for x in raw:
    d, mo = x["date"].split("-")
    M.append((dt.date(int(x["year"]), int(mo), int(d)), x))
M.sort(key=lambda t: t[0])
assert len({m[0] for m in M}) == 1343, "one match per date expected"
matches = []
for i, (date, x) in enumerate(M, 1):
    iso = date.isoformat()
    tid = team_id(x, date)
    fn = x["competition"]
    c = COMP[fn]
    gs, ga = int(x["scoreTeam"]), int(x["scoreOpponent"])
    tags = [p.split(",")[0] for p in decisive.get(iso, "").split("|") if p]
    season = x["season"][:5] + x["season"][-2:]
    tourn = None
    if fn == "World Cup":
        tourn = f'{x["year"]} World Cup'
    elif fn == "UEFA European Championships":
        tourn = EURO_EDITION[x["year"]]
    elif fn == "Confederations Cup":
        tourn = "2017 Confederations Cup"
    elif fn == "UEFA Nations League":
        tourn = f"Nations League {season}"
    rating = num(x["rating"], float)
    matches.append(dict(
        match_id=f"M{i:04d}", player_id=PLAYER_ID, match_date=iso, season_id=season, calendar_year=date.year,
        team_id=tid, competition_id=c[0], competition_name_at_time=historical_name(fn, season), tournament_id=tourn,
        stage=STAGE[x["round"]] if x["round"] else None, venue_type={"H": "Home", "A": "Away", "N": "Neutral"}[x["homeAway"]],
        opponent=x["opponent"], team_score=gs, opponent_score=ga, result="W" if gs > ga else "L" if gs < ga else "D",
        shootout_result={"1": "Won", "x": "Lost"}.get(x["shootout"]), is_competitive=0 if fn == "International Friendly" else 1,
        age_at_match=round((date - DOB).days / 365.25, 2), started=int(x["started"]), substitute=1 - int(x["started"]), minutes=int(x["minsPlayed"]),
        goals=int(x["goals"]), assists_opta=int(x["assists"]), assists_all=num(x["allAssists"]),
        goal_contributions=int(x["goals"]) + int(x["assists"]), pens_scored=int(x["pens"]), pens_missed=int(x["pensMissed"]),
        hat_tricks=int(x["hatTricks"]), free_kick_goals=int(x["freeKicks"]), inside_box_goals=int(x["insideBox"]), outside_box_goals=int(x["outsideBox"]),
        left_foot_goals=int(x["left"]), right_foot_goals=int(x["right"]), headed_goals=int(x["head"]), other_goals=int(x["other"]),
        winning_goals=tags.count("mw"), winning_goals_when_ahead=tags.count("gwg"),
        yellow_cards=None, red_cards=1 if iso in RED else 0, captain=None,
        shots=num(x["shots"]), shots_on_target=num(x["shotsOnTarget"]), key_passes=num(x["keyPasses"]), successful_dribbles=num(x["successfulDribbles"]),
        xg=num(x["xg"], float), xa=num(x["xa"], float), match_rating=rating if rating else None, man_of_the_match=num(x["motm"]),
        cards_source="S17" if iso in RED else None, source_id="S01"))
by_date = {m["match_date"]: m for m in matches}
missing_red = [d for d in RED if d not in by_date]
assert not missing_red, missing_red

# yellow cards and captaincy from tournament line-ups
MONTHS = {m: i + 1 for i, m in enumerate("January February March April May June July August September October November December".split())}
tdir = os.path.join(RAW, "wikipedia", "tournaments")
lineup_hits = {}
PAGE_DATE = {"UEFA_Euro_2004_final.txt": "2004-07-04", "UEFA_Euro_2016_final.txt": "2016-07-10", "Battle_of_Nuremberg.txt": "2006-06-25"}
for f in sorted(os.listdir(tdir)):
    t = open(os.path.join(tdir, f), encoding="utf8").read()
    for mt in re.finditer(r"^\|[^\n]*\[\[Cristiano Ronaldo\]\][^\n]*$", t, re.M):
        line = mt.group(0)
        hdr = t[t.rfind("ootball box", 0, mt.start()):][:900]
        dm = re.search(r"date\s*=\s*\{\{[Ss]tart date\|(\d{4})\|(\d+)\|(\d+)", hdr)
        if dm:
            iso = f"{int(dm[1])}-{int(dm[2]):02d}-{int(dm[3]):02d}"
        else:
            dm = re.search(r"date\s*=\s*(\d+) (\w+) (\d{4})", hdr)
            iso = f"{dm[3]}-{MONTHS[dm[2]]:02d}-{int(dm[1]):02d}" if dm else PAGE_DATE.get(f)
        if iso is None:
            continue
        if iso not in by_date:  # some kick-offs are dated UTC in one source and local in the other
            near = [(dt.date.fromisoformat(iso) + dt.timedelta(k)).isoformat() for k in (1, -1)]
            iso = next((n for n in near if n in by_date and by_date[n]["competition_id"] in ("EUR", "WC")), iso)
        lineup_hits[iso] = (len(re.findall(r"\{\{\s*yel", line, re.I)), "Captain" in line)
unjoined = [d for d in lineup_hits if d not in by_date]
for iso, (y, cap) in lineup_hits.items():
    if iso in by_date:
        m = by_date[iso]
        m["yellow_cards"], m["captain"] = y, 1 if cap else 0
        m["cards_source"] = (m["cards_source"] + "+S09") if m["cards_source"] else "S09"


# ---------------------------------------------------------------- aggregates
def agg(rows):
    g = lambda k: sum(r[k] for r in rows)
    mins, goals, ast, apps = g("minutes"), g("goals"), g("assists_opta"), len(rows)
    yel = [r["yellow_cards"] for r in rows]
    shots = [r["shots"] for r in rows if r["shots"] is not None]
    return dict(
        appearances=apps, starts=g("started"), substitute_appearances=g("substitute"), minutes_played=mins, goals=goals, assists=ast,
        assists_all_definitions=sum(r["assists_all"] or 0 for r in rows), pens_scored=g("pens_scored"), pens_missed=g("pens_missed"), hat_tricks=g("hat_tricks"),
        free_kick_goals=g("free_kick_goals"), headed_goals=g("headed_goals"), left_foot_goals=g("left_foot_goals"), right_foot_goals=g("right_foot_goals"),
        winning_goals=g("winning_goals"), yellow_cards=sum(yel) if yel and all(v is not None for v in yel) else None, red_cards=g("red_cards"),
        goals_per_appearance=ratio(goals, apps), goals_per_90=ratio(goals * 90, mins), assists_per_appearance=ratio(ast, apps), assists_per_90=ratio(ast * 90, mins),
        wins=sum(r["result"] == "W" for r in rows), draws=sum(r["result"] == "D" for r in rows), losses=sum(r["result"] == "L" for r in rows),
        shots=sum(shots) if len(shots) == apps else None)


def group(rows, *keys):
    out = collections.OrderedDict()
    for r in rows:
        out.setdefault(tuple(r[k] for k in keys), []).append(r)
    return out


CID = {v[0]: v for v in COMP.values()}
club = [m for m in matches if m["team_id"] != "POR"]
intl = [m for m in matches if m["team_id"] == "POR"]

print("Writing CSVs")
write("match_statistics.csv", matches)

season_rows = []
for (sid, tid, cid), rows in group(club, "season_id", "team_id", "competition_id").items():
    season_rows.append(dict(player="Cristiano Ronaldo", player_id=PLAYER_ID, team_id=tid, club=TEAMS[tid][0], season_id=sid, competition_id=cid,
                            competition=rows[0]["competition_name_at_time"], competition_type=CID[cid][2],
                            country=TEAMS[tid][2] if CID[cid][5] == "Domestic" else CID[cid][5], **agg(rows), source_id="S01+S17"))
write("season_statistics.csv", season_rows)

# ---------------------------------------------------------------- trophies
T = [  # name, feed competition, team, season, level, listed by Wikipedia, listed by tracker
    ("Supertaça Cândido de Oliveira", None, "SPO", "2002-03", "Domestic super cup", 1, 1),
    ("Premier League", "Premier League", "MU1", "2006-07", "League", 1, 1), ("Premier League", "Premier League", "MU1", "2007-08", "League", 1, 1), ("Premier League", "Premier League", "MU1", "2008-09", "League", 1, 1),
    ("FA Cup", "FA Cup", "MU1", "2003-04", "Domestic cup", 1, 1), ("Football League Cup", "League Cup", "MU1", "2005-06", "Domestic cup", 1, 1), ("Football League Cup", "League Cup", "MU1", "2008-09", "Domestic cup", 1, 1),
    ("FA Community Shield", "FA Community Shield", "MU1", "2007-08", "Domestic super cup", 1, 1), ("FA Community Shield", "FA Community Shield", "MU1", "2008-09", "Domestic super cup", 0, 1),
    ("UEFA Champions League", "Champions League", "MU1", "2007-08", "Continental", 1, 1), ("FIFA Club World Cup", "Club World Cup", "MU1", "2008-09", "Intercontinental", 1, 1),
    ("La Liga", "La Liga", "RMA", "2011-12", "League", 1, 1), ("La Liga", "La Liga", "RMA", "2016-17", "League", 1, 1), ("Copa del Rey", "Copa del Rey", "RMA", "2010-11", "Domestic cup", 1, 1), ("Copa del Rey", "Copa del Rey", "RMA", "2013-14", "Domestic cup", 1, 1),
    ("Supercopa de España", "Supercopa de Espana", "RMA", "2012-13", "Domestic super cup", 1, 1), ("Supercopa de España", "Supercopa de Espana", "RMA", "2017-18", "Domestic super cup", 1, 1),
    ("UEFA Champions League", "Champions League", "RMA", "2013-14", "Continental", 1, 1), ("UEFA Champions League", "Champions League", "RMA", "2015-16", "Continental", 1, 1), ("UEFA Champions League", "Champions League", "RMA", "2016-17", "Continental", 1, 1), ("UEFA Champions League", "Champions League", "RMA", "2017-18", "Continental", 1, 1),
    ("UEFA Super Cup", "UEFA Super Cup", "RMA", "2014-15", "Continental", 1, 1), ("UEFA Super Cup", "UEFA Super Cup", "RMA", "2016-17", "Continental", 0, 1), ("UEFA Super Cup", "UEFA Super Cup", "RMA", "2017-18", "Continental", 1, 1),
    ("FIFA Club World Cup", "Club World Cup", "RMA", "2014-15", "Intercontinental", 1, 1), ("FIFA Club World Cup", "Club World Cup", "RMA", "2016-17", "Intercontinental", 1, 1), ("FIFA Club World Cup", "Club World Cup", "RMA", "2017-18", "Intercontinental", 1, 1),
    ("Serie A", "Serie A", "JUV", "2018-19", "League", 1, 1), ("Serie A", "Serie A", "JUV", "2019-20", "League", 1, 1), ("Coppa Italia", "Coppa Italia", "JUV", "2020-21", "Domestic cup", 1, 1), ("Supercoppa Italiana", "Supercoppa Italiana", "JUV", "2018-19", "Domestic super cup", 1, 1), ("Supercoppa Italiana", "Supercoppa Italiana", "JUV", "2020-21", "Domestic super cup", 1, 1),
    ("Saudi Pro League", "Saudi Pro League", "NAS", "2025-26", "League", 1, 1), ("Arab Club Champions Cup", "Arab Club Champions Cup", "NAS", "2023-24", "Regional", 1, 1),
    ("UEFA European Championship", "UEFA European Championships", "POR", "2015-16", "International tournament", 1, 1), ("UEFA Nations League", "UEFA Nations League", "POR", "2018-19", "International tournament", 1, 1), ("UEFA Nations League", "UEFA Nations League", "POR", "2024-25", "International tournament", 1, 1),
]
trophies = []
for i, (name, fn, tid, season, level, wk, tr) in enumerate(T, 1):
    rows = [m for m in matches if fn and m["team_id"] == tid and m["season_id"] == season and m["competition_id"] == COMP[fn][0]]
    final = [m for m in rows if m["stage"] == "Final"]
    single = level == "Domestic super cup" or fn == "UEFA Super Cup"
    if not rows:
        status, counted = "No recorded appearance", 0
    elif level == "League":
        status, counted = f"Played in league ({len(rows)} apps)", 1
    elif final or single:
        status, counted = "Played in final", 1
    else:
        status, counted = f"Played in competition, not final ({len(rows)} apps)", 1
    trophies.append(dict(
        trophy_id=f"T{i:02d}", trophy_name=name, competition=name, trophy_category="International trophy" if tid == "POR" else "Club trophy", competition_level=level,
        team_id=tid, club_or_country=TEAMS[tid][0], team=TEAMS[tid][0].split(" (")[0], season_year=season, ronaldo_apps_in_competition=len(rows),
        ronaldo_goals_in_competition=sum(m["goals"] for m in rows), ronaldo_participation_status=status, counts_as_played=counted, listed_by_wikipedia=wk, listed_by_tracker=tr,
        official_source="+".join(s for s, on in (("S05", wk), ("S03", tr)) if on),
        verification_status="Cross-checked (2 sources) and match log" if wk and tr and rows else "Disputed: see data_quality_report"))
write("trophies.csv", trophies)
tcount = collections.Counter(t["team_id"] for t in trophies if t["counts_as_played"])
played_trophies = sum(tcount.values())
assert len(trophies) == 37


# ---------------------------------------------------------------- awards
def split_years(s):
    return [p.strip() for p in re.split(r",\s*(?:and\s+)?|\s+and\s+", s.replace("[cn]", "").strip()) if p.strip()]


def result_of(v):
    v = v.replace("[cn]", "").strip().lower()
    if "nominated" in v:
        return "Nominated"
    if v in ("won", "gold", "first team", "winner"):
        return "Won"
    if v in ("runner-up", "silver", "second place"):
        return "Runner-up"
    if v in ("third place", "bronze"):
        return "Third place"
    if v == "nom":
        return "Nominated"
    if v == "sho":
        return "Shortlisted"
    if "team" in v or "selected" in v:
        return "Team selection"
    return "Placed: " + v


def team_at(y):
    if y is None:
        return None
    for a_, b_, n in ((2002, 2003, "Sporting CP"), (2004, 2009, "Manchester United"), (2010, 2018, "Real Madrid"), (2019, 2021, "Juventus"), (2022, 2022, "Manchester United"), (2023, 2030, "Al Nassr")):
        if a_ <= y <= b_:
            return n


REGION_TEAM = {"England": "Manchester United", "Manchester United": "Manchester United", "Spain": "Real Madrid", "Real Madrid": "Real Madrid", "Italy": "Juventus", "Juventus": "Juventus", "Saudi Arabia": "Al Nassr", "Al Nassr": "Al Nassr", "Al-Nassr": "Al Nassr", "Portugal": "Portugal"}
MAJOR = re.compile(r"Ballon d'Or$|The Best FIFA Men|Men's Player of the Year|Club Footballer of the Year|Golden Shoe|Pichichi|Golden Boot|Capocannoniere|Premier League Player of the Season|Serie A Footballer|Pusk", re.I)
hon = [e["node"] for e in feed("pd_honours-and-achievements.json")["result"]["data"]["allSheetHonours"]["edges"]]


def hy(name):
    for h in hon:
        if h["honour"] == name and h["ryears"]:
            return {int(y) for y in re.findall(r"(?<!\d)(\d{4})", h["ryears"])}
    return set()


XCHECK = [(r"^Ballon d'Or$|^FIFA Ballon d'Or$", "Ballon d'Or"), (r"The Best FIFA Men", "FIFA World Player of the Year"), (r"^World Player of the Year \(FIFA\)", "FIFA World Player of the Year"),
          (r"Men's Player of the Year", "UEFA Best Player (2011-)"), (r"Club Footballer of the Year", "UEFA Club Footballer of the Year (97-2010)"), (r"Golden Shoe", "European Golden Shoe"),
          (r"Pichichi", "La Liga Top Scorer (Pichichi)"), (r"Premier League \(Golden Boot\)", "Premier League Top Scorer"), (r"Capocannoniere", "Serie A Top Scorer"), (r"Saudi Pro League", "Saudi Pro League Top Scorer"),
          (r"Champions League$|Champions League \(", "Champions League Top Scorer"), (r"Premier League Player of the Season", "Premier League Player of the Season"), (r"PFA Players' Player", "PFA Players' Player of the Year"),
          (r"Pusk", "FIFA Puskas Award"), (r"^Golden Ball", "FIFA Club World Cup Golden Ball"), (r"Serie A Footballer", "Serie A Footballer of the Year (AIC)")]


def award_row(section, region, org, cat, edition, result, extra, cn):
    y = re.search(r"\d{4}", edition)
    year = int(y.group()) if y else None
    name = cat if cat and cat != org else org
    if name in ("World Player of the Year", "Player of the Year", "Best Player of the Year", "Best Player", "Footballer of the Year"):
        name = f"{name} ({org})"
    fifa_poty = name == "World Player of the Year (FIFA)"
    verified = "Single source (Wikipedia)"
    if cn:
        verified = "Unverified: source marks citation needed"
    elif result == "Won" and year:
        for rx, h in XCHECK:
            ys = hy(h)
            if re.search(rx, name) and ys and (year in ys or year + 1 in ys):
                verified = "Cross-checked (2 sources)"
                break
    national = bool(re.search(r"European Championship|Euro All Time|(?<!Club )World Cup|Nations League|UEFA Euro", name + " " + org)) and "Club" not in name
    major = bool(MAJOR.search(name)) or fifa_poty or (section == "Top scorer" and bool(re.search(r"Premier League|La Liga|Serie A|Saudi Pro League|Champions League|Golden Shoe|European Championship", name)))
    won = 1 if result == "Won" else 0
    if section == "Top scorer" and "European Championship" in name and year == 2012:
        result, won, extra = "Joint top scorer", 0, "Joint top scorer with 3 goals. Neither S05 nor S03 lists a Euro 2012 Golden Boot; both list only Euro 2020."
    return dict(achievement_name=name, organisation=org, award_category=section, result_type=result, is_award_won=won, is_major=1 if major else 0, year=edition, year_start=year,
                club_or_country="Portugal" if national else REGION_TEAM.get(region) or team_at(year), competition=region or None, description=extra, official_source="S08", verification_status=verified)


a = wiki("List_of_career_achievements_by_Cristiano_Ronaldo.txt")
sec = a[a.find("== Individual honours =="):a.find("== Records ==")]
heads = [(m.start(), m.group(0).strip("= ")) for m in re.finditer(r"^==+[^=\n]+==+", sec, re.M)]
SECTION = {"Selections for the best player or forward": "Player of the year", "Goal of the competition": "Goal award", "Inclusions in theoretical teams": "Team of the year",
           "Selections for international sportsperson of the year": "Sportsperson of the year", "Selections for national sports personality of the year": "National sports honour",
           "Selections for international sportsperson of the decade or the last 25 years": "Decade and all-time lists", "Miscellaneous": "Special award"}
awards = []
for i, (p, h) in enumerate(heads):
    e = heads[i + 1][0] if i + 1 < len(heads) else len(sec)
    if h in ("Individual honours", "Goalscoring", "Orders", "International man of the match awards"):
        continue
    for cap, rows in W.tables(sec[p:e])[:1]:
        hdr = rows[0]
        region = None
        for r in rows[1:]:
            if len(set(r)) == 1:
                region = r[0]
                continue
            r = r + [""] * (len(hdr) - len(r))
            cn = "[cn]" in " ".join(r)
            r = [x.replace("[cn]", "").strip() for x in r]
            if h == "Miscellaneous" and not re.search(r"FIFA|Union of European|IFFHS|Globe", r[0]):
                continue  # non-football novelty awards are out of scope
            if h in ("Top goalscorer", "Top assist provider"):
                unit = "goals" if h == "Top goalscorer" else "assists"
                for ed in split_years(r[1]):
                    awards.append(award_row("Top scorer" if unit == "goals" else "Top assists", region, r[0], r[0], ed, "Won", f"{r[2]} {unit}" if r[2] else None, cn))
            else:
                for ed in split_years(r[2]):
                    awards.append(award_row(SECTION.get(h, h), region, r[0], r[1], ed, result_of(r[3]), None, cn))
awards = [dict(award_id=f"A{i:03d}", player_id=PLAYER_ID, **r) for i, r in enumerate(awards, 1)]
write("individual_awards.csv", awards)

# ---------------------------------------------------------------- goals
wk_rows = W.tables(wiki("goals.txt"))[1][1][1:]


def wdate(s):
    m = re.match(r"(\d+) (\w+) (\d{4})", s)
    return dt.date(int(m[3]), MONTHS[m[2]], int(m[1]))


agoals = sorted(feed("pd_ronaldo-all-goals.json")["result"]["pageContext"]["goals"], key=lambda g: g["number"])
goals, date_diffs = [], []
for g, w in zip(agoals, wk_rows):
    d = dt.date(int(g["year"]), int(g["month"]), int(g["day"]))
    wd = wdate(w[1])
    m = by_date[d.isoformat()]
    diff = (wd - d).days
    if diff:
        date_diffs.append((g["number"], d.isoformat(), wd.isoformat()))
    assert abs(diff) <= 1, (g["number"], d, wd)
    minute = str(g["goalTime"])
    base = re.match(r"\d+", minute)
    n = int(base.group()) if base else None
    st = g.get("gameState") or ""
    goals.append(dict(
        goal_no=g["number"], match_id=m["match_id"], player_id=PLAYER_ID, match_date=d.isoformat(), season_id=m["season_id"], calendar_year=d.year, team_id=m["team_id"], competition_id=m["competition_id"], opponent=m["opponent"],
        minute=minute, minute_num=n, minute_band=None if n is None else "01-15" if n <= 15 else "16-30" if n <= 30 else "31-45" if n <= 45 else "46-60" if n <= 60 else "61-75" if n <= 75 else "76-90" if n <= 90 else "90+ and extra time",
        body_part={"right": "Right foot", "left": "Left foot", "head": "Header", "other": "Other"}[g["type"]],
        situation={"inside-open-play": "Open play, inside box", "outside-open-play": "Open play, outside box", "penalty": "Penalty", "free-kick": "Direct free kick"}[g["where"]],
        assisted_by=g.get("assistedBy") or None, opponent_goalkeeper=g.get("opponentGoalkeeper") or None, stadium=g.get("stadium") or None, city=g.get("city") or None, country=g.get("country") or None,
        game_state="Level" if st.startswith("dr") else "Leading" if st.startswith("wb") else "Trailing" if st.startswith("lb") else None,
        is_winning_goal=1 if g.get("matchWinner") == "mw" else 0, wikipedia_check="Exact" if diff == 0 else f"Date differs by {diff:+d} day", source_id="S02+S06"))
write("goal_statistics.csv", goals)

# ---------------------------------------------------------------- club level
HIST = [("SPO", "2003-08-12", "Sporting CP", "Senior debut and breakthrough"), ("MU1", "2009-07-01", "Manchester United (first spell)", "Premier League, Champions League, first Ballon d'Or"),
        ("RMA", "2018-07-10", "Real Madrid", "All-time club top scorer; four Champions League titles"), ("JUV", "2021-08-31", "Juventus", "Two Serie A titles; Capocannoniere"),
        ("MU2", "2022-11-22", "Manchester United (second spell)", "Separate career period; ran into the 2022-23 season"), ("NAS", None, "Al Nassr", "Current club; contract to 2027")]
hist_rows = [dict(career_period=0, team_id="SPOB", club="Sporting CP B", country="Portugal", league="Segunda Divisao B", first_match=None, last_match=None, date_left=None, status="Ended; excluded from totals", appearances=2, goals=0, notes="Reserve-team appearances. Wikipedia includes them (club apps 1,111); the official first-team log does not (1,109).", source_id="S05")]
for i, (tid, e, label, note) in enumerate(HIST, 1):
    rows = [m for m in matches if m["team_id"] == tid]
    hist_rows.append(dict(career_period=i, team_id=tid, club=label, country=TEAMS[tid][2], league=TEAMS[tid][3], first_match=rows[0]["match_date"], last_match=rows[-1]["match_date"], date_left=e, status="Current" if tid == "NAS" else "Ended", appearances=len(rows), goals=sum(m["goals"] for m in rows), notes=note, source_id="S01+S05"))
write("club_history.csv", hist_rows)


def club_awards(tid):
    club_name = TEAMS[tid][0].split(" (")[0]
    n = [x for x in awards if x["club_or_country"] == club_name and x["is_award_won"]]
    if tid == "MU1":
        n = [x for x in n if (x["year_start"] or 0) < 2015]
    if tid == "MU2":
        n = [x for x in n if (x["year_start"] or 0) >= 2015]
    return len(n)


club_rows = []
for tid in ("SPO", "MU1", "RMA", "JUV", "MU2", "NAS"):
    rows = [m for m in matches if m["team_id"] == tid]
    club_rows.append(dict(team_id=tid, club=TEAMS[tid][0], **agg(rows), trophies_with_appearance=tcount[tid],
                          trophies_no_appearance=sum(1 for t in trophies if t["team_id"] == tid and not t["counts_as_played"]), individual_awards_won=club_awards(tid), source_id="S01+S17"))
write("club_statistics.csv", club_rows)

comp_rows = []
for (cid, tid), rows in group(matches, "competition_id", "team_id").items():
    comp_rows.append(dict(competition_id=cid, competition=CID[cid][1], competition_type=CID[cid][2], team_id=tid, team=TEAMS[tid][0], **agg(rows),
                          first_match=min(r["match_date"] for r in rows), last_match=max(r["match_date"] for r in rows), source_id="S01+S17"))
comp_rows.sort(key=lambda r: (CID[r["competition_id"]][3], r["competition_id"], r["team_id"]))
write("competition_statistics.csv", comp_rows)


# ---------------------------------------------------------------- international
def streaks(rows):
    out, cur = [], []
    for r in rows + [None]:
        if r and r["goals"] > 0:
            cur.append(r)
        else:
            if len(cur) > 1:
                out.append(cur)
            cur = []
    return sorted(out, key=lambda s: (-len(s), s[0]["match_date"]))


int_rows = []


def irow(group_, item, rows, note=None):
    s = agg(rows)
    int_rows.append(dict(metric_group=group_, item=item, appearances=s["appearances"], starts=s["starts"], minutes_played=s["minutes_played"], goals=s["goals"], assists=s["assists"],
                         pens_scored=s["pens_scored"], pens_missed=s["pens_missed"], hat_tricks=s["hat_tricks"], goals_per_appearance=s["goals_per_appearance"], goals_per_90=s["goals_per_90"],
                         wins=s["wins"], draws=s["draws"], losses=s["losses"], first_match=rows[0]["match_date"], last_match=rows[-1]["match_date"], notes=note, source_id="S01+S07"))


comp_intl = [m for m in intl if m["is_competitive"]]
irow("Career", "All senior caps", intl)
irow("Career", "Competitive caps", comp_intl)
irow("Career", "Friendly caps", [m for m in intl if not m["is_competitive"]], "Senior caps recognised by FIFA; shown separately from competitive totals")
for (y,), r in sorted(group(intl, "calendar_year").items()):
    irow("By calendar year", str(y), r)
for (c,), r in group(intl, "competition_id").items():
    irow("By competition", CID[c][1], r)
for (o,), r in sorted(group(intl, "opponent").items(), key=lambda kv: (-sum(m["goals"] for m in kv[1]), kv[0][0])):
    irow("By opponent", o, r, CONF_OF[o])
for (v,), r in group(intl, "venue_type").items():
    irow("Home, away, neutral", v, r)
for c in CONF:
    r = [m for m in intl if CONF_OF[m["opponent"]] == c]
    irow("By opponent confederation", f"{CONF_REGION[c]} ({c})", r)
for i, s in enumerate(streaks(intl)[:5], 1):
    irow("Scoring streak (consecutive caps)", f"#{i}: {len(s)} caps", s, f"{s[0]['match_date']} to {s[-1]['match_date']}; opponents: " + ", ".join(m["opponent"] for m in s))
for i, s in enumerate(streaks(comp_intl)[:3], 1):
    irow("Scoring streak (consecutive competitive caps)", f"#{i}: {len(s)} caps", s, f"{s[0]['match_date']} to {s[-1]['match_date']}")
capt = [m for m in intl if m["captain"] == 1]
irow("Captaincy (tournament matches only)", "Captain in World Cup and Euro matches", capt, "Whole-career captaincy count is unavailable; this covers matches with line-ups in S09")
write("international_statistics.csv", int_rows)

# ---------------------------------------------------------------- tournaments
award_lines = {}
for x in awards:
    n = (x["achievement_name"] + " " + x["organisation"]).lower()
    k = None
    if "european championship" in n or "uefa euro" in n or re.search(r"\beuro\b", n):
        k = {"2004": "Euro 2004", "2008": "Euro 2008", "2012": "Euro 2012", "2016": "Euro 2016", "2020": "Euro 2020", "2021": "Euro 2020", "2024": "Euro 2024"}.get(str(x["year_start"]))
    elif "world cup" in n and "club" not in n and "qualif" not in n:
        k = f'{x["year_start"]} World Cup'
    if k and x["result_type"] != "Nominated":
        award_lines.setdefault(k, []).append(f'{x["achievement_name"]} ({x["result_type"]})')
RECORDS_T = {"2022 World Cup": "First man to score at five World Cups", "2026 World Cup": "First man to score at six World Cups (FIFA)"}


def position(rows):
    last = max(rows, key=lambda r: r["match_date"])
    st = last["stage"]
    if st == "Final":
        return "Winners" if last["result"] == "W" else "Runners-up"
    if st == "Third-place play-off":
        return "Third place" if last["result"] == "W" else "Fourth place"
    return {"Group stage": "Group stage", "Round of 16": "Round of 16", "Quarter-final": "Quarter-finals", "Semi-final": "Semi-finals", "Round of 32": "Round of 32"}[st]


def t_rows(cid):
    out = []
    for (tn,), rows in group([m for m in matches if m["competition_id"] == cid], "tournament_id").items():
        s = agg(rows)
        top = max(rows, key=lambda r: (r["goals"], r["match_date"]))
        pr = " > ".join(sorted({m["stage"] for m in rows}, key=lambda x: STAGE_ORDER[x]))
        yel = [r["yellow_cards"] for r in rows]
        g_st = lambda st: sum(m["goals"] for m in rows if m["stage"] == st)
        out.append(dict(tournament_id=tn, tournament_year=int(re.search(r"\d{4}", tn).group()), played_year=int(rows[0]["match_date"][:4]), host=HOST[tn], portugal_final_position=position(rows), stage_progression=pr,
                        matches_played=s["appearances"], starts=s["starts"], minutes_played=s["minutes_played"], goals=s["goals"], assists=s["assists"], goal_contributions=s["goals"] + s["assists"],
                        yellow_cards=sum(yel) if all(v is not None for v in yel) else None, red_cards=s["red_cards"], pens_scored=s["pens_scored"], pens_missed=s["pens_missed"], shots=s["shots"], goals_per_90=s["goals_per_90"],
                        goals_group=g_st("Group stage"), goals_round_of_32=g_st("Round of 32"), goals_round_of_16=g_st("Round of 16"), goals_quarter_final=g_st("Quarter-final"), goals_semi_final=g_st("Semi-final"), goals_third_place=g_st("Third-place play-off"), goals_final=g_st("Final"),
                        top_scoring_match=f'{top["goals"]} v {top["opponent"]} ({top["match_date"]})' if top["goals"] else None, player_awards="; ".join(dict.fromkeys(award_lines.get(tn, []))) or None, records_achieved=RECORDS_T.get(tn), source_id="S01+S09"))
    return out


euro, wc = t_rows("EUR"), t_rows("WC")
write("euro_statistics.csv", euro)
write("world_cup_statistics.csv", wc)
TM = ("match_id", "match_date", "tournament_id", "competition_id", "stage", "opponent", "venue_type", "team_score", "opponent_score", "result", "shootout_result", "started", "minutes", "goals", "assists_opta", "pens_scored", "pens_missed", "yellow_cards", "red_cards", "captain", "shots", "shots_on_target", "match_rating", "man_of_the_match")
write("tournament_matches.csv", [dict(**{k: m[k] for k in TM}, opponent_confederation=CONF_OF[m["opponent"]]) for m in matches if m["competition_id"] in ("EUR", "WC")])

# ---------------------------------------------------------------- milestones and records
ms = []


def add(date, typ, cat, text, team=None, comp=None, value=None, src="S01", ver="Computed from match log"):
    ms.append(dict(milestone_id=None, player_id=PLAYER_ID, milestone_date=date, milestone_type=typ, category=cat, description=text, team=team, competition=comp, value=value, source_id=src, verification_status=ver))


XC = "Cross-checked (2 sources)"
add(matches[0]["match_date"], "Milestone", "Debut", f'Senior competitive debut for Sporting CP v {matches[0]["opponent"]}, aged {matches[0]["age_at_match"]:.1f}', "Sporting CP")
for tid in ("MU1", "RMA", "JUV", "MU2", "NAS", "POR"):
    r = [m for m in matches if m["team_id"] == tid]
    add(r[0]["match_date"], "Milestone", "Debut", f'First match for {TEAMS[tid][0]} v {r[0]["opponent"]}', TEAMS[tid][0])
for tid in ("SPO", "MU1", "RMA", "JUV", "MU2", "NAS", "POR"):
    g = next(x for x in goals if x["team_id"] == tid)
    add(g["match_date"], "Milestone", "First goal", f'First goal for {TEAMS[tid][0]} v {g["opponent"]} (career goal {g["goal_no"]})', TEAMS[tid][0], src="S02+S06", ver=XC)
for n in list(range(100, 985, 100)) + [985]:
    g = goals[n - 1]
    add(g["match_date"], "Milestone", "Career goals", f'Career goal {n}, v {g["opponent"]}', TEAMS[g["team_id"]][0], CID[g["competition_id"]][1], n, "S02+S06", XC)
for n in list(range(100, 1343, 100)) + [1343]:
    m = matches[n - 1]
    add(m["match_date"], "Milestone", "Career appearances", f'Official senior appearance {n}, v {m["opponent"]}', TEAMS[m["team_id"]][0], CID[m["competition_id"]][1], n)
for n in (1, 50, 100, 150, 200, 234):
    m = intl[n - 1]
    add(m["match_date"], "Milestone", "Portugal caps", f'Portugal cap {n}, v {m["opponent"]}' + (" (first man to 200 caps, per Guinness)" if n == 200 else ""), "Portugal", CID[m["competition_id"]][1], n, "S01+S15" if n == 200 else "S01")
ig = [g for g in goals if g["team_id"] == "POR"]
for n in (1, 50, 100, 110, 146):
    g = ig[n - 1]
    add(g["match_date"], "Milestone", "Portugal goals", f'Portugal goal {n}, v {g["opponent"]}' + (" (passed Ali Daei's 109 to hold the men's record)" if n == 110 else ""), "Portugal", CID[g["competition_id"]][1], n, "S02+S07+S16" if n == 110 else "S02+S07", XC)
h1 = next(m for m in matches if m["hat_tricks"])
add(h1["match_date"], "Milestone", "Hat-tricks", f'First career hat-trick, v {h1["opponent"]}', TEAMS[h1["team_id"]][0], CID[h1["competition_id"]][1], 1)
ucl = [g for g in goals if g["competition_id"] == "UCL"]
for n in (1, 100, 140):
    g = ucl[n - 1]
    add(g["match_date"], "Milestone", "Champions League goals", f'Champions League goal {n}, v {g["opponent"]}', TEAMS[g["team_id"]][0], "UEFA Champions League", n, "S02+S06", XC)
add("2003-08-12", "Milestone", "Transfer", "Signed by Manchester United", "Manchester United", None, None, "S05", "Single source (Wikipedia)")
add("2009-07-01", "Milestone", "Transfer", "Joined Real Madrid for a world-record fee of GBP 80m", "Real Madrid", None, 80, "S05", "Single source (Wikipedia)")
add("2016-07-10", "Milestone", "Trophy", "Won Euro 2016, Portugal's first major title", "Portugal", "UEFA European Championship", None, "S05+S03", XC)
add("2026-06-23", "Record", "Record", "First man to score at six FIFA World Cups", "Portugal", "FIFA World Cup", 6, "S20+S08", "Verified: official")
add("2026-11-05", "Milestone", "Retirement", "Announced retirement from international football, effective after the November 2026 break", "Portugal", None, None, "S19", "Cross-checked (press)")
recs = W.tables(a[a.find("== Records =="):a.find("== Goalscoring statistics ==")])[0][1]
region = None
for r in recs[1:]:
    if len(set(r)) == 1:
        region = r[0]
        continue
    when = re.sub(r"\{\{Center\|(.*?)\}\}", r"\1", r[0]).strip()
    add(None, "Record", region, f'{r[1].replace("[cn]", "").strip()} [{when}]', src="S08", ver="Single source (Wikipedia)")
ms.sort(key=lambda r: (r["milestone_date"] or "9999", r["category"] or ""))
for i, r in enumerate(ms, 1):
    r["milestone_id"] = f"MS{i:03d}"
write("career_milestones.csv", ms)

# ---------------------------------------------------------------- transfers
tr = lambda i, d, f, t, txt, e, g, ty, n, s: dict(transfer_id=f"TR{i}", date=d, from_club=f, to_club=t, fee_text=txt, fee_eur_m=e, fee_gbp_m=g, transfer_type=ty, notes=n, source_id=s)
write("career_transfers.csv", [
    tr(1, "1997", "C.D. Nacional (youth)", "Sporting CP (youth)", "GBP 1,500", None, 0.0015, "Youth", "Signed at age 12 after a three-day trial", "S05"),
    tr(2, "2003-08-12", "Sporting CP", "Manchester United", "GBP 12m", None, 12, "Permanent", "Rounded press figure; precise amounts vary by outlet", "S05"),
    tr(3, "2009-07-01", "Manchester United", "Real Madrid", "GBP 80m", None, 80, "Permanent", "World-record fee at the time; 1 July is the conventional completion date", "S05"),
    tr(4, "2018-07-10", "Real Madrid", "Juventus", "EUR 100m (reported GBP 99.2m)", 100, 99.2, "Permanent", "Highest fee for a player over 30 and by an Italian club", "S05"),
    tr(5, "2021-08-31", "Juventus", "Manchester United", "EUR 15m over five years plus up to EUR 8m add-ons", 15, None, "Permanent", "Agreement announced 27 August; Juventus confirmed 31 August", "S21+S05"),
    tr(6, "2022-11-22", "Manchester United", "Free agent", "Contract terminated", None, None, "Contract termination", "Terminated after a falling-out with manager Erik ten Hag", "S05"),
    tr(7, "2022-12-30", "Free agent", "Al Nassr", "Free transfer", 0, 0, "Free transfer", "Initial contract to 2025", "S05"),
    tr(8, "2025-06-26", "Al Nassr", "Al Nassr", "Not applicable", None, None, "Contract extension", "Extended to 2027", "S05"),
])

# ---------------------------------------------------------------- profile, overview
write("player_profile.csv", [dict(player_id=PLAYER_ID, full_name="Cristiano Ronaldo dos Santos Aveiro", known_as="Cristiano Ronaldo", date_of_birth="1985-02-05", place_of_birth="Funchal, Madeira, Portugal", nationality="Portuguese", height_m=1.87, height_note="Varies 1.85 to 1.89 by source; FIFA lists 1.85", position="Forward", preferred_foot="Right", current_club="Al Nassr", shirt_number=7, contract_until=2027, club_status="Active", international_status="Retirement announced 5 November 2026, effective after the November 2026 break", youth_clubs="Andorinha (1992-95); Nacional (1995-97); Sporting CP (1997-2002)", data_as_of=LAST_MATCH, retrieved=RETRIEVED, source_id="S05+S19")])
sa, sc, si = agg(matches), agg(club), agg(intl)
wcagg, eu, ua = agg([m for m in matches if m["competition_id"] == "WC"]), agg([m for m in matches if m["competition_id"] == "EUR"]), agg([m for m in matches if m["competition_id"] == "UCL"])
ov = lambda g, m, v, n=None, s="S01": dict(metric_group=g, metric=m, value=v, notes=n, source_id=s, as_of=LAST_MATCH)
write("career_overview.csv", [
    ov("Club", "Total club appearances", sc["appearances"], "Official first-team. Excludes 2 Sporting CP B matches."), ov("Club", "Total club goals", sc["goals"], None, "S01+S06"), ov("Club", "Total club assists (Opta)", sc["assists"], "Broader definitions run higher"), ov("Club", "Total club minutes", sc["minutes_played"]),
    ov("International", "Portugal senior caps", si["appearances"], "Includes 56 FIFA-recognised friendlies"), ov("International", "Portugal senior goals", si["goals"], "Includes 22 in friendlies", "S01+S07+S16"), ov("International", "Portugal assists (Opta)", si["assists"], "S10 reports 45 on a broader definition"), ov("International", "Competitive caps", len(comp_intl)), ov("International", "Competitive goals", sum(m["goals"] for m in comp_intl)),
    ov("Career", "Total appearances", sa["appearances"]), ov("Career", "Total goals", sa["goals"], None, "S01+S06+S10+S11"), ov("Career", "Total assists (Opta)", sa["assists"]), ov("Career", "Total minutes", sa["minutes_played"]), ov("Career", "Competitive appearances (excl. friendlies)", sum(m["is_competitive"] for m in matches)), ov("Career", "Competitive goals (excl. friendlies)", sum(m["goals"] for m in matches if m["is_competitive"])),
    ov("Career", "Hat-tricks", sa["hat_tricks"]), ov("Career", "Penalties scored", sa["pens_scored"], "Shoot-outs excluded"), ov("Career", "Penalties missed", sa["pens_missed"]), ov("Career", "Free-kick goals", sa["free_kick_goals"]), ov("Career", "Headed goals", sa["headed_goals"]), ov("Career", "Red cards (senior)", sa["red_cards"], "12 club, 1 Portugal", "S17+S18"), ov("Career", "Yellow cards", 162, "Press figure at 14 November 2025; scope not stated. Not derivable from match data.", "S18"),
    ov("Honours", "Trophies won with at least one appearance", played_trophies, "See trophies.csv", "S01+S03+S05"), ov("Honours", "Trophies listed by Wikipedia", sum(t["listed_by_wikipedia"] for t in trophies), None, "S05"), ov("Honours", "Trophies listed by tracker", len(trophies), "Includes squad-only titles", "S03"),
    ov("Honours", "Ballon d'Or wins", 5, "2008, 2013, 2014, 2016, 2017", "S05+S03"), ov("Honours", "European Golden Shoe wins", 4, "2007-08, 2010-11, 2013-14, 2014-15", "S05+S03"),
    ov("UEFA Champions League", "Titles", 5, "2007-08, 2013-14, 2015-16, 2016-17, 2017-18", "S05+S03"), ov("UEFA Champions League", "Appearances", ua["appearances"]), ov("UEFA Champions League", "Goals", ua["goals"], "UEFA's official 141 adds one qualifying goal", "S01+S12"),
    ov("FIFA World Cup", "Tournaments", len(wc), "2006 to 2026"), ov("FIFA World Cup", "Appearances", wcagg["appearances"]), ov("FIFA World Cup", "Goals", wcagg["goals"]), ov("FIFA World Cup", "Assists (Opta)", wcagg["assists"]),
    ov("UEFA Euro", "Tournaments", len(euro), "2004 to 2024; Euro 2020 played in 2021"), ov("UEFA Euro", "Appearances", eu["appearances"]), ov("UEFA Euro", "Goals", eu["goals"]), ov("UEFA Euro", "Assists (Opta)", eu["assists"]),
])

# ---------------------------------------------------------------- dimensions
write("dim_player.csv", [dict(player_id=PLAYER_ID, player="Cristiano Ronaldo", date_of_birth="1985-02-05", nationality="Portuguese", position="Forward")])
write("dim_team.csv", [dict(team_id=k, team=v[0], team_type=v[1], team_country=v[2], primary_league=v[3] or None, career_order=v[4], parent_club=v[0].split(" (")[0]) for k, v in TEAMS.items()])
write("dim_competition.csv", [dict(competition_id=c[0], competition=c[1], competition_type=c[2], competition_group=c[3], organiser=c[4], scope=c[5], is_competitive=0 if c[0] == "FRI" else 1, historical_note=HIST_NOTE.get(c[0])) for c in COMP.values()])
seasons = sorted({m["season_id"] for m in matches})
write("dim_season.csv", [dict(season_id=s, season_start_year=int(s[:4]), season_sort=i, age_at_season_start=int(s[:4]) - 1985, clubs=", ".join(dict.fromkeys(TEAMS[m["team_id"]][0] for m in club if m["season_id"] == s)) or None) for i, s in enumerate(seasons, 1)])
nat = {m["opponent"] for m in intl}
write("dim_opponent.csv", [dict(opponent=o, opponent_type="National team" if o in nat else "Club", confederation=CONF_OF.get(o) if o in nat else None, region=CONF_REGION.get(CONF_OF.get(o)) if o in nat else None) for o in sorted({m["opponent"] for m in matches})])
days, d = [], dt.date(2002, 1, 1)
while d <= dt.date(2027, 12, 31):
    days.append(dict(date=d.isoformat(), year=d.year, quarter=(d.month - 1) // 3 + 1, month=d.month, month_name=d.strftime("%B"), month_short=d.strftime("%b"), day_of_week=d.strftime("%A"), decade=f"{d.year // 10 * 10}s", age=int((d - DOB).days / 365.25), is_match_day=1 if d.isoformat() in by_date else 0))
    d += dt.timedelta(1)
write("dim_date.csv", days)
tourn = sorted({m["tournament_id"] for m in matches if m["tournament_id"]})
write("dim_tournament.csv", [dict(tournament_id=t, tournament_type="World Cup" if "World Cup" in t else "Euro" if "Euro" in t else "Nations League" if "Nations" in t else "Confederations Cup", edition_year=int(re.search(r"\d{4}", t).group()), host=HOST.get(t)) for t in tourn])

# ---------------------------------------------------------------- sources
write("data_sources.csv", [dict(source_id=s[0], source_name=s[1], source_tier=s[2], url=s[3] or None, retrieval_date=RETRIEVED, access_status=s[4], used_for=s[5], methodology_notes=s[6]) for s in SOURCES])

# ---------------------------------------------------------------- data quality
Q = []


def chk(area, name, expected, actual, status=None, note=None, src=None):
    status = status or ("PASS" if str(expected) == str(actual) else "FAIL")
    Q.append(dict(check_id=f"Q{len(Q) + 1:03d}", area=area, check_name=name, expected=expected, actual=actual, status=status, note=note, source_id=src))


chk("Reconciliation", "Official senior matches vs Ronaldo Stats", 1343, len(matches), src="S10")
chk("Reconciliation", "Career goals vs Wikipedia goal list", 985, len(wk_rows), src="S06")
chk("Reconciliation", "Career goals in match log vs every-goal feed", sum(m["goals"] for m in matches), len(goals), src="S02")
chk("Reconciliation", "Career goals vs CR7 Counter (2 Nov 2026)", 985, sa["goals"], src="S11")
for tid, exp in (("SPO", 5), ("RMA", 450), ("JUV", 101), ("NAS", 138), ("POR", 146)):
    chk("Reconciliation", f"Goals by team: {TEAMS[tid][0]}", exp, sum(m["goals"] for m in matches if m["team_id"] == tid), src="S05+S10")
chk("Reconciliation", "Goals, Manchester United (both spells)", 145, sum(m["goals"] for m in matches if m["team_id"] in ("MU1", "MU2")), src="S05+S10")
chk("Reconciliation", "Goal-by-goal date match against Wikipedia", 985, 985 - len(date_diffs), "EXPLAINED", f"{len(date_diffs)} goals across {len({d_[1] for d_ in date_diffs})} matches differ by one day, consistent with UTC vs local dating. Goal order agrees. Matches: " + ", ".join(sorted({d_[1] for d_ in date_diffs})), "S06")
wr = [r for c, rows in W.tables(wiki("Cristiano_Ronaldo.txt")) if "by club, season" in c for r in rows]
bad, compared = [], 0
fb = {v[0]: v[6] for v in COMP.values()}
for r in wr:
    if len(r) < 15 or r[0] not in ("Sporting CP", "Manchester United", "Real Madrid", "Juventus", "Al-Nassr") or not re.match(r"\d{4}–\d{2}", r[1]):
        continue
    s = r[1].replace("–", "-")
    name = "Al Nassr" if r[0] == "Al-Nassr" else r[0]
    rows = [m for m in club if TEAMS[m["team_id"]][0].split(" (")[0] == name and m["season_id"] == s]
    for b, ai, gi in (("League", 3, 4), ("NatCup", 5, 6), ("LeagueCup", 7, 8), ("Continental", 9, 10), ("Other", 11, 12)):
        apps, gl = (int(r[ai]) if r[ai].isdigit() else 0), (int(r[gi]) if r[gi].isdigit() else 0)
        sub = [m for m in rows if fb[m["competition_id"]] == b]
        compared += 1
        if (len(sub), sum(m["goals"] for m in sub)) != (apps, gl):
            bad.append(f'{r[0]} {s} {b}: Wikipedia {apps}/{gl} vs log {len(sub)}/{sum(m["goals"] for m in sub)}')
chk("Reconciliation", "Club season-competition cells vs Wikipedia table (apps and goals)", compared, compared - len(bad), None if not bad else "REVIEW", "; ".join(bad) or "All cells agree", "S05")
yr = [r for c, rows in W.tables(wiki("Cristiano_Ronaldo.txt")) if "by national team" in c for r in rows if r[0] == "Portugal" and re.match(r"\d{4}$", r[1])]
badi = []
for r in yr:
    y = int(r[1])
    rows = [m for m in intl if m["calendar_year"] == y]
    ca, fr = [m for m in rows if m["is_competitive"]], [m for m in rows if not m["is_competitive"]]
    v = lambda x: int(x) if x.isdigit() else 0
    log = (len(ca), sum(m["goals"] for m in ca), len(fr), sum(m["goals"] for m in fr))
    if log != (v(r[2]), v(r[3]), v(r[4]), v(r[5])):
        badi.append(f"{y}: Wikipedia {r[2:6]} vs log {log}")
chk("Reconciliation", "Portugal year rows vs Wikipedia (competitive and friendly, apps and goals)", len(yr), len(yr) - len(badi), None if not badi else "REVIEW", "; ".join(badi) or "All years agree", "S05")
ig_rows = next(rows for c, rows in W.tables(wiki("List_of_international_goals_scored_by_Cristiano_Ronaldo.txt")) if len(rows) > 100)[1:]
cap_of = {m["match_date"]: i for i, m in enumerate(intl, 1)}
cap_bad = [f'goal {r[0]}: Wikipedia cap {r[1]} vs log {cap_of[g["match_date"]]}' for g, r in zip(ig, ig_rows) if int(re.sub(r"\D", "", r[1])) != cap_of[g["match_date"]]]
chk("Reconciliation", "Cap number of each international goal vs Wikipedia", 146, 146 - len(cap_bad), None if not cap_bad else "REVIEW", "; ".join(cap_bad[:12]) or "All cap numbers agree", "S07")
chk("Reconciliation", "World Cup goals and caps", "11 goals, 27 apps", f'{wcagg["goals"]} goals, {wcagg["appearances"]} apps', src="S10")
chk("Reconciliation", "Euro goals and caps", "14 goals, 30 apps", f'{eu["goals"]} goals, {eu["appearances"]} apps', src="S10")
chk("Reconciliation", "Red cards all join to a senior match", 13, len(RED) - len(missing_red), src="S17")
ucq = sum(m["goals"] for m in matches if m["competition_id"] == "UCQ")
chk("Discrepancy", "Champions League goals: UEFA 141 vs databases 140", 141, ua["goals"] + ucq, "EXPLAINED", f"140 in the competition proper plus {ucq} qualifying goal (Debrecen, 9 August 2005). UEFA counts qualifying; most databases do not. Dashboard shows 140 with the 141 note.", "S12")
chk("Discrepancy", "Real Madrid goals: club 451 vs databases 450", 451, 450, "EXPLAINED", "One goal v Real Sociedad, 18 September 2010. La Liga and UEFA credit Pepe; Marca credits Ronaldo. The club's 451 and its La Liga 312 (vs 311) are consistent with counting it, though the club does not state this. Dashboard uses 450.", "S13+S05")
chk("Discrepancy", "Club appearances: Wikipedia 1,111 vs match log 1,109", 1111, sc["appearances"], "EXPLAINED", "Wikipedia adds 2 Sporting CP B matches. Reserve football is held out of first-team totals.", "S05")
chk("Discrepancy", "International caps: Guinness 233 vs match log 234", 233, si["appearances"] - 1, "EXPLAINED", "Guinness page runs to 6 July 2026; the Wales match on 24 September 2026 is cap 234.", "S15")
chk("Discrepancy", "Assists: 291 (Ronaldo Stats) vs 261 (Opta)", 291, sa["assists"], "EXPLAINED", f'Opta 261 is the default. The match feed\'s wider definition gives {sa["assists_all_definitions"]}; Ronaldo Stats gives 291 (Portugal 45 vs Opta 37). The definitions differ, so none is simply wrong.', "S01+S10")
chk("Discrepancy", "Trophies: 37 tracker, 35 Wikipedia, 34 with an appearance", 37, played_trophies, "EXPLAINED", "No recorded appearance in Supertaca 2002, Community Shield 2008 or UEFA Super Cup 2016. Wikipedia omits the latter two. Dashboard headline uses trophies with an appearance.", "S03+S05")
chk("Discrepancy", "Red cards: ESPN 14 vs senior 13", 14, sa["red_cards"], "EXPLAINED", "ESPN's list includes Portugal U17 v France U17, 28 April 2002: youth football.", "S17+S18")
chk("Discrepancy", "Hat-tricks: match log 67 vs detailed list 66", 67, len(feed("pd_detailed-stats_hat-tricks.json")["result"]["data"]["allSheetRonaldoHatTricks"]["edges"]), "REVIEW", "Same provider disagrees with itself. Match-log value is used.", "S01")
chk("Discrepancy", "Free-kick goals: match log 65 vs detailed list 64", 65, len(feed("pd_detailed-stats_free-kicks.json")["result"]["data"]["allSheetRonaldoFreeKicks"]["edges"]), "EXPLAINED", "Goal-level feed also gives 65, so 65 is used; the 64-row list looks one row short.", "S01+S02")
chk("Discrepancy", "1,000th senior appearance: BBC 22 February 2020 vs match log", "2020-02-22", matches[999]["match_date"], "EXPLAINED" if matches[999]["match_date"] != "2020-02-22" else "PASS", "BBC's count includes the 2 Sporting CP B matches; without them appearance 1,000 falls two games later.", "S05")
chk("Internal logic", "Starts + substitute = appearances", sa["appearances"], sa["starts"] + sa["substitute_appearances"])
chk("Internal logic", "Left + right + head + other = goals", sa["goals"], sa["left_foot_goals"] + sa["right_foot_goals"] + sa["headed_goals"] + sum(m["other_goals"] for m in matches))
chk("Internal logic", "Goal situations cover all goals", 985, sum(1 for g in goals if g["situation"]))
chk("Internal logic", "Unique match ids", 1343, len({m["match_id"] for m in matches}))
chk("Internal logic", "Matches without a valid competition or team key", 0, sum(1 for m in matches if m["competition_id"] not in CID or m["team_id"] not in TEAMS))
chk("Internal logic", "National opponents without a confederation", 0, sum(1 for m in intl if m["opponent"] not in CONF_OF))
chk("Internal logic", "Season table rolls up to match log (club apps)", sc["appearances"], sum(r["appearances"] for r in season_rows))
chk("Internal logic", "Season table rolls up to match log (club goals)", sc["goals"], sum(r["goals"] for r in season_rows))
chk("Internal logic", "Tournament line-ups that fail to join a match", 0, len(unjoined), None, ", ".join(unjoined) or None, "S09")
tn = [m for m in matches if m["competition_id"] in ("EUR", "WC")]
miss = [m["match_date"] for m in tn if m["yellow_cards"] is None]
chk("Coverage", "World Cup and Euro matches with a line-up (cards, captain)", len(tn), len(tn) - len(miss), None if not miss else "REVIEW", "Missing: " + ", ".join(miss) if miss else "Complete", "S09")
WHY = {"yellow_cards": "Yellows exist only for World Cup and Euro matches. Transfermarkt and FBref, which carry season cards, could not be reached.", "captain": "Available only for World Cup and Euro matches.", "shots": "Partial before 2009-10.", "shots_on_target": "Partial before 2009-10.", "key_passes": "Partial before 2009-10.", "xg": "Recent seasons only.", "xa": "Recent seasons only.", "match_rating": "Partial before 2009-10.", "man_of_the_match": "Partial."}
for fld, why in WHY.items():
    n = sum(1 for m in matches if m[fld] is not None)
    chk("Completeness", f"match_statistics.{fld}", 1343, n, "INFO", f"{n / 13.43:.1f}% populated. {why} Missing values are NULL, not zero.", "S01")
for fld in ("assisted_by", "opponent_goalkeeper", "stadium", "minute"):
    n = sum(1 for g in goals if g[fld])
    chk("Completeness", f"goal_statistics.{fld}", 985, n, "INFO" if n < 985 else "PASS", "NULL means no assister (solo, penalty, free kick) or unknown." if fld == "assisted_by" else None, "S02")
chk("Coverage", "Tier 1 cross-checks performed", "FIFA, UEFA, Real Madrid, Man Utd, Juventus, Saudi Pro League", "UEFA, FIFA, Real Madrid, Guinness", "INFO", "Man Utd, Juventus and Saudi Pro League sites were not used. Transfermarkt, FBref, WorldFootball and 11v11 could not be reached, so cross-checks rely on Wikipedia, Ronaldo Stats and CR7 Counter.")
chk("Coverage", "Independence of cross-checks", "Independent", "Partly independent", "INFO", "S01 is compiled mainly from Opta, S06 cites FBref, S05 cites WorldFootball and Soccerway. These may share upstream providers, so agreement is strong evidence, not proof.")
chk("Coverage", "Data freshness (last match in log)", LAST_MATCH, matches[-1]["match_date"], None, "Portugal play Denmark on 14 November and Norway on 17 November 2026; totals may change.", "S01+S19")
chk("Coverage", "Yellow cards career total", 162, 162, "REVIEW", "Single press source dated 14 November 2025, scope not stated. Stored in career_overview.csv only.", "S18")
write("data_quality_report.csv", Q)

c = collections.Counter(q["status"] for q in Q)
print("\nQuality:", dict(c))
for q in Q:
    if q["status"] in ("FAIL", "REVIEW"):
        print(" ", q["check_id"], q["status"], q["check_name"], "|", q["expected"], "vs", q["actual"], "|", (q["note"] or "")[:260])
print("line-ups", len(lineup_hits), "unjoined", unjoined, "| tournament yellows", sum(m["yellow_cards"] or 0 for m in matches), "| captain matches", len(capt))
