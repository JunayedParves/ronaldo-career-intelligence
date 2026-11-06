"""Generates the dashboard page and the store documents used to publish it."""
import html, json, os, sys, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from story import story_page
from icons import icon, icon_for

HERE = os.path.dirname(os.path.abspath(__file__))
STAMP = {"via": "claude", "at": "2026-11-06T12:00:00Z"}
UPDATED = {"at": "2026-11-06T12:00:00Z", "by": "Claude, from data/csv in the CR project"}


def val(source, field, base="", follow="", fmt="", tag="b"):
    a = f'data-draw="val" data-source="{source}" data-field="{field}"'
    if base:
        a += f' data-where="{html.escape(base)}" data-base="{html.escape(base)}"'
    if follow:
        a += f' data-follow="{follow}"'
    if fmt:
        a += f' data-fmt="{fmt}"'
    return f"<{tag} {a}>—</{tag}>"


def kpi(label, value, note=""):
    n = f"<small>{note}</small>" if note else ""
    return f'<div class="kpi"><i class="kpi-ic">{icon_for(label)}</i><span>{label}</span>{value}{n}</div>'


def strong(*a, **k):
    return val(*a, tag="strong", **k)


def ov(metric, fmt="int", tag="strong"):
    return val("overview", "value", base=f"metric={metric}", fmt=fmt, tag=tag)


def table(tid, draw, source, key, cols, attrs=""):
    th = "".join(f'<th data-field="{f}">{l}</th>' for f, l in cols)
    return f'<div class="scroll"><table id="{tid}" data-source="{source}" data-row-key="{key}"><thead><tr>{th}</tr></thead><tbody data-draw="t-{draw}" {attrs}></tbody></table></div>'


def card(title, note, body, cid=""):
    i = f' id="{cid}"' if cid else ""
    return f'<section class="card"{i}><h4>{icon_for(title)}{title}</h4><p>{note}</p>{body}</section>'


def chart(name, source, attrs=""):
    return f'<div class="chart" data-draw="{name}" data-source="{source}" {attrs}></div>'


def search(id_, label):
    return f'<div class="tools"><input id="{id_}" type="search" data-search placeholder="{label}" aria-label="{label}"></div>'


PAGE_ICON = {"summary": "ball", "progression": "up", "clubs": "scale", "honours": "trophy", "quality": "check"}
CREST = {"SPO": "crest_SPO", "MU1": "crest_MU", "MU2": "crest_MU", "RMA": "crest_RMA", "JUV": "crest_JUV", "NAS": "crest_NAS", "POR": "crest_POR"}


def page(pid, title, sub, body, filters="", hidden=True, club=None, eyebrow=""):
    h = " hidden" if hidden else ""
    f = f'<div class="filters">{filters}</div>' if filters else ""
    if club:
        crest = f'<img class="club-crest" data-draw="photo" data-img="{CREST[club]}" alt="{html.escape(eyebrow)} crest">'
        return (f'<section class="pg themed" id="{pid}" role="tabpanel" data-club="{club}"{h}><div class="club-banner"><i class="sheen" aria-hidden="true"></i>{icon("ball", "float f0")}{icon("star", "float f1")}{crest}'
                f'<div class="club-title"><p class="eyebrow">{eyebrow}</p><h3>{title}</h3><p>{sub}</p></div>{f}</div>{body}</section>')
    return f'<section class="pg" id="{pid}" role="tabpanel"{h}><div class="pg-top"><i class="sheen" aria-hidden="true"></i><span class="pg-icon">{icon(PAGE_ICON[pid])}</span><div class="pg-words"><h3>{title}</h3><p>{sub}</p></div>{f}</div>{body}</section>'


TEAM_OPTS = '<option value="All">All teams</option><option value="SPO">Sporting CP</option><option value="MU1">Man Utd 2003-09</option><option value="RMA">Real Madrid</option><option value="JUV">Juventus</option><option value="MU2">Man Utd 2021-22</option><option value="NAS">Al Nassr</option><option value="POR">Portugal</option>'
F = "team:teamS,scope:scopeS"
pages = []
credits = json.load(open(os.path.join(HERE, "images", "credits.json"), encoding="utf8"))
pages.append(story_page(val, credits))

