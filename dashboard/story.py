"""The opening page: a loud, animated run from Funchal to world football."""
import html
import random
from icons import icon, icon_for

FALLBACK_CREDIT = {
    "madeira": dict(title="Funchal, Jardins da Quinta Vigia (lookout)", artist="Dr. Thomas Liptak", license="CC BY-SA 4.0",
                    page="https://commons.wikimedia.org/wiki/File:Funchal,_Jardins_da_Quinta_Vigia_(lookout).jpg"),
    "siuu": dict(title="All 48 goals of Cristiano Ronaldo, in 35 league matches for Real Madrid (2014-15)", artist="Real Madrid", license="CC BY 3.0",
                 page="https://commons.wikimedia.org/wiki/File:All_48_goals_of_Cristiano_Ronaldo,_in_35_league_matches_for_Real_Madrid_(2014-15).ogv"),
}
STOPS = ["Funchal", "Lisbon", "Manchester", "Madrid", "Saint-Denis", "Turin", "Manchester", "Riyadh", "The world", "Home"]


CONFETTI = ["#FF2D55", "#FFC400", "#00E08A", "#2EA8FF", "#FFFFFF", "#A78BFA", "#FF7A1A"]


def confetti(n, seed):
    r = random.Random(seed)
    bits = "".join(
        f'<i style="--x:{r.randint(0, 100)}%;--d:{r.uniform(3, 8):.1f}s;--w:{r.uniform(-8, 0):.1f}s;--c:{r.choice(CONFETTI)};--s:{r.uniform(.6, 1.3):.2f}"></i>'
        for _ in range(n))
    return f'<div class="confetti" aria-hidden="true">{bits}</div>'


def siuu_word():
    letters = "".join(f'<span style="--i:{i}">{c}</span>' for i, c in enumerate("SIUUU!"))
    return f'<p class="siuu" role="img" aria-label="Siuuu!">{letters}</p>'


def clip(alt, cls=""):
    return f'<div class="clip {cls}"><div class="clip-in"><img data-draw="photo" data-img="siuu" alt="{html.escape(alt)}"></div></div>'


def photo(key, alt, caption, credits, focus="50% 30%", extra=""):
    c = {**FALLBACK_CREDIT, **credits}[key]
    return (f'<figure class="frame-photo"><div class="photo-card"><img data-draw="photo" data-img="{key}" alt="{html.escape(alt)}" style="object-position:{focus}"></div>{extra}'
            f'<figcaption>{html.escape(caption)} Photo: {html.escape(c["artist"])}, {html.escape(c["license"])}.</figcaption></figure>')


def stats(items):
    return '<dl class="frame-stats count">' + "".join(f"<div>{icon_for(l)}<dd>{v}</dd><dt>{l}</dt></div>" for l, v in items) + "</dl>"


def frame(n, club, when, title, paras, pic, numbers, crest=None, floats=("ball", "star")):
    chip = f'<img class="frame-crest" data-draw="photo" data-img="{crest}" alt="">' if crest else ""
    body = "".join(f"<p>{p}</p>" for p in paras)
    bits = "".join(icon(f, f"float f{i}") for i, f in enumerate(floats))
    return (f'<article class="frame" id="ch{n}" data-beat="{n}" data-club="{club}"><span class="frame-num" aria-hidden="true">{n:02d}</span>{bits}'
            f'<div class="frame-inner"><div class="frame-text"><div class="frame-when">{chip}<span>{when}</span></div>'
            f"<h3>{title}</h3>{body}{stats(numbers)}</div>{pic}</div></article>")


