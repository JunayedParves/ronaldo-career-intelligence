# Cristiano Ronaldo Career Intelligence

**[Open the live dashboard](https://junayedparves.github.io/ronaldo-career-intelligence/)**

An animated career dashboard and match-level database covering every official senior appearance: the boy from Madeira who conquered world football. Unofficial fan project, not connected to any club, federation or to the player.

**Data through:** 29 October 2026 (his last match). **Retrieved:** 6 November 2026.

Portugal play Denmark on 14 November and Norway on 17 November 2026. He announced his retirement from international football on 5 November 2026, effective after that break, so caps and goals may still change. He remains an active Al Nassr player.

**Dashboard source:** edit `dashboard/generate.py`, `story.py`, `app.js` or `style.css`, then run the two commands under Rebuild. GitHub Pages serves the result from `docs/`.

The opening story page lives in `dashboard/story.py`, icons in `dashboard/icons.py`, and colour and motion in `dashboard/style.css`. Photos are from Wikimedia Commons, with credits in `dashboard/images/credits.json` and on the page. The celebration clip (`dashboard/images/web/siuu.webp`) is two seconds cut from a Real Madrid video on Wikimedia Commons, listed there as CC BY 3.0, and is credited on the page. Club crests are trademarks taken from Wikipedia, and the clip contains match footage, so review both before any public use.

## Headline figures

| Metric | Value | Note |
|---|---|---|
| Appearances | 1,343 | 1,109 club, 234 Portugal |
| Goals | 985 | 839 club, 146 Portugal |
| Assists (Opta) | 261 | Other definitions run to 291 |
| Minutes | 109,812 | One goal every 111 minutes |
| Competitive only | 1,287 apps, 963 goals | Excludes 56 Portugal friendlies (22 goals) |
| Hat-tricks | 67 | Open query: the provider's own list has 66 |
| Trophies | 34 | With at least one appearance. Wikipedia lists 35, the tracker 37 |
| Red cards | 13 | 12 club, 1 Portugal |
| World Cup | 27 apps, 11 goals | Six tournaments, 2006 to 2026 |
| Euro | 30 apps, 14 goals | Six tournaments, 2004 to 2024 |
| Champions League | 183 apps, 140 goals | UEFA's 141 adds one qualifying goal |

## Three decisions to review

1. **Friendlies.** The brief says not to mix friendlies into senior competitive records. Club friendlies are excluded. Portugal friendlies are full FIFA-recognised caps, and every official count (including the 146 and 234) includes them, so they stay in the totals but carry `is_competitive = 0`. Competitive-only figures are always available.
2. **Trophies.** The headline counts only trophies where the match log shows an appearance. That drops the 2002 Supertaça, 2008 Community Shield and 2016 UEFA Super Cup. `trophies.csv` keeps all 37 with a participation status.
3. **Assists.** Opta's definition is the default. `assists_all` holds the provider's wider definition.

## Scope beyond the brief

The brief stopped at the 2022 World Cup. The 2026 World Cup has since been played, so it is included. Al Nassr's 2025-26 league title and 2026-27 season are also included. These extra files were added to support the model:

- `career_overview.csv`: the consolidated career summary from section 3A
- `goal_statistics.csv`: one row per goal
- `tournament_matches.csv`: match-by-match World Cup and Euro detail
- `dim_*.csv`: star-schema dimensions

## Known gaps

- **Yellow cards** exist only for the 57 World Cup and Euro matches. Elsewhere they are NULL. The only career total found is a press figure of 162 from November 2025, whose scope is not stated.
- **Transfermarkt, FBref, WorldFootball and 11v11** were not used. Transfermarkt and FBref show human-verification checks, which were not bypassed; the other two refuse automated requests. Opening them yourself would be the way to fill the yellow-card gap.
- **Tier 1 coverage is partial.** UEFA, FIFA, Real Madrid and Guinness were checked. Several of those were read through search summaries, as `data_sources.csv` records. The Manchester United, Juventus and Saudi Pro League sites were not used.
- **Cross-checks are not fully independent.** The sources may share upstream providers such as Opta.
- **Shots, ratings and xG** are partial or recent-only. Missing values are NULL, never zero.
- **Captaincy** is known only for World Cup and Euro matches.
- **Awards** are mostly single-source (Wikipedia). Each row's `verification_status` says so, and 17 rows the source itself marks "citation needed" are flagged.
- **Goal-level detail** depends on one tracker for fields like assister and goalkeeper. Only the date and order of each goal were cross-checked.

## Reuse

The spine comes from MessivsRonaldo.app, a third-party site with a copyright notice and no stated data licence. Only factual records were kept; its commentary and video links were not copied. It is credited here. If you reuse the dataset, check with the site first. Raw source snapshots are kept out of this repository.

## Data quality

`data/csv/data_quality_report.csv` holds 54 checks:

| Status | Count | Meaning |
|---|---|---|
| PASS | 30 | Sources agree or an internal test held |
| EXPLAINED | 10 | Sources differ and the reason is documented |
| REVIEW | 2 | Still open: hat-tricks (67 vs 66), yellow cards total |
| INFO | 12 | Coverage and completeness notes |
| FAIL | 0 | |

## Rebuild

The website:

```bash
cd dashboard
python generate.py
python build_site.py
```

The dataset, with the Python 3 standard library only:

```bash
python scripts/build_dataset.py
```

The raw source snapshots in `data/raw` are not published here, so the dataset step needs them collected again.

## Files in `data/csv`

| File | Grain |
|---|---|
| `player_profile.csv` | One player |
| `career_overview.csv` | One row per headline metric |
| `club_history.csv` | One row per career period; Manchester United spells are separate |
| `club_statistics.csv` | One row per club spell |
| `season_statistics.csv` | Player, season, club, competition |
| `competition_statistics.csv` | Competition and team |
| `match_statistics.csv` | One row per match (1,343) |
| `goal_statistics.csv` | One row per goal (985) |
| `international_statistics.csv` | Long format: `metric_group` and `item` (year, opponent, competition, confederation, streaks) |
| `euro_statistics.csv` | One row per tournament |
| `world_cup_statistics.csv` | One row per tournament |
| `tournament_matches.csv` | One row per World Cup or Euro match |
| `trophies.csv` | One row per team trophy (37 candidates) |
| `individual_awards.csv` | One row per award, placing or nomination; use `result_type` to separate wins from nominations |
| `career_milestones.csv` | One row per milestone or record |
| `career_transfers.csv` | One row per move |
| `data_sources.csv` | One row per source, with access status and retrieval date |
| `data_quality_report.csv` | One row per check |
| `dim_player`, `dim_team`, `dim_competition`, `dim_season`, `dim_date`, `dim_opponent`, `dim_tournament` | Dimensions |

**Conventions.** Keys: `match_id`, `team_id`, `competition_id`, `season_id`, `tournament_id`, `opponent`. Manchester United spells are `MU1` and `MU2`. `source_id` values join to `data_sources.csv`. `competition_name_at_time` keeps historical names, such as AFC Champions League before the Elite rebrand.

**Winning goals.** `winning_goals` counts goals scored when level that put the team ahead for good. `winning_goals_when_ahead` counts the decisive goal when the team was already leading. The provider does not publish a formal definition, so this reading is inferred from its page filters.

## Rights

No open licence is offered for this repository. Third-party material stays under its own terms: photos and the celebration clip keep the Creative Commons licences credited on the page, crests belong to their clubs and federations, and d3 is ISC licensed. If you are a rights holder and want something removed, please open an issue.