# Summary
pages.append(page("summary",
    f'{val("totals","goals",base="team=All&scope=All",fmt="int")} goals in {val("totals","appearances",base="team=All&scope=All",fmt="int")} matches: one every {val("totals","minutes_per_goal",base="team=All&scope=All")} minutes',
    "Every official senior match for club and country. Portugal friendlies are full caps, so they count here; choose Competitive only to remove them.",
    '<div class="kpis">' +
    kpi("Appearances", strong("totals", "appearances", follow=F, fmt="int")) +
    kpi("Goals", strong("totals", "goals", follow=F, fmt="int")) +
    kpi("Assists", strong("totals", "assists", follow=F, fmt="int"), "Opta definition") +
    kpi("Goals per 90", strong("totals", "goals_per_90", follow=F)) +
    kpi("Trophies", ov("Trophies won with at least one appearance"), "All teams, with an appearance") +
    kpi("Ballons d'Or", ov("Ballon d'Or wins"), "All teams") + "</div>" +
    '<div class="grid wide">' + card("Goals by season", "Each bar stacks the goals scored for each team that season.", chart("c-season-team", "season_team"), "goals-season") +
    card("Goals by team", "Manchester United spells are counted apart.", chart("c-team-goals", "totals"), "goals-team") + "</div>" +
    card("Key moments", "Debuts, first goals, round-number goals and caps, newest first.", search("sMoments", "Search moments") + table("tMoments", "moments", "milestones", "milestone_id", [("milestone_date", "Date"), ("category", "Category"), ("description", "Moment"), ("team", "Team"), ("verification_status", "Checked")]), "moments"),
    filters=f'<label>Team<select id="fTeam" class="dash-select" data-param="teamS">{TEAM_OPTS}</select></label><label>Matches<select id="fScope" class="dash-select" data-param="scopeS"><option value="All">All official</option><option value="Competitive">Competitive only</option></select></label>',
    ))

# Progression
pages.append(page("progression",
    f'{val("peaks","peak_goals")} club goals at the {val("peaks","peak_season")} peak, and still {val("peaks","recent_goals")} in {val("peaks","recent_season")}',
    "How output changed with age, from a first-team debut at 17 to the present.",
    '<div class="kpis">' +
    kpi("Best club season", strong("peaks", "peak_goals"), val("peaks", "peak_season", tag="span")) +
    kpi("Best calendar year", strong("peaks", "peak_year_goals"), val("peaks", "peak_year", tag="span")) +
    kpi("Goals from age 30", strong("peaks", "goals_after_30", fmt="int"), val("peaks", "share_after_30", tag="span")) +
    kpi("Minutes per goal", strong("totals", "minutes_per_goal", base="team=All&scope=All"), "Whole career") + "</div>" +
    '<div class="grid">' + card("Running total of goals", "Goals added up by age.", chart("c-cumulative", "by_age"), "cumulative") +
    card("Goals per 90 by age", "Rate across all minutes played at that age.", chart("c-age-rate", "by_age"), "rate-age") + "</div>" +
    '<div class="grid">' + card("Calendar-year record", "Club and country.", table("tYears", "years", "by_year", "year", [("year", "Year"), ("appearances", "Apps"), ("goals", "Goals"), ("assists", "Assists"), ("minutes", "Minutes"), ("goals_per_90", "Per 90")]), "years") +
    card("Career moves", "Transfers, contract changes and fees as reported.", table("tMoves", "moves", "transfers", "transfer_id", [("date", "Date"), ("from_club", "From"), ("to_club", "To"), ("fee_text", "Fee"), ("transfer_type", "Type")]), "moves") + "</div>",
    filters='<label>Show<select id="fAge" class="dash-select" data-param="ageGroup"><option value="All">Club and country</option><option value="Club">Club</option><option value="Portugal">Portugal</option></select></label>'))