def story_page(val, credits):
    C = lambda f, t: val("clubs", f, base=f"team_id={t}", fmt="int")
    R = lambda f, t, s: val("club_rollup", f, base=f"team_id={t}&season_id={s}&competition_id=All")
    O = lambda m: val("overview", "value", base=f"metric={m}", fmt="int")
    T = lambda f: val("totals", f, base="team=All&scope=All", fmt="int")
    F = lambda f, d: val("tmatches", f, base=f"match_date={d}")
    p = lambda *a, **k: photo(*a, credits, **k)
    pip = ('<div class="pip">' + clip("Looping clip of Ronaldo running, spinning, jumping and landing with his back to the camera in Real Madrid's white kit") +
           '<span class="pip-tag">The celebration</span></div>')
    frames = [
        frame(1, "MAD", "1985 to 1997 · Funchal, Madeira", "An island boy",
              ["Cristiano Ronaldo was born on 5 February 1985 in Funchal, the capital of the Portuguese island of Madeira. He was the youngest of four children and grew up in a poor home in the nearby parish of Santo António, sharing a room with his brother and sisters.",
               "His mother worked as a cook and a cleaner. His father was a municipal gardener and a part-time kit man at a local club, Andorinha. That is where the football began: he played there from 1992, then moved to Nacional in 1995."],
              p("madeira", "The city of Funchal seen from a garden lookout, with the harbour and Atlantic beyond", "Funchal, where the story starts.", focus="50% 50%"),
              [("Born in", "<b>Funchal</b>"), ("First club", "<b>Andorinha</b>")], floats=("wave", "pin")),
        frame(2, "SPO", "1997 to 2003 · Lisbon", "Leaving the island at 12",
              ["At 12, he went on a three-day trial with Sporting CP. The club signed him for a reported £1,500, and he left Madeira for Lisbon and its youth academy.",
               f'He made his first-team debut at 17 and scored twice against Moreirense in October 2002. A year later, days after a match that impressed Alex Ferguson, Manchester United signed him. He had played just {C("appearances","SPO")} senior matches for Sporting.'],
              p("sporting", "A museum case holding his Sporting shirt and photographs", "His Sporting shirt on show in the club's museum."),
              [("Sporting matches", C("appearances", "SPO")), ("Goals", C("goals", "SPO"))], "crest_SPO", ("plane", "shirt")),
        frame(3, "MU1", "2003 to 2009 · Manchester", "From teenager to world's best",
              ["He arrived at Old Trafford at 18. At 19 he scored in the FA Cup final, the first major trophy of his career, and that summer reached the Euro 2004 final with Portugal.",
               f'What followed was a transformation. United won three straight Premier League titles, and in 2007-08 he scored {R("goals","MU1","2007-08")} goals, one of them in the Champions League final as United won in Moscow. That year he won his first Ballon d\'Or.'],
              p("manutd_b", "Ronaldo in a red Manchester United shirt celebrating a goal with Rio Ferdinand", "Celebrating with Rio Ferdinand, December 2006.", focus="40% 25%"),
              [("Matches", C("appearances", "MU1")), ("Goals", C("goals", "MU1")), ("Trophies", C("trophies_with_appearance", "MU1"))], "crest_MU", ("bolt", "trophy")),
        frame(4, "RMA", "2009 to 2018 · Madrid", "More goals than games",
              [f'Real Madrid paid a world-record £80m. What they got was almost beyond belief: {C("goals","RMA")} goals in {C("appearances","RMA")} matches, the most in the club\'s history.',
               f'He scored {val("peaks","peak_goals")} in {val("peaks","peak_season")} alone, won four Champions League titles, and took four more Ballons d\'Or. The boy from Funchal had become the most prolific goalscorer in the sport\'s biggest club competition.'],
              p("realmadrid", "Ronaldo in Real Madrid's white kit on the pitch", "Against Atlético Madrid, September 2013.", focus="50% 20%", extra=pip),
              [("Matches", C("appearances", "RMA")), ("Goals", C("goals", "RMA")), ("Goals per 90", val("clubs", "goals_per_90", base="team_id=RMA"))], "crest_RMA", ("crown", "flame")),
        frame(5, "POR", "Meanwhile, July 2016 · With Portugal", "The night Portugal won without him",
              ["Twelve years after losing the Euro 2004 final at home, he led Portugal back to a final, this time against the hosts, France.",
               f'He lasted just {F("minutes","2016-07-10")} minutes before going off injured. Portugal won anyway, {F("team_score","2016-07-10")}-{F("opponent_score","2016-07-10")}, and lifted the first major trophy in their history.'],
              p("euro2016", "Ronaldo in Portugal's green away kit during a match", "In the last-16 win over Croatia, June 2016.", focus="50% 15%"),
              [("Euro matches", val("tourn_totals", "matches", base="comp=EUR&tournament_id=All")), ("Euro goals", val("tourn_totals", "goals", base="comp=EUR&tournament_id=All"))], "crest_POR", ("flag", "trophy")),
        frame(6, "JUV", "2018 to 2021 · Turin", "A new league at 33",
              [f'Most players slow down at 33. He joined Juventus for €100m, at the time the highest fee ever paid for a player over 30, and scored {C("goals","JUV")} goals in {C("appearances","JUV")} matches.',
               "He won Serie A twice and the Coppa Italia, and finished as the league's top scorer in 2020-21. He had now been top scorer in England, Spain and Italy."],
              p("juventus", "Ronaldo in Juventus black and white stripes waiting at a free kick", "Against Lokomotiv Moscow, October 2019.", focus="85% 30%"),
              [("Matches", C("appearances", "JUV")), ("Goals", C("goals", "JUV")), ("Trophies", C("trophies_with_appearance", "JUV"))], "crest_JUV", ("shield", "star")),
        frame(7, "MU2", "2021 to 2022 · Manchester again", "The return",
              [f'He went back to Old Trafford at 36 and scored twice on his second debut against Newcastle. He finished that season with {R("goals","MU2","2021-22")} goals and became the Champions League\'s most capped player.',
               "It did not end the way he wanted. After a falling-out with manager Erik ten Hag, his contract was terminated in November 2022."],
              p("return", "Ronaldo in Manchester United's red kit on the touchline", "At Old Trafford against Everton, October 2021.", focus="50% 12%"),
              [("Matches", C("appearances", "MU2")), ("Goals", C("goals", "MU2"))], "crest_MU", ("home", "bolt")),
        frame(8, "NAS", "2023 to now · Riyadh", "A new continent",
              [f'At nearly 38 he crossed to Asia and joined Al Nassr. Few expected what came next: {C("goals","NAS")} goals in {C("appearances","NAS")} matches, two Saudi Pro League top-scorer awards, and the Arab Club Champions Cup.',
               "In 2025-26 he finally won the Saudi Pro League, his first league title with the club and a league title in a fourth country."],
              p("alnassr", "Ronaldo in Al Nassr's navy kit with the ball at his feet", "Against Persepolis, September 2023.", focus="40% 30%"),
              [("Matches", C("appearances", "NAS")), ("Goals", C("goals", "NAS")), ("Trophies", C("trophies_with_appearance", "NAS"))], "crest_NAS", ("globe", "plane")),
        frame(9, "POR", "2003 to 2026 · For Portugal", "The most capped man in history",
              [f'Through all of it there was Portugal: {O("Portugal senior goals")} goals in {O("Portugal senior caps")} caps, more than any man has ever scored for his country. He became the first man to reach 200 caps, and won the Nations League twice.',
               f'In 2026 he became the first man to score at six World Cups, and his World Cup story ended with a defeat to Spain in the round of 16. On 5 November 2026 he announced his international retirement, effective after the November matches.'],
              p("wc2026", "Portrait of Ronaldo in a Portugal shirt with the captain's armband", "Against Croatia at the 2026 World Cup.", focus="50% 12%"),
              [("Caps", O("Portugal senior caps")), ("Goals", O("Portugal senior goals")), ("World Cups", val("tourn_totals", "tournaments", base="comp=WC&tournament_id=All"))], "crest_POR", ("medal", "globe")),
        frame(10, "HOME", "Today · Back in Funchal", "The boy who conquered the game",
              [f'A bronze statue of him now stands outside the CR7 Museum in Funchal, the city where he was born. He has played {T("appearances")} official matches, scored {T("goals")} goals, and won {O("Trophies won with at least one appearance")} trophies and {O("Ballon d'Or wins")} Ballons d\'Or.',
               f'He is still playing, and still {val("story_beats","to_thousand",base="beat=10")} goals short of a thousand.'],
              p("statue", "Bronze statue of Ronaldo beside the CR7 Museum in Funchal", "The statue at the CR7 Museum, Funchal.", focus="50% 40%"),
              [("Matches", T("appearances")), ("Goals", T("goals")), ("Trophies", O("Trophies won with at least one appearance"))], floats=("crown", "star")),
    ]
    route = "".join(f'<li data-stop="{i}">{s}</li>' for i, s in enumerate(STOPS, 1))
    allc = {**FALLBACK_CREDIT, **credits}
    used = ["siuu", "madeira", "sporting", "manutd_b", "realmadrid", "euro2016", "juventus", "return", "alnassr", "wc2026", "statue"]
    rows = "".join(f'<li><a href="{html.escape(allc[k]["page"])}">{html.escape(allc[k]["title"])}</a>, {html.escape(allc[k]["artist"])}, {html.escape(allc[k]["license"])}. {"Two seconds cut out, cropped and compressed." if k == "siuu" else "Resized."}</li>' for k in used)
    chips = "".join(f'<div class="hero-chip">{icon(i)}{v}<span>{l}</span></div>' for i, v, l in [
        ("ball", T("goals"), "Goals"), ("shirt", T("appearances"), "Matches"),
        ("trophy", O("Trophies won with at least one appearance"), "Trophies"), ("crown", O("Ballon d'Or wins"), "Ballons d'Or")])
    hero = (f'<header class="story-hero"><img class="hero-bg" data-draw="photo" data-img="madeira" alt=""><div class="beams" aria-hidden="true"><i></i><i></i></div>{confetti(44, 7)}'
            f'<div class="hero-grid"><div class="hero-copy"><p class="hero-kicker">{icon("pin")}<span>Funchal to the world</span></p><h3>The boy from Madeira who conquered world football</h3>'
            f'<p class="hero-lead">From a shared bedroom on a small Atlantic island to {T("goals")} goals in {T("appearances")} matches.</p><div class="hero-chips count">{chips}</div></div>'
            f'<figure class="hero-fig">{clip("Looping clip of Ronaldo running, spinning, jumping and landing with his back to the camera in Real Madrid colours at the Bernabéu", "big")}{siuu_word()}'
            f'<figcaption>The celebration, Bernabéu, 2014-15. Footage: Real Madrid, CC BY 3.0.</figcaption></figure></div>'
            f'<div class="scroll-cue" aria-hidden="true">{icon("ball")}</div></header>')

    def tick(hide=False):
        h = ' aria-hidden="true"' if hide else ""
        items = [("ball", T("goals"), "goals"), ("shirt", T("appearances"), "matches"), ("trophy", O("Trophies won with at least one appearance"), "trophies"),
                 ("crown", O("Ballon d'Or wins"), "Ballons d'Or"), ("boot", O("European Golden Shoe wins"), "Golden Shoes"), ("flame", O("Hat-tricks"), "hat-tricks"),
                 ("flag", O("Portugal senior caps"), "Portugal caps"), ("target", O("Portugal senior goals"), "Portugal goals"), ("star", O("Free-kick goals"), "free-kick goals"), ("bolt", O("Headed goals"), "headed goals")]
        return f'<div class="tick-run"{h}>' + "".join(f"<span>{icon(i)}{v} {l}</span>" for i, v, l in items) + "</div>"

    ticker = f'<div class="ticker">{tick()}{tick(True)}</div>'
    bar = (f'<div class="story-bar" data-source="story_beats"><div class="pitch" aria-hidden="true"><i class="pitch-fill"></i>{icon("ball", "pitch-ball")}</div><ol class="route" aria-label="Places in the story">{route}</ol>'
           f'<div class="tally"><span>{icon("ball")}Goals so far <b data-draw="beat" data-source="story_beats" data-field="goals">—</b></span>'
           f'<span>{icon("shirt")}Matches so far <b data-draw="beat" data-source="story_beats" data-field="matches">—</b></span></div></div>')
    links = [("summary", "ball", "Career summary"), ("progression", "up", "Progression"), ("clubs", "scale", "Compare clubs"), ("portugal", "flag", "Portugal"), ("worldcup", "globe", "World Cup"), ("honours", "trophy", "Honours"), ("quality", "check", "How it was checked")]
    tiles = "".join(f'<button type="button" data-goto="{g}">{icon(i)}<span>{l}</span></button>' for g, i, l in links)
    foot = (f'<section class="story-end">{confetti(30, 11)}<div class="end-grid">{clip("Looping clip of Ronaldo running, spinning, jumping and landing", "big")}<div>{siuu_word()}<h3>Now see the numbers behind it</h3><div class="story-links">{tiles}</div></div></div>'
            f'<details><summary>Photo credits and notices</summary><ul>{rows}</ul><p>Photos come from Wikimedia Commons under the licences shown. The celebration clip is cut from a Real Madrid video published on Wikimedia Commons under CC BY 3.0. Club and federation crests belong to their owners and are used here only to identify each team. This is an unofficial fan project, not connected to any club, federation or to the player. The biography comes from Wikipedia and the statistics from this dashboard\'s data.</p></details></section>')
    return f'<section class="pg story" id="story" role="tabpanel">{hero}{ticker}{bar}<div class="frames">{"".join(frames)}</div>{foot}</section>'