# Club comparison
pages.append(page("clubs",
    f'Real Madrid was the peak: {val("clubs","goals_per_90",base="team_id=RMA")} goals per 90 across {val("clubs","appearances",base="team_id=RMA")} matches',
    "Spells differ a lot in length, so compare them by rate as well as total. Manchester United's two spells are separate.",
    '<div class="grid">' + card("Goals per 90 by spell", "The fairest single comparison.", chart("c-rate-club", "clubs"), "rate-club") +
    card("Volume against rate", "Bubble size shows total goals.", chart("c-bubbles", "clubs"), "bubbles") + "</div>" +
    card("Full spell comparison", "Yellow cards are left out: they are only known for World Cup and Euro matches.", table("tClubs", "club-compare", "clubs", "team_id", [("club", "Club"), ("appearances", "Apps"), ("goals", "Goals"), ("assists", "Assists"), ("minutes_played", "Minutes"), ("goals_per_90", "Per 90"), ("hat_tricks", "Hat-tricks"), ("pens_scored", "Pens"), ("pens_missed", "Pens missed"), ("free_kick_goals", "Free kicks"), ("headed_goals", "Headers"), ("winning_goals", "Winners"), ("red_cards", "Reds"), ("trophies_with_appearance", "Trophies")]), "club-table")))

# Club pages
CLUBS = [
    ("sporting", "SPO", "Sporting CP", lambda v: f'{v("appearances")} matches and {v("goals")} goals: the breakthrough at Sporting', "First-team debut in the 2002-03 season. Two Sporting B matches are held out of these totals."),
    ("manutd1", "MU1", "Man Utd 2003-09", lambda v: f'{v("goals")} goals and a first Ballon d\'Or at Old Trafford', "First spell at Manchester United."),
    ("realmadrid", "RMA", "Real Madrid", lambda v: f'{v("goals")} goals in {v("appearances")} matches: more goals than games', "Real Madrid's own record says 451, counting a goal against Real Sociedad that La Liga and UEFA credit to Pepe."),
    ("juventus", "JUV", "Juventus", lambda v: f'{v("goals")} goals in {v("appearances")} matches, with back-to-back Serie A titles', "Includes the one Serie A match of 2021-22 before he left."),
    ("manutd2", "MU2", "Man Utd 2021-22", lambda v: f'{v("goals")} goals in {v("appearances")} matches on the return to Old Trafford', "Second spell, which ran into the 2022-23 season."),
    ("alnassr", "NAS", "Al Nassr", lambda v: f'{v("goals")} goals in {v("appearances")} matches and a first Saudi title', "Current club. The 2026-27 season is still in progress."),
]
for pid, t, name, title, sub in CLUBS:
    v = lambda f, t=t: val("clubs", f, base=f"team_id={t}", fmt="int")
    fw = f"season_id:season{t},competition_id:comp{t}"
    base = f"team_id={t}"
    pages.append(page(pid, title(v), sub,
        '<div class="kpis">' +
        kpi("Appearances", strong("club_rollup", "appearances", base=base, follow=fw, fmt="int")) +
        kpi("Goals", strong("club_rollup", "goals", base=base, follow=fw, fmt="int")) +
        kpi("Assists", strong("club_rollup", "assists", base=base, follow=fw, fmt="int"), "Opta definition") +
        kpi("Minutes", strong("club_rollup", "minutes_played", base=base, follow=fw, fmt="int")) +
        kpi("Goals per 90", strong("club_rollup", "goals_per_90", base=base, follow=fw)) +
        kpi("Trophies", strong("clubs", "trophies_with_appearance", base=base), "Whole spell") + "</div>" +
        '<div class="grid">' + card("Goals by season", "The peak season is highlighted.", chart("c-club-season", "club_rollup", f'data-team="{t}"')) +
        card("Goals by competition", "For the season picked above.", chart("c-club-comp", "club_rollup", f'data-team="{t}"')) +
        card("How the goals came", "For the season and competition picked above.", chart("c-club-type", "goal_types", f'data-team="{t}"')) + "</div>" +
        '<div class="grid">' + card("Season record", "One row for each season and competition.", table(f"tS{t}", "club-seasons", "seasons", "team_id,season_id,competition_id", [("season_id", "Season"), ("competition", "Competition"), ("appearances", "Apps"), ("starts", "Starts"), ("minutes_played", "Minutes"), ("goals", "Goals"), ("assists", "Assists"), ("pens_scored", "Pens"), ("pens_missed", "Missed"), ("red_cards", "Reds"), ("goals_per_90", "Per 90")], f'data-team="{t}"')) +
        card("Trophies", "Each title, and whether the match log shows him playing.", table(f"tT{t}", "club-trophies", "trophies", "trophy_id", [("season_year", "Season"), ("trophy_name", "Trophy"), ("ronaldo_participation_status", "His part")], f'data-team="{t}"')) + "</div>",
        filters=f'<label>Season<select id="fS{t}" class="dash-select" data-draw="club-season" data-source="club_rollup" data-team="{t}" data-param="season{t}" aria-label="Season"></select></label><label>Competition<select id="fC{t}" class="dash-select" data-draw="club-comp" data-source="club_rollup" data-team="{t}" data-param="comp{t}" aria-label="Competition"></select></label>', club=t, eyebrow=name))

# Portugal
pages.append(page("portugal",
    f'{ov("Portugal senior goals",tag="b")} goals in {ov("Portugal senior caps",tag="b")} caps: the men\'s international record',
    "He announced his international retirement on 5 November 2026, effective after the November break, so these totals may still change.",
    '<div class="kpis">' +
    kpi("Caps", ov("Portugal senior caps")) + kpi("Goals", ov("Portugal senior goals")) + kpi("Assists", ov("Portugal assists (Opta)"), "Opta definition") +
    kpi("Competitive caps", ov("Competitive caps")) + kpi("Competitive goals", ov("Competitive goals")) +
    kpi("Longest scoring run", strong("intl", "appearances", base="metric_group=Scoring streak (consecutive caps)&item=#1: 7 caps"), "Consecutive caps") + "</div>" +
    '<div class="grid wide">' + card("Goals by calendar year", "The peak year is highlighted.", chart("c-intl-year", "intl"), "intl-year") +
    card("Goals by opponent region", "Grouped by the opponent's confederation.", chart("c-intl-region", "intl"), "intl-region") + "</div>" +
    '<div class="grid">' + card("Goals by competition", "Friendlies are shown as their own line.", chart("c-intl-comp", "intl"), "intl-comp") +
    card("Home, away and neutral", "Portugal's status in the match.", chart("c-intl-venue", "intl"), "intl-venue") + "</div>" +
    '<div class="grid">' + card("Opponents", "Sort any column to see most-played or most-scored-against.", search("sOpp", "Search opponents") + table("tOpp", "opponents", "intl", "metric_group,item", [("item", "Opponent"), ("notes", "Confederation"), ("appearances", "Caps"), ("goals", "Goals"), ("assists", "Assists"), ("wins", "Won"), ("draws", "Drawn"), ("losses", "Lost")]), "opponents") +
    card("Longest scoring runs", "Consecutive caps with a goal.", table("tStreak", "streaks", "intl", "metric_group,item", [("item", "Run"), ("goals", "Goals"), ("first_match", "From"), ("last_match", "To"), ("notes", "Detail")]), "streaks") + "</div>", club="POR", eyebrow="Portugal"))


def tourn(pid, comp, ds, label, title, sub):
    fw = "tournament_id:" + ("edEUR" if comp == "EUR" else "edWC")
    base = f"comp={comp}"
    p = "edEUR" if comp == "EUR" else "edWC"
    extra = [("shots", "Shots")] if comp == "WC" else []
    pages.append(page(pid, title, sub,
        '<div class="kpis">' +
        kpi("Tournaments", strong("tourn_totals", "tournaments", base=base, follow=fw)) +
        kpi("Matches", strong("tourn_totals", "matches", base=base, follow=fw)) +
        kpi("Goals", strong("tourn_totals", "goals", base=base, follow=fw)) +
        kpi("Assists", strong("tourn_totals", "assists", base=base, follow=fw), "Opta definition") +
        kpi("Minutes", strong("tourn_totals", "minutes", base=base, follow=fw, fmt="int")) +
        kpi("Yellow cards", strong("tourn_totals", "yellow_cards", base=base, follow=fw)) +
        kpi("Red cards", strong("tourn_totals", "red_cards", base=base, follow=fw)) + "</div>" +
        '<div class="grid">' + card("Goals by tournament", "The highest total is highlighted.", chart("c-edition-goals", ds)) +
        card("Goals and assists", "Direct contribution at each tournament.", chart("c-edition-both", ds)) +
        card("Goals by stage", "For the tournament picked above.", chart("c-stage", "stage_goals", f'data-comp="{comp}" data-param="{p}"')) +
        card("Goals by opponent", "For the tournament picked above.", chart("c-opp", "opp_goals", f'data-comp="{comp}" data-param="{p}"')) + "</div>" +
        card("Tournament comparison", "Portugal's finish and his contribution at each tournament.", table(f"tSum{comp}", "tourn-sum", ds, "tournament_id", [("tournament_id", "Tournament"), ("host", "Host"), ("portugal_final_position", "Portugal finished"), ("stage_progression", "Stages reached"), ("matches_played", "Apps"), ("starts", "Starts"), ("minutes_played", "Minutes"), ("goals", "Goals"), ("assists", "Assists"), ("yellow_cards", "Yellows"), ("red_cards", "Reds"), ("pens_scored", "Pens"), ("top_scoring_match", "Best match"), ("player_awards", "Awards"), ("records_achieved", "Records")])) +
        card("Match by match", "For the tournament picked above, newest first.", table(f"tM{comp}", "tourn-matches", "tmatches", "match_id", [("match_date", "Date"), ("tournament_id", "Tournament"), ("stage", "Stage"), ("opponent", "Opponent"), ("team_score", "Portugal"), ("opponent_score", "Opp."), ("result", "Result"), ("shootout_result", "Shoot-out"), ("started", "Started"), ("minutes", "Minutes"), ("goals", "Goals"), ("assists_opta", "Assists"), ("yellow_cards", "Yellow")] + extra + [("match_rating", "Rating")], f'data-comp="{comp}" data-param="{p}"')),
        filters=f'<label>Tournament<select id="fEd{comp}" class="dash-select" data-draw="edition" data-source="{ds}" data-param="{p}" aria-label="Tournament"></select></label>', club="POR", eyebrow=label))


tourn("euro", "EUR", "euro", "Euro",
      f'{val("tourn_totals","goals",base="comp=EUR&tournament_id=All")} goals across {val("tourn_totals","tournaments",base="comp=EUR&tournament_id=All")} Euros, including Portugal\'s first major title',
      "Euro 2020 was played in 2021 and keeps its official name. Euro goals and caps are counted apart from all other internationals.")
tourn("worldcup", "WC", "wc", "World Cup",
      f'{val("tourn_totals","goals",base="comp=WC&tournament_id=All")} goals at {val("tourn_totals","tournaments",base="comp=WC&tournament_id=All")} World Cups, scoring at every one',
      "This includes the 2026 World Cup. World Cup goals and caps are counted apart from qualifiers and friendlies.")

# Honours
pages.append(page("honours",
    f'{val("honour_counts","played")} trophies with an appearance, {ov("Ballon d\'Or wins",tag="b")} Ballons d\'Or, {ov("European Golden Shoe wins",tag="b")} Golden Shoes',
    "Team titles only count where the match log shows him playing. Awards won are kept apart from nominations and placings.",
    '<div class="kpis">' +
    kpi("Trophies with an appearance", strong("honour_counts", "played")) +
    kpi("No recorded appearance", strong("honour_counts", "no_appearance"), "Listed by a source, not counted") +
    kpi("Ballons d'Or", ov("Ballon d'Or wins")) + kpi("Golden Shoes", ov("European Golden Shoe wins")) +
    kpi("Major awards won", strong("honour_counts", "major_won")) +
    kpi("All awards won", strong("honour_counts", "awards_won", fmt="int")) + "</div>" +
    '<div class="grid">' + card("Trophies by team", "With at least one appearance.", chart("c-trophy-team", "trophy_team"), "trophy-team") +
    card("Awards won by type", "Nominations and placings are not counted.", chart("c-award-cat", "award_cat"), "award-cat") + "</div>" +
    '<div class="grid">' + card("Trophy cabinet", "Every title a source lists, with his part in it.", table("tTrophies", "trophies", "trophies", "trophy_id", [("season_year", "Season"), ("trophy_name", "Trophy"), ("team", "Team"), ("ronaldo_participation_status", "His part"), ("verification_status", "Checked")]), "trophies") +
    card("Ballon d'Or record", "Wins and every recorded placing.", table("tBallon", "ballon", "awards", "award_id", [("year", "Year"), ("achievement_name", "Award"), ("result_type", "Result"), ("club_or_country", "Team"), ("verification_status", "Checked")]), "ballon") + "</div>" +
    card("All awards", "Filter by result to separate wins from nominations.", '<div class="tools"><input id="sAwards" type="search" data-search placeholder="Search awards" aria-label="Search awards"><select id="fAward" class="dash-select" data-param="awardResult" aria-label="Result"><option value="All">All results</option><option value="Won">Won</option><option value="Nominated">Nominated</option><option value="Shortlisted">Shortlisted</option><option value="Other">Placings and selections</option></select></div>' + table("tAwards", "awards", "awards", "award_id", [("year", "Year"), ("achievement_name", "Award"), ("organisation", "Organisation"), ("award_category", "Type"), ("result_type", "Result"), ("club_or_country", "Team"), ("description", "Detail"), ("verification_status", "Checked")]), "awards") +
    card("Records", "As listed on Wikipedia, which is the only source for these rows.", search("sRecords", "Search records") + table("tRecords", "records", "milestones", "milestone_id", [("category", "Group"), ("description", "Record"), ("verification_status", "Checked")]), "records")))

# Quality
pages.append(page("quality",
    f'{val("quality_counts","pass")} checks passed, {val("quality_counts","explained")} differences explained, {val("quality_counts","review")} still open',
    "All goals match a second, separate list. Where sources disagree, the reason is recorded here.",
    '<div class="kpis">' +
    kpi("Passed", strong("quality_counts", "pass")) + kpi("Explained", strong("quality_counts", "explained")) +
    kpi("Open", strong("quality_counts", "review")) + kpi("Coverage notes", strong("quality_counts", "info")) +
    kpi("Failed", strong("quality_counts", "fail")) + kpi("Sources reached", strong("quality_counts", "sources_used")) +
    kpi("Sources blocked", strong("quality_counts", "sources_blocked")) + "</div>" +
    '<div class="grid">' + card("Checks by area", "What was tested, and how it came out.", chart("c-quality-area", "quality_area"), "quality-area") +
    card("What to keep in mind", "These change how some figures should be read.", '<ul class="gaps"><li>Yellow cards are known only for World Cup and Euro matches. Elsewhere they are blank, not zero.</li><li>Transfermarkt, FBref, WorldFootball and 11v11 could not be reached.</li><li>Most awards rest on Wikipedia alone. Each row says how it was checked.</li><li>Hat-tricks remain open: the provider\'s match log and its own list disagree by one.</li><li>The sources may share upstream data, so agreement is strong evidence rather than proof.</li></ul>', "gaps") + "</div>" +
    card("Every check", "Filter by outcome or search for a figure.", '<div class="tools"><input id="sChecks" type="search" data-search placeholder="Search checks" aria-label="Search checks"><select id="fQuality" class="dash-select" data-param="qualityStatus" aria-label="Outcome"><option value="All">All outcomes</option><option value="PASS">Passed</option><option value="EXPLAINED">Explained</option><option value="REVIEW">Open</option><option value="INFO">Coverage notes</option></select></div>' + table("tChecks", "checks", "quality", "check_id", [("area", "Area"), ("check_name", "Check"), ("expected", "Expected"), ("actual", "Actual"), ("status", "Outcome"), ("note", "Note")]), "checks") +
    card("Sources", "Reached and blocked sources, with what each was used for.", table("tSources", "sourcesList", "sources", "source_id", [("source_name", "Source"), ("source_tier", "Tier"), ("access_status", "Access"), ("used_for", "Used for"), ("methodology_notes", "Method")]), "sources")))

TABS = [("story", "The story"), ("summary", "Summary"), ("progression", "Progression"), ("clubs", "Compare clubs"), ("sporting", "Sporting CP"), ("manutd1", "Man Utd 2003-09"), ("realmadrid", "Real Madrid"), ("juventus", "Juventus"), ("manutd2", "Man Utd 2021-22"), ("alnassr", "Al Nassr"), ("portugal", "Portugal"), ("euro", "Euro"), ("worldcup", "World Cup"), ("honours", "Honours"), ("quality", "Data quality")]
TAB_MARK = {"story": "book", "summary": "ball", "progression": "up", "clubs": "scale", "euro": "medal", "worldcup": "globe", "honours": "trophy", "quality": "check"}
TAB_CREST = {"sporting": "SPO", "manutd1": "MU1", "realmadrid": "RMA", "juventus": "JUV", "manutd2": "MU2", "alnassr": "NAS", "portugal": "POR"}
mark = lambda i: f'<img class="tab-crest" data-draw="photo" data-img="{CREST[TAB_CREST[i]]}" alt="">' if i in TAB_CREST else icon(TAB_MARK[i])
tabs = "".join(f'<button type="button" role="tab" aria-controls="{i}" aria-selected="{"true" if n == 0 else "false"}">{mark(i)}<span>{l}</span></button>' for n, (i, l) in enumerate(TABS))
asof = val("overview", "as_of", base="metric=Total goals")
# Images travel as data URLs in script files of their own, each under the store's size limit.
web = os.path.join(HERE, "images", "web")
keep = ["crest_SPO.png", "crest_MU.png", "crest_RMA.png", "crest_JUV.png", "crest_NAS.png", "crest_POR.png", "madeira.jpg", "sporting.jpg", "manutd_b.jpg", "realmadrid.jpg", "euro2016.jpg", "juventus.jpg", "return.jpg", "alnassr.jpg", "wc2026.jpg", "statue.jpg", "siuu_still.jpg", "siuu.webp"]
bundles, cur, size = [], {}, 0
for n in keep:
    mime = {"png": "image/png", "jpg": "image/jpeg", "webp": "image/webp"}[n.rsplit(".", 1)[1]]
    uri = f"data:{mime};base64," + base64.b64encode(open(os.path.join(web, n), "rb").read()).decode()
    if size + len(uri) > 220000:
        bundles.append(cur)
        cur, size = {}, 0
    cur[n.rsplit(".", 1)[0]] = uri
    size += len(uri)
bundles.append(cur)
image_files = []
for i, b in enumerate(bundles, 1):
    name = f"img{i}.js"
    open(os.path.join(HERE, name), "w", encoding="utf8").write("window.CRX_IMG = Object.assign(window.CRX_IMG || {}, " + json.dumps(b) + ");\n")
    image_files.append(name)
img_tags = "".join(f'<script src="{n}"></script>' for n in image_files)
doc = f"""<meta name="dash-one-writer">
<link rel="stylesheet" href="style.css">
<div class="crx">
<header class="crx-head">{icon("ball", "brand-ball")}<div><h2>Cristiano Ronaldo Career Intelligence</h2><p>Official senior career, through his last match on {asof}.</p></div><button type="button" class="motion" aria-pressed="false">{icon("pause")}<span class="m-on">Pause motion</span><span class="m-off">Play motion</span></button></header>
<nav class="tabs" role="tablist" aria-label="Pages">{tabs}</nav>
{"".join(pages)}
</div>
{img_tags}<script src="app.js"></script>
"""
open(os.path.join(HERE, "index.html"), "w", encoding="utf8").write(doc)

DS = {
    "matches": ("Match log", "All 1,343 official senior matches.", "/_blob/03d92a03b8b938a6812eb4c8fea43676", "match_statistics.csv"),
    "goals": ("Every goal", "One row for each of the 985 goals, checked against a second list.", "/_blob/596ff4808a16d9960c14facd601e00cf", "goal_statistics.csv"),
    "seasons": ("Season record", "One row per season, club and competition.", "/_blob/40e36f56c2d0fd5a53cd7528ea73f200", "season_statistics.csv"),
    "clubs": ("Club spell totals", "One row per club spell.", "/_blob/a7c81a7c8bb668f65c7e9be66ad84a25", "club_statistics.csv"),
    "overview": ("Career headline figures", "Consolidated career figures with notes and sources.", "/_blob/7bcc59b372263fb43f30f2d966dec6e8", "career_overview.csv"),
    "intl": ("Portugal breakdowns", "Caps and goals by year, opponent, competition, venue and scoring run.", "/_blob/5f511f9796f529a8f44625fccdf2cd1a", "international_statistics.csv"),
    "euro": ("Euro tournaments", "One row per Euro.", "/_blob/42aa51473922a7b5217335838702faca", "euro_statistics.csv"),
    "wc": ("World Cup tournaments", "One row per World Cup.", "/_blob/f0768601c0250b87577d2e77a26a4d13", "world_cup_statistics.csv"),
    "tmatches": ("Tournament matches", "Each World Cup and Euro match, with cards from line-ups.", "/_blob/e53d084a2a86e243a062472ec9ed9263", "tournament_matches.csv"),
    "trophies": ("Trophy cabinet", "Every team title a source lists, tested against the match log.", "/_blob/b0735486a668e66909d15c05eedd0d29", "trophies.csv"),
    "awards": ("Individual awards", "Awards, placings and nominations, each with how it was checked.", "/_blob/8e3fe89ad05235866e17cbe4ded2abc0", "individual_awards.csv"),
    "milestones": ("Milestones and records", "Career milestones and listed records.", "/_blob/e10c992908377ddd59dd168fe7936a35", "career_milestones.csv"),
    "quality": ("Data quality checks", "Every reconciliation, discrepancy and coverage check.", "/_blob/986f911ae3b3d3d8dbb024b2488ee8d6", "data_quality_report.csv"),
    "sources": ("Source register", "Each source, its tier, access status and method.", "/_blob/2f3beab491eba74936c6bbbdd321241d", "data_sources.csv"),
    "transfers": ("Career moves", "Transfers and contract changes.", "/_blob/001b73a5a14333fa762a6b07f91bc83d", "career_transfers.csv"),
}
store = os.path.join(HERE, "store")
os.makedirs(store, exist_ok=True)


def save(name, obj):
    json.dump(obj, open(os.path.join(store, name + ".json"), "w", encoding="utf8"), ensure_ascii=False)


for k, (t, d, u, n) in DS.items():
    save("ds_" + k, {"title": t, "description": d, "source": {"kind": "file", "url": u, "name": n}, "updated": UPDATED, "fixed": True, "edit": STAMP})
save("meta", {"title": "Ronaldo Career Intelligence"})
save("params", {})
for old in os.listdir(store):
    if old.startswith("file_img"):
        os.remove(os.path.join(store, old))
for name in ("index.html", "app.js", "style.css", *image_files):
    save("file_" + name.replace(".", "_"), {"text": open(os.path.join(HERE, name), encoding="utf8").read(), "edit": STAMP})
writes = [{"op": "set", "collection": "dash", "doc_id": "meta", "file_path": os.path.join(store, "meta.json")}]
writes += [{"op": "set", "collection": "datasets", "doc_id": k, "file_path": os.path.join(store, f"ds_{k}.json")} for k in DS]
writes += [{"op": "set", "collection": "files", "doc_id": n, "file_path": os.path.join(store, "file_" + n.replace(".", "_") + ".json")} for n in ("style.css", "app.js", "index.html")]
print(json.dumps(writes))
print({n: os.path.getsize(os.path.join(HERE, n)) for n in ("index.html", "app.js", "style.css", *image_files)})
