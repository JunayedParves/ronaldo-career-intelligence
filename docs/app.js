/* Calculations. Each is visible to readers in Sources. */
dash.calc('totals', {
  title: 'Career totals by team',
  description: 'Sums the match log for each team and for all teams, with and without friendlies.',
  inputs: ['matches'],
  fn: (matches) => {
    const out = [];
    for (const team of ['All', 'SPO', 'MU1', 'RMA', 'JUV', 'MU2', 'NAS', 'POR']) {
      for (const scope of ['All', 'Competitive']) {
        const rows = matches.filter((m) => (team === 'All' || m.team_id === team) && (scope === 'All' || Number(m.is_competitive) === 1));
        const sum = (k) => rows.reduce((t, m) => t + (Number(m[k]) || 0), 0);
        const goals = sum('goals');
        const minutes = sum('minutes');
        out.push({team, scope, appearances: rows.length, goals, assists: sum('assists_opta'), minutes,
          goals_per_90: minutes ? Math.round((goals * 9000) / minutes) / 100 : 0,
          minutes_per_goal: goals ? Math.round(minutes / goals) : 0});
      }
    }
    return out;
  },
});
dash.calc('season_team', {
  title: 'Goals by season and team',
  description: 'Goals in each season for each team, with friendlies held apart.',
  inputs: ['matches'],
  fn: (matches) => {
    const map = new Map();
    for (const m of matches) {
      const key = [m.season_id, m.team_id, m.is_competitive].join('|');
      const row = map.get(key) || {season_id: m.season_id, team_id: m.team_id, competitive: Number(m.is_competitive), goals: 0};
      row.goals += Number(m.goals) || 0;
      map.set(key, row);
    }
    return [...map.values()];
  },
});
dash.calc('by_age', {
  title: 'Output by age',
  description: 'Goals, running total and goals per 90 at each age, for club and country together and apart.',
  inputs: ['matches'],
  fn: (matches) => {
    const out = [];
    for (const group of ['Club and country', 'Club', 'Portugal']) {
      const map = new Map();
      for (const m of matches) {
        if ((group === 'Club' && m.team_id === 'POR') || (group === 'Portugal' && m.team_id !== 'POR')) continue;
        const age = Math.floor(Number(m.age_at_match));
        const row = map.get(age) || {age, goals: 0, minutes: 0};
        row.goals += Number(m.goals) || 0;
        row.minutes += Number(m.minutes) || 0;
        map.set(age, row);
      }
      let cumulative = 0;
      for (const row of [...map.values()].sort((a, b) => a.age - b.age)) {
        cumulative += row.goals;
        out.push({group, age: row.age, goals: row.goals, cumulative, goals_per_90: row.minutes ? Math.round((row.goals * 9000) / row.minutes) / 100 : 0});
      }
    }
    return out;
  },
});
dash.calc('by_year', {
  title: 'Calendar-year record',
  description: 'Club and country totals for each calendar year.',
  inputs: ['matches'],
  fn: (matches) => {
    const map = new Map();
    for (const m of matches) {
      const row = map.get(m.calendar_year) || {year: m.calendar_year, appearances: 0, goals: 0, assists: 0, minutes: 0};
      row.appearances += 1;
      row.goals += Number(m.goals) || 0;
      row.assists += Number(m.assists_opta) || 0;
      row.minutes += Number(m.minutes) || 0;
      map.set(m.calendar_year, row);
    }
    return [...map.values()].map((r) => ({...r, goals_per_90: r.minutes ? Math.round((r.goals * 9000) / r.minutes) / 100 : 0}));
  },
});
dash.calc('peaks', {
  title: 'Peak figures',
  description: 'Best club season, best calendar year, the latest full club season, and goals scored from age 30.',
  inputs: ['matches'],
  fn: (matches) => {
    const seasons = new Map();
    const years = new Map();
    let after30 = 0;
    let total = 0;
    for (const m of matches) {
      const g = Number(m.goals) || 0;
      total += g;
      if (Number(m.age_at_match) >= 30) after30 += g;
      if (m.team_id !== 'POR') seasons.set(m.season_id, (seasons.get(m.season_id) || 0) + g);
      years.set(m.calendar_year, (years.get(m.calendar_year) || 0) + g);
    }
    const [peak_season, peak_goals] = [...seasons].sort((a, b) => b[1] - a[1])[0];
    const [peak_year, peak_year_goals] = [...years].sort((a, b) => b[1] - a[1])[0];
    const recent_season = '2025-26';
    return [{peak_season, peak_goals, peak_year, peak_year_goals, recent_season, recent_goals: seasons.get(recent_season) || 0, goals_after_30: after30, share_after_30: Math.round((after30 * 100) / total) + '%'}];
  },
});
dash.calc('club_rollup', {
  title: 'Club spell totals',
  description: 'Season table added up for every club, season and competition choice on the club pages.',
  inputs: ['seasons'],
  fn: (seasons) => {
    const out = [];
    for (const team_id of [...new Set(seasons.map((s) => s.team_id))]) {
      const own = seasons.filter((s) => s.team_id === team_id);
      for (const season_id of ['All', ...new Set(own.map((s) => s.season_id))]) {
        for (const competition_id of ['All', ...new Set(own.map((s) => s.competition_id))]) {
          const rows = own.filter((s) => (season_id === 'All' || s.season_id === season_id) && (competition_id === 'All' || s.competition_id === competition_id));
          const sum = (k) => rows.reduce((t, r) => t + (Number(r[k]) || 0), 0);
          const goals = sum('goals');
          const minutes = sum('minutes_played');
          const named = own.find((s) => s.competition_id === competition_id);
          out.push({team_id, season_id, competition_id, competition: named ? named.competition : 'All', appearances: sum('appearances'), goals, assists: sum('assists'), minutes_played: minutes,
            goals_per_90: minutes ? Math.round((goals * 9000) / minutes) / 100 : 0});
        }
      }
    }
    return out;
  },
});
dash.calc('goal_types', {
  title: 'Goals by situation',
  description: 'Counts goals by how they were scored, for each team, season and competition.',
  inputs: ['goals'],
  fn: (goals) => {
    const map = new Map();
    for (const g of goals) {
      const key = [g.team_id, g.season_id, g.competition_id, g.situation, g.body_part].join('|');
      const row = map.get(key) || {team_id: g.team_id, season_id: g.season_id, competition_id: g.competition_id, situation: g.situation, body_part: g.body_part, goals: 0};
      row.goals += 1;
      map.set(key, row);
    }
    return [...map.values()];
  },
});
dash.calc('tourn_totals', {
  title: 'Tournament totals',
  description: 'Adds up the Euro and World Cup tables, for one edition or all of them.',
  inputs: ['euro', 'wc'],
  fn: (euro, wc) => {
    const out = [];
    for (const [comp, rows] of [['EUR', euro], ['WC', wc]]) {
      for (const tournament_id of ['All', ...rows.map((r) => r.tournament_id)]) {
        const own = rows.filter((r) => tournament_id === 'All' || r.tournament_id === tournament_id);
        const sum = (k) => own.reduce((t, r) => t + (Number(r[k]) || 0), 0);
        out.push({comp, tournament_id, tournaments: own.length, matches: sum('matches_played'), goals: sum('goals'), assists: sum('assists'), minutes: sum('minutes_played'), yellow_cards: sum('yellow_cards'), red_cards: sum('red_cards')});
      }
    }
    return out;
  },
});
dash.calc('stage_goals', {
  title: 'Tournament goals by stage',
  description: 'Goals at each stage for each Euro and World Cup.',
  inputs: ['tmatches'],
  fn: (tmatches) => {
    const map = new Map();
    for (const m of tmatches) {
      const key = [m.competition_id, m.tournament_id, m.stage].join('|');
      const row = map.get(key) || {competition_id: m.competition_id, tournament_id: m.tournament_id, stage: m.stage, goals: 0, matches: 0};
      row.goals += Number(m.goals) || 0;
      row.matches += 1;
      map.set(key, row);
    }
    return [...map.values()];
  },
});
dash.calc('opp_goals', {
  title: 'Tournament goals by opponent',
  description: 'Goals against each opponent at each Euro and World Cup.',
  inputs: ['tmatches'],
  fn: (tmatches) => {
    const map = new Map();
    for (const m of tmatches) {
      const key = [m.competition_id, m.tournament_id, m.opponent].join('|');
      const row = map.get(key) || {competition_id: m.competition_id, tournament_id: m.tournament_id, opponent: m.opponent, goals: 0};
      row.goals += Number(m.goals) || 0;
      map.set(key, row);
    }
    return [...map.values()];
  },
});
dash.calc('honour_counts', {
  title: 'Honours counts',
  description: 'Counts team trophies by whether he appeared, and individual awards won.',
  inputs: ['trophies', 'awards'],
  fn: (trophies, awards) => {
    const played = trophies.filter((t) => Number(t.counts_as_played) === 1).length;
    const won = awards.filter((a) => Number(a.is_award_won) === 1);
    return [{listed: trophies.length, played, no_appearance: trophies.length - played, awards_won: won.length, major_won: won.filter((a) => Number(a.is_major) === 1).length,
      not_won: awards.length - won.length}];
  },
});
dash.calc('trophy_team', {
  title: 'Trophies by team',
  description: 'Trophies won with at least one appearance, by parent club or country.',
  inputs: ['trophies'],
  fn: (trophies) => {
    const map = new Map();
    for (const t of trophies) if (Number(t.counts_as_played) === 1) map.set(t.team, (map.get(t.team) || 0) + 1);
    return [...map].map(([team, trophies_won]) => ({team, trophies_won}));
  },
});
dash.calc('award_cat', {
  title: 'Awards won by category',
  description: 'Individual awards won, by type. Nominations and placings are not counted.',
  inputs: ['awards'],
  fn: (awards) => {
    const map = new Map();
    for (const a of awards) if (Number(a.is_award_won) === 1) map.set(a.award_category, (map.get(a.award_category) || 0) + 1);
    return [...map].map(([award_category, awards_won]) => ({award_category, awards_won}));
  },
});
dash.calc('quality_counts', {
  title: 'Quality checks by status',
  description: 'Counts each check by its outcome, and the sources reached.',
  inputs: ['quality', 'sources'],
  fn: (quality, sources) => {
    const n = (s) => quality.filter((q) => q.status === s).length;
    return [{checks: quality.length, pass: n('PASS'), explained: n('EXPLAINED'), review: n('REVIEW'), info: n('INFO'), fail: n('FAIL'),
      sources_used: sources.filter((s) => String(s.access_status).startsWith('Accessed')).length,
      sources_blocked: sources.filter((s) => s.access_status === 'Blocked').length}];
  },
});
dash.calc('quality_area', {
  title: 'Quality checks by area',
  description: 'Counts checks by area and outcome.',
  inputs: ['quality'],
  fn: (quality) => {
    const map = new Map();
    for (const q of quality) {
      const key = q.area + '|' + q.status;
      const row = map.get(key) || {area: q.area, status: q.status, checks: 0};
      row.checks += 1;
      map.set(key, row);
    }
    return [...map.values()];
  },
});

dash.calc('story_beats', {
  title: 'Story running totals',
  description: 'Goals and matches added up to the end of each frame of the story, and goals still needed to reach one thousand.',
  inputs: ['matches'],
  fn: (matches) => {
    const ends = ['2002-08-01', '2003-08-11', '2009-07-01', '2018-07-10', '2018-07-10', '2021-08-31', '2022-11-22', '2026-12-31', '2026-12-31', '2026-12-31'];
    const total = matches.reduce((t, m) => t + (Number(m.goals) || 0), 0);
    return ends.map((end, i) => {
      const rows = matches.filter((m) => m.match_date <= end);
      return {beat: i + 1, goals: rows.reduce((t, m) => t + (Number(m.goals) || 0), 0), matches: rows.length, to_thousand: 1000 - total};
    });
  },
});

/* Shared helpers */
const param = (name) => dash.params()[name] ?? 'All';
const ok = (id) => dash.data(id).status === 'ok';
const fmtInt = d3.format(',');
const PAL = ['#FF2D55', '#FFC400', '#00E08A', '#2EA8FF', '#A78BFA', '#FF7A1A', '#22D3EE'];
const TEAM_COL = {SPO: '#00D27A', MU1: '#FF3B30', RMA: '#FFC400', JUV: '#DDE3F2', MU2: '#FF8A65', NAS: '#2EA8FF', POR: '#FF2D78'};
const cols = () => PAL;
const clubbed = (el) => Boolean(el.closest('[data-club]'));
const acc = (el) => (clubbed(el) ? 'var(--club-chart)' : PAL[0]);
const acc2 = (el) => (clubbed(el) ? 'var(--club-alt)' : PAL[1]);
const rainbow = (el, i) => (clubbed(el) ? (i % 2 ? 'var(--club-alt)' : 'var(--club-chart)') : PAL[i % PAL.length]);
const calm = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches || document.querySelector('.crx.still') !== null;
const delay = (i) => `${Math.min(i, 24) * 45}ms`;

/* Numbers count up the first time they scroll into view; the final value is always in place first. */
const countTo = (el, to) => {
  cancelAnimationFrame(el._raf);
  if (calm()) {
    el._at = to;
    el._raf = null;
    el.textContent = fmtInt(to);
    return;
  }
  const from = el._at || 0;
  const start = performance.now();
  const step = (now) => {
    const p = Math.min(1, (now - start) / 1500);
    const n = p === 1 ? to : Math.round(from + (to - from) * (1 - (1 - p) ** 4));
    el._at = n;
    el.textContent = fmtInt(n);
    el._raf = p < 1 ? requestAnimationFrame(step) : null;
  };
  el._raf = requestAnimationFrame(step);
};
const counter = new IntersectionObserver((entries) => {
  for (const e of entries) {
    if (!e.isIntersecting) continue;
    counter.unobserve(e.target);
    countTo(e.target, Number(e.target.dataset.to));
  }
}, {root: document, threshold: 0.3});
const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const matchWhere = (row, where) => where.split('&').filter(Boolean).every((part) => {
  const [k, v] = part.split('=');
  return String(row[decodeURIComponent(k)]) === decodeURIComponent(v);
});
const STAGES = ['Group stage', 'Round of 32', 'Round of 16', 'Quarter-final', 'Semi-final', 'Third-place play-off', 'Final'];
const TEAM_NAME = {SPO: 'Sporting CP', MU1: 'Man Utd 2003-09', RMA: 'Real Madrid', JUV: 'Juventus', MU2: 'Man Utd 2021-22', NAS: 'Al Nassr', POR: 'Portugal'};

/* Single values. data-base and data-follow build the row to read. */
dash.draw('val', (el) => {
  const g = dash.data(el.dataset.source);
  if (g.status !== 'ok') {
    el.textContent = '—';
    return;
  }
  const follow = (el.dataset.follow || '').split(',').filter(Boolean).map((pair) => {
    const [field, name] = pair.split(':');
    return `${field}=${encodeURIComponent(param(name))}`;
  });
  const where = [el.dataset.base, ...follow].filter(Boolean).join('&');
  if (where) el.dataset.where = where;
  const row = where ? g.data.find((r) => matchWhere(r, where)) : g.data[0];
  const value = row ? row[el.dataset.field] : '';
  if (el.dataset.fmt === 'int' && el.closest('.count') && row) {
    const to = Number(value);
    if (el.dataset.to === String(to)) {
      if (!el._raf) el.textContent = fmtInt(to);
      return;
    }
    el.dataset.to = String(to);
    el.textContent = fmtInt(to);
    counter.unobserve(el);
    counter.observe(el);
    return;
  }
  el.textContent = el.dataset.fmt === 'int' ? fmtInt(Number(value)) : String(value ?? '');
});

/* Dropdowns */
document.querySelectorAll('select[data-param]:not([data-draw])').forEach((sel) => {
  sel.addEventListener('change', () => dash.setParams({[sel.dataset.param]: sel.value === 'All' ? null : sel.value}));
});
dash.onData(() => {
  document.querySelectorAll('select[data-param]:not([data-draw])').forEach((sel) => {
    sel.value = param(sel.dataset.param);
  });
});
dash.draw('club-season', (sel) => {
  const rows = ok('club_rollup') ? dash.data('club_rollup').data.filter((r) => r.team_id === sel.dataset.team && r.competition_id === 'All' && r.season_id !== 'All') : [];
  sel.replaceChildren(new Option('All seasons', 'All'), ...rows.map((r) => new Option(r.season_id, r.season_id)));
  sel.value = param(sel.dataset.param);
  sel.onchange = () => dash.setParams({[sel.dataset.param]: sel.value === 'All' ? null : sel.value});
});
dash.draw('club-comp', (sel) => {
  const rows = ok('club_rollup') ? dash.data('club_rollup').data.filter((r) => r.team_id === sel.dataset.team && r.season_id === 'All' && r.competition_id !== 'All') : [];
  sel.replaceChildren(new Option('All competitions', 'All'), ...rows.map((r) => new Option(r.competition, r.competition_id)));
  sel.value = param(sel.dataset.param);
  sel.onchange = () => dash.setParams({[sel.dataset.param]: sel.value === 'All' ? null : sel.value});
});
dash.draw('edition', (sel) => {
  const id = sel.dataset.source;
  const rows = ok(id) ? dash.data(id).data : [];
  sel.replaceChildren(new Option('All tournaments', 'All'), ...rows.map((r) => new Option(r.tournament_id, r.tournament_id)));
  sel.value = param(sel.dataset.param);
  sel.onchange = () => dash.setParams({[sel.dataset.param]: sel.value === 'All' ? null : sel.value});
});

/* Tables */
const sortState = new Map();
const search = (el) => {
  const box = el.closest('.card')?.querySelector('input[data-search]');
  return box ? box.value.trim().toLowerCase() : '';
};
const clubFilter = (el, r) => {
  const t = el.dataset.team;
  const s = param(`season${t}`);
  const c = param(`comp${t}`);
  return r.team_id === t && (s === 'All' || r.season_id === s) && (c === 'All' || r.competition_id === c);
};
const TABLES = {
  moments: {source: 'milestones', key: ['milestone_id'], rows: (d) => d.filter((r) => r.milestone_type === 'Milestone').reverse()},
  moves: {source: 'transfers', key: ['transfer_id'], rows: (d) => d},
  years: {source: 'by_year', key: ['year'], rows: (d) => d},
  'club-compare': {source: 'clubs', key: ['team_id'], rows: (d) => d},
  'club-seasons': {source: 'seasons', key: ['team_id', 'season_id', 'competition_id'], rows: (d, el) => d.filter((r) => clubFilter(el, r))},
  'club-trophies': {source: 'trophies', key: ['trophy_id'], rows: (d, el) => d.filter((r) => r.team_id === el.dataset.team)},
  opponents: {source: 'intl', key: ['metric_group', 'item'], rows: (d) => d.filter((r) => r.metric_group === 'By opponent')},
  streaks: {source: 'intl', key: ['metric_group', 'item'], rows: (d) => d.filter((r) => r.metric_group === 'Scoring streak (consecutive caps)')},
  'tourn-sum': {source: null, key: ['tournament_id'], rows: (d) => d},
  'tourn-matches': {source: 'tmatches', key: ['match_id'], rows: (d, el) => {
    const pick = param(el.dataset.param);
    return d.filter((r) => r.competition_id === el.dataset.comp && (pick === 'All' || r.tournament_id === pick)).reverse();
  }},
  trophies: {source: 'trophies', key: ['trophy_id'], rows: (d) => d},
  ballon: {source: 'awards', key: ['award_id'], rows: (d) => d.filter((r) => /Ballon d'Or$/.test(r.achievement_name) && !/Dream/.test(r.achievement_name)).sort((a, b) => Number(b.year_start) - Number(a.year_start))},
  awards: {source: 'awards', key: ['award_id'], rows: (d) => {
    const pick = param('awardResult');
    return d.filter((r) => pick === 'All' || (pick === 'Other' ? !['Won', 'Nominated', 'Shortlisted'].includes(r.result_type) : r.result_type === pick));
  }},
  records: {source: 'milestones', key: ['milestone_id'], rows: (d) => d.filter((r) => r.milestone_type === 'Record')},
  checks: {source: 'quality', key: ['check_id'], rows: (d) => {
    const pick = param('qualityStatus');
    return d.filter((r) => pick === 'All' || r.status === pick);
  }},
  sourcesList: {source: 'sources', key: ['source_id'], rows: (d) => d},
};
const showCell = (v) => {
  if (v === null || v === undefined) return '';
  const n = Number(v);
  return v !== '' && Number.isInteger(n) && Math.abs(n) >= 1000 && !/^(19|20)\d\d$/.test(String(v)) ? fmtInt(n) : String(v);
};
Object.entries(TABLES).forEach(([name, spec]) => {
  dash.draw(`t-${name}`, (body) => {
    const table = body.closest('table');
    const source = spec.source || table.dataset.source;
    const g = dash.data(source);
    if (g.status !== 'ok') {
      body.replaceChildren();
      return;
    }
    const fields = [...table.querySelectorAll('th[data-field]')].map((th) => th.dataset.field);
    let rows = spec.rows([...g.data], body);
    const q = search(body);
    if (q) rows = rows.filter((r) => fields.some((f) => String(r[f] ?? '').toLowerCase().includes(q)));
    const sort = sortState.get(table.id);
    if (sort) {
      const dir = sort.dir === 'ascending' ? 1 : -1;
      const val = (r) => {
        const v = r[sort.field];
        return v !== '' && v !== null && !Number.isNaN(Number(v)) ? Number(v) : String(v ?? '');
      };
      rows = [...rows].sort((a, b) => (val(a) > val(b) ? dir : val(a) < val(b) ? -dir : 0));
    }
    body.replaceChildren(...rows.map((r) => {
      const tr = document.createElement('tr');
      tr.dataset.key = spec.key.length === 1 ? String(r[spec.key[0]]) : spec.key.map((k) => encodeURIComponent(r[k])).join(',');
      for (const f of fields) {
        const td = document.createElement('td');
        td.textContent = showCell(r[f]);
        if (f === 'status' || f === 'access_status' || f === 'result_type' || f === 'ronaldo_participation_status' || f === 'verification_status') td.dataset.state = String(r[f] ?? '').split(/[ :]/)[0].toLowerCase();
        tr.append(td);
      }
      return tr;
    }));
  });
});
document.querySelectorAll('th[data-field]').forEach((th) => {
  th.addEventListener('click', () => {
    const table = th.closest('table');
    const was = sortState.get(table.id);
    const dir = was && was.field === th.dataset.field && was.dir === 'descending' ? 'ascending' : 'descending';
    sortState.set(table.id, {field: th.dataset.field, dir});
    table.querySelectorAll('th').forEach((h) => h.removeAttribute('aria-sort'));
    th.setAttribute('aria-sort', dir);
    const body = table.querySelector('tbody[data-draw]');
    if (body) dash.draw(body.dataset.draw);
  });
});
document.querySelectorAll('input[data-search]').forEach((box) => {
  box.addEventListener('input', () => {
    const body = box.closest('.card').querySelector('tbody[data-draw]');
    if (body) dash.draw(body.dataset.draw);
  });
});

/* Charts */
const frame = (el, height) => {
  el.replaceChildren();
  const width = Math.max(el.clientWidth, 280);
  const svg = d3.select(el).append('svg').attr('width', '100%').attr('height', height).attr('viewBox', `0 0 ${width} ${height}`);
  const tip = d3.select(el).append('div').attr('class', 'tip').attr('hidden', true);
  const show = (event, title, lines) => {
    tip.attr('hidden', null).selectAll('*').remove();
    tip.append('div').attr('class', 'tip-title').text(title);
    for (const line of lines) tip.append('div').text(line);
    const [x, y] = d3.pointer(event, el);
    const box = tip.node().getBoundingClientRect();
    tip.style('left', `${Math.min(Math.max(0, x + 12), el.clientWidth - box.width - 4)}px`).style('top', `${Math.max(0, y - box.height - 8)}px`);
  };
  const hide = () => tip.attr('hidden', true);
  return {svg, width, show, hide};
};
const textWidth = (svg, strings) => {
  const probe = svg.append('text').attr('class', 'tick-text');
  const widest = d3.max(strings, (s) => {
    probe.text(s);
    return probe.node().getComputedTextLength();
  }) || 0;
  probe.remove();
  return widest;
};
const hbars = (el, rows, label, value, format = fmtInt) => {
  if (!rows.length) {
    el.textContent = '—';
    return;
  }
  const rowH = 30;
  const height = rows.length * rowH + 8;
  const {svg, width, show, hide} = frame(el, height);
  const left = textWidth(svg, rows.map(label)) + 12;
  const right = textWidth(svg, rows.map((r) => format(value(r)))) + 12;
  const x = d3.scaleLinear([0, d3.max(rows, value) || 1], [0, Math.max(width - left - right, 20)]);
  const y = d3.scaleBand(rows.map(label), [4, height - 4]).padding(0.28);
  const g = svg.selectAll('g').data(rows).join('g').attr('transform', (r) => `translate(0,${y(label(r))})`);
  g.append('text').attr('class', 'tick-text').attr('x', left - 8).attr('y', y.bandwidth() / 2).attr('dy', '.35em').attr('text-anchor', 'end').text(label);
  g.append('rect').attr('class', 'grow-x').attr('x', left).attr('height', y.bandwidth()).attr('width', (r) => Math.max(x(value(r)), 1)).attr('rx', 3)
    .style('animation-delay', (r, i) => delay(i))
    .style('fill', (r, i) => rainbow(el, i))
    .on('mousemove', (e, r) => show(e, label(r), [format(value(r))])).on('mouseleave', hide);
  g.append('text').attr('class', 'tick-text strong').attr('x', (r) => left + x(value(r)) + 6).attr('y', y.bandwidth() / 2).attr('dy', '.35em').text((r) => format(value(r)));
};
const xLabels = (svg, x, names, height, width) => {
  const widest = textWidth(svg, names) + 10;
  const step = Math.max(1, Math.ceil((widest * names.length) / width));
  svg.append('g').selectAll('text').data(names.filter((n, i) => i % step === 0)).join('text').attr('class', 'tick-text').attr('x', (n) => x(n) + x.bandwidth() / 2).attr('y', height - 6).attr('text-anchor', 'middle').text((n) => n);
};
const yAxis = (svg, y, width, left) => {
  const ticks = y.ticks(4);
  svg.append('g').selectAll('line').data(ticks).join('line').attr('x1', left).attr('x2', width).attr('y1', y).attr('y2', y).style('stroke', 'var(--cds-chart-grid)');
  svg.append('g').selectAll('text').data(ticks).join('text').attr('class', 'tick-text').attr('x', left - 6).attr('y', y).attr('dy', '.35em').attr('text-anchor', 'end').text((t) => fmtInt(t));
};
const vbars = (el, rows, label, value, highlight = true) => {
  if (!rows.length) {
    el.textContent = '—';
    return;
  }
  const height = 260;
  const {svg, width, show, hide} = frame(el, height);
  const y = d3.scaleLinear([0, d3.max(rows, value) || 1], [height - 26, 10]).nice();
  const left = textWidth(svg, y.ticks(4).map((t) => fmtInt(t))) + 10;
  const x = d3.scaleBand(rows.map(label), [left, width - textWidth(svg, rows.map(label)) / 2]).padding(0.24);
  yAxis(svg, y, width, left);
  const peak = d3.max(rows, value);
  svg.append('g').selectAll('rect').data(rows).join('rect').attr('class', (r) => (value(r) === peak ? 'grow-y peak' : 'grow-y')).attr('x', (r) => x(label(r))).attr('y', (r) => y(value(r))).attr('width', x.bandwidth()).attr('height', (r) => y(0) - y(value(r))).attr('rx', 3)
    .style('animation-delay', (r, i) => delay(i))
    .style('fill', (r) => (!highlight || value(r) === peak ? acc(el) : acc2(el)))
    .style('fill-opacity', (r) => (!highlight || value(r) === peak ? 1 : 0.62))
    .on('mousemove', (e, r) => show(e, label(r), [`${fmtInt(value(r))} goals`])).on('mouseleave', hide);
  xLabels(svg, x, rows.map(label), height, width - left);
};
const LEGEND = (el, items) => {
  const box = d3.select(el).append('div').attr('class', 'legend');
  for (const [name, color] of items) {
    const row = box.append('span');
    row.append('i').style('background', color);
    row.append('span').text(name);
  }
};
const stacked = (el, categories, keys, value, colorOf, nameOf) => {
  const height = 300;
  const {svg, width, show, hide} = frame(el, height);
  const totals = categories.map((c) => d3.sum(keys, (k) => value(c, k)));
  const y = d3.scaleLinear([0, d3.max(totals) || 1], [height - 26, 10]).nice();
  const left = textWidth(svg, y.ticks(4).map((t) => fmtInt(t))) + 10;
  const x = d3.scaleBand(categories, [left, width - textWidth(svg, categories) / 2]).padding(0.2);
  yAxis(svg, y, width, left);
  categories.forEach((c, ci) => {
    let base = 0;
    keys.forEach((k) => {
      const v = value(c, k);
      if (!v) return;
      svg.append('rect').attr('class', 'grow-y').style('animation-delay', delay(ci)).attr('x', x(c)).attr('width', x.bandwidth()).attr('y', y(base + v)).attr('height', y(base) - y(base + v)).style('fill', colorOf(k))
        .on('mousemove', (e) => show(e, c, keys.filter((t) => value(c, t)).map((t) => `${nameOf(t)}: ${fmtInt(value(c, t))}`))).on('mouseleave', hide);
      base += v;
    });
  });
  xLabels(svg, x, categories, height, width - left);
  LEGEND(el, keys.map((k) => [nameOf(k), colorOf(k)]));
};
const grouped = (el, rows, label, series) => {
  const height = 260;
  const {svg, width, show, hide} = frame(el, height);
  const y = d3.scaleLinear([0, d3.max(rows, (r) => d3.max(series, (s) => s.value(r))) || 1], [height - 26, 10]).nice();
  const left = textWidth(svg, y.ticks(4).map((t) => fmtInt(t))) + 10;
  const x = d3.scaleBand(rows.map(label), [left, width - textWidth(svg, rows.map(label)) / 2]).padding(0.24);
  const inner = d3.scaleBand(series.map((s) => s.name), [0, x.bandwidth()]).padding(0.08);
  yAxis(svg, y, width, left);
  series.forEach((s, i) => {
    svg.append('g').selectAll('rect').data(rows).join('rect').attr('class', 'grow-y').style('animation-delay', (r, n) => delay(n)).attr('x', (r) => x(label(r)) + inner(s.name)).attr('y', (r) => y(s.value(r))).attr('width', inner.bandwidth()).attr('height', (r) => y(0) - y(s.value(r))).attr('rx', 3)
      .style('fill', i === 0 ? acc(el) : acc2(el)).on('mousemove', (e, r) => show(e, label(r), series.map((t) => `${t.name}: ${t.value(r)}`))).on('mouseleave', hide);
  });
  xLabels(svg, x, rows.map(label), height, width - left);
  LEGEND(el, series.map((s, i) => [s.name, i === 0 ? acc(el) : acc2(el)]));
};
const line = (el, rows, xv, yv, unit, format = fmtInt) => {
  if (!rows.length) {
    el.textContent = '—';
    return;
  }
  const height = 260;
  const {svg, width, show, hide} = frame(el, height);
  const y = d3.scaleLinear([0, d3.max(rows, yv) || 1], [height - 26, 12]).nice();
  const left = textWidth(svg, y.ticks(4).map((t) => format(t))) + 10;
  const lastLabel = format(yv(rows[rows.length - 1]));
  const x = d3.scaleLinear(d3.extent(rows, xv), [left, width - textWidth(svg, [lastLabel]) - 12]);
  const ticks = y.ticks(4);
  svg.append('g').selectAll('line').data(ticks).join('line').attr('x1', left).attr('x2', width).attr('y1', y).attr('y2', y).style('stroke', 'var(--cds-chart-grid)');
  svg.append('g').selectAll('text').data(ticks).join('text').attr('class', 'tick-text').attr('x', left - 6).attr('y', y).attr('dy', '.35em').attr('text-anchor', 'end').text((t) => format(t));
  svg.append('g').selectAll('text').data(x.ticks(Math.min(8, Math.floor(width / 70)))).join('text').attr('class', 'tick-text').attr('x', x).attr('y', height - 6).attr('text-anchor', 'middle').text((t) => t);
  svg.append('path').datum(rows).attr('class', 'fade-in').attr('fill-opacity', 0.16).style('fill', acc(el)).attr('d', d3.area().x((r) => x(xv(r))).y0(y(0)).y1((r) => y(yv(r))));
  svg.append('path').datum(rows).attr('class', 'draw-line').attr('pathLength', 1).attr('fill', 'none').attr('stroke-width', 3).attr('stroke-linecap', 'round').attr('stroke-linejoin', 'round').style('stroke', acc(el)).attr('d', d3.line().x((r) => x(xv(r))).y((r) => y(yv(r))));
  const end = rows[rows.length - 1];
  svg.append('circle').attr('cx', x(xv(end))).attr('cy', y(yv(end))).attr('r', 4.5).attr('class', 'pulse').style('fill', acc(el));
  svg.append('text').attr('class', 'tick-text strong').attr('x', x(xv(end)) + 7).attr('y', y(yv(end))).attr('dy', '.35em').text(lastLabel);
  const dot = svg.append('circle').attr('r', 4).attr('opacity', 0).style('fill', acc(el));
  svg.append('rect').attr('x', left).attr('y', 0).attr('width', width - left).attr('height', height - 22).style('fill', 'transparent')
    .on('mousemove', (e) => {
      const [mx] = d3.pointer(e);
      const r = rows[d3.bisectCenter(rows.map(xv), x.invert(mx))];
      dot.attr('cx', x(xv(r))).attr('cy', y(yv(r))).attr('opacity', 1);
      show(e, `Age ${xv(r)}`, [`${format(yv(r))} ${unit}`]);
    }).on('mouseleave', () => {
      dot.attr('opacity', 0);
      hide();
    });
};
const bubbles = (el, rows) => {
  const height = 300;
  const {svg, width, show, hide} = frame(el, height);
  const apps = (r) => Number(r.appearances);
  const rate = (r) => Number(r.goals_per_90);
  const y = d3.scaleLinear([0, d3.max(rows, rate) * 1.15], [height - 34, 14]).nice();
  const left = 36;
  const x = d3.scaleLinear([0, d3.max(rows, apps) * 1.08], [left, width - 24]);
  const r = d3.scaleSqrt([0, d3.max(rows, (d) => Number(d.goals))], [0, 26]);
  const ticks = y.ticks(4);
  svg.append('g').selectAll('line').data(ticks).join('line').attr('x1', left).attr('x2', width).attr('y1', y).attr('y2', y).style('stroke', 'var(--cds-chart-grid)');
  svg.append('g').selectAll('text').data(ticks).join('text').attr('class', 'tick-text').attr('x', left - 6).attr('y', y).attr('dy', '.35em').attr('text-anchor', 'end').text((t) => t.toFixed(1));
  svg.append('g').selectAll('text').data(x.ticks(5)).join('text').attr('class', 'tick-text').attr('x', x).attr('y', height - 16).attr('text-anchor', 'middle').text((t) => t);
  svg.append('text').attr('class', 'tick-text').attr('x', width - 24).attr('y', height - 2).attr('text-anchor', 'end').text('Appearances');
  svg.append('g').selectAll('circle').data(rows).join('circle').attr('class', 'pop').style('animation-delay', (d, i) => delay(i * 2)).attr('cx', (d) => x(apps(d))).attr('cy', (d) => y(rate(d))).attr('r', (d) => r(Number(d.goals))).attr('fill-opacity', 0.9)
    .style('fill', (d) => TEAM_COL[d.team_id])
    .on('mousemove', (e, d) => show(e, d.club, [`${d.appearances} matches`, `${d.goals} goals`, `${d.goals_per_90} per 90`])).on('mouseleave', hide);
  svg.append('g').selectAll('text').data(rows).join('text').attr('class', 'tick-text').attr('text-anchor', (d) => (x(apps(d)) > width * 0.7 ? 'end' : 'start'))
    .attr('x', (d) => x(apps(d)) + (x(apps(d)) > width * 0.7 ? -1 : 1) * (r(Number(d.goals)) + 5)).attr('y', (d) => y(rate(d))).attr('dy', '.35em').text((d) => TEAM_NAME[d.team_id]);
};

const descending = (value) => (a, b) => value(b) - value(a);
dash.draw('c-season-team', (el) => {
  if (!ok('season_team')) {
    el.textContent = '—';
    return;
  }
  const team = param('teamS');
  const scope = param('scopeS');
  const rows = dash.data('season_team').data.filter((r) => (team === 'All' || r.team_id === team) && (scope === 'All' || r.competitive === 1));
  const seasons = [...new Set(dash.data('season_team').data.map((r) => r.season_id))].sort();
  const keys = ['SPO', 'MU1', 'RMA', 'JUV', 'MU2', 'NAS', 'POR'].filter((k) => rows.some((r) => r.team_id === k));
  const value = (s, k) => d3.sum(rows.filter((r) => r.season_id === s && r.team_id === k), (r) => r.goals);
  stacked(el, seasons, keys, value, (k) => TEAM_COL[k], (k) => TEAM_NAME[k]);
});
dash.draw('c-team-goals', (el) => {
  if (!ok('totals')) {
    el.textContent = '—';
    return;
  }
  const scope = param('scopeS');
  const rows = dash.data('totals').data.filter((r) => r.team !== 'All' && r.scope === scope).sort(descending((r) => r.goals));
  hbars(el, rows, (r) => TEAM_NAME[r.team], (r) => r.goals);
});
dash.draw('c-cumulative', (el) => {
  if (!ok('by_age')) {
    el.textContent = '—';
    return;
  }
  const group = dash.params().ageGroup ?? 'Club and country';
  line(el, dash.data('by_age').data.filter((r) => r.group === group), (r) => r.age, (r) => r.cumulative, 'goals in total');
});
dash.draw('c-age-rate', (el) => {
  if (!ok('by_age')) {
    el.textContent = '—';
    return;
  }
  const group = dash.params().ageGroup ?? 'Club and country';
  line(el, dash.data('by_age').data.filter((r) => r.group === group), (r) => r.age, (r) => r.goals_per_90, 'goals per 90', d3.format('.2f'));
});
dash.draw('c-rate-club', (el) => {
  if (!ok('clubs')) {
    el.textContent = '—';
    return;
  }
  hbars(el, [...dash.data('clubs').data].sort(descending((r) => Number(r.goals_per_90))), (r) => TEAM_NAME[r.team_id], (r) => Number(r.goals_per_90), d3.format('.2f'));
});
dash.draw('c-bubbles', (el) => {
  if (!ok('clubs')) {
    el.textContent = '—';
    return;
  }
  bubbles(el, dash.data('clubs').data);
});
dash.draw('c-club-season', (el) => {
  if (!ok('club_rollup')) {
    el.textContent = '—';
    return;
  }
  const t = el.dataset.team;
  const c = param(`comp${t}`);
  const rows = dash.data('club_rollup').data.filter((r) => r.team_id === t && r.competition_id === c && r.season_id !== 'All');
  vbars(el, rows, (r) => r.season_id, (r) => r.goals);
});
dash.draw('c-club-comp', (el) => {
  if (!ok('club_rollup')) {
    el.textContent = '—';
    return;
  }
  const t = el.dataset.team;
  const s = param(`season${t}`);
  const rows = dash.data('club_rollup').data.filter((r) => r.team_id === t && r.season_id === s && r.competition_id !== 'All' && r.appearances > 0).sort(descending((r) => r.goals));
  hbars(el, rows, (r) => r.competition, (r) => r.goals);
});
dash.draw('c-club-type', (el) => {
  if (!ok('goal_types')) {
    el.textContent = '—';
    return;
  }
  const t = el.dataset.team;
  const s = param(`season${t}`);
  const c = param(`comp${t}`);
  const rows = dash.data('goal_types').data.filter((r) => r.team_id === t && (s === 'All' || r.season_id === s) && (c === 'All' || r.competition_id === c));
  const groups = d3.rollups(rows, (v) => d3.sum(v, (r) => r.goals), (r) => r.situation).map(([situation, goals]) => ({situation, goals})).sort(descending((r) => r.goals));
  hbars(el, groups, (r) => r.situation, (r) => r.goals);
});
const intlRows = (group) => (ok('intl') ? dash.data('intl').data.filter((r) => r.metric_group === group) : []);
dash.draw('c-intl-year', (el) => {
  const rows = intlRows('By calendar year');
  if (!rows.length) {
    el.textContent = '—';
    return;
  }
  vbars(el, rows, (r) => r.item, (r) => Number(r.goals));
});
['By opponent confederation:c-intl-region', 'By competition:c-intl-comp', 'Home, away, neutral:c-intl-venue'].forEach((pair) => {
  const [group, name] = pair.split(':');
  dash.draw(name, (el) => {
    const rows = intlRows(group).sort(descending((r) => Number(r.goals)));
    hbars(el, rows, (r) => r.item, (r) => Number(r.goals));
  });
});
dash.draw('c-edition-goals', (el) => {
  const id = el.dataset.source;
  if (!ok(id)) {
    el.textContent = '—';
    return;
  }
  vbars(el, dash.data(id).data, (r) => r.tournament_id, (r) => Number(r.goals));
});
dash.draw('c-edition-both', (el) => {
  const id = el.dataset.source;
  if (!ok(id)) {
    el.textContent = '—';
    return;
  }
  grouped(el, dash.data(id).data, (r) => r.tournament_id, [{name: 'Goals', value: (r) => Number(r.goals)}, {name: 'Assists', value: (r) => Number(r.assists)}]);
});
dash.draw('c-stage', (el) => {
  if (!ok('stage_goals')) {
    el.textContent = '—';
    return;
  }
  const pick = param(el.dataset.param);
  const rows = dash.data('stage_goals').data.filter((r) => r.competition_id === el.dataset.comp && (pick === 'All' || r.tournament_id === pick));
  const groups = d3.rollups(rows, (v) => d3.sum(v, (r) => r.goals), (r) => r.stage).map(([stage, goals]) => ({stage, goals})).sort((a, b) => STAGES.indexOf(a.stage) - STAGES.indexOf(b.stage));
  hbars(el, groups, (r) => r.stage, (r) => r.goals);
});
dash.draw('c-opp', (el) => {
  if (!ok('opp_goals')) {
    el.textContent = '—';
    return;
  }
  const pick = param(el.dataset.param);
  const rows = dash.data('opp_goals').data.filter((r) => r.competition_id === el.dataset.comp && (pick === 'All' || r.tournament_id === pick));
  const groups = d3.rollups(rows, (v) => d3.sum(v, (r) => r.goals), (r) => r.opponent).map(([opponent, goals]) => ({opponent, goals})).filter((r) => r.goals > 0).sort(descending((r) => r.goals));
  hbars(el, groups, (r) => r.opponent, (r) => r.goals);
});
dash.draw('c-trophy-team', (el) => {
  if (!ok('trophy_team')) {
    el.textContent = '—';
    return;
  }
  hbars(el, [...dash.data('trophy_team').data].sort(descending((r) => r.trophies_won)), (r) => r.team, (r) => r.trophies_won);
});
dash.draw('c-award-cat', (el) => {
  if (!ok('award_cat')) {
    el.textContent = '—';
    return;
  }
  hbars(el, [...dash.data('award_cat').data].sort(descending((r) => r.awards_won)), (r) => r.award_category, (r) => r.awards_won);
});
dash.draw('c-quality-area', (el) => {
  if (!ok('quality_area')) {
    el.textContent = '—';
    return;
  }
  const rows = dash.data('quality_area').data;
  const areas = [...new Set(rows.map((r) => r.area))];
  const keys = ['PASS', 'EXPLAINED', 'INFO', 'REVIEW', 'FAIL'].filter((k) => rows.some((r) => r.status === k));
  const value = (a, k) => d3.sum(rows.filter((r) => r.area === a && r.status === k), (r) => r.checks);
  const color = {PASS: 'var(--color-ok)', EXPLAINED: cols()[0], INFO: 'var(--cds-chart-muted)', REVIEW: 'var(--color-warn)', FAIL: 'var(--color-bad)'};
  stacked(el, areas, keys, value, (k) => color[k], (k) => k.charAt(0) + k.slice(1).toLowerCase());
});

/* Images, and the story's running tally */
dash.draw('photo', (img) => {
  const key = img.dataset.img === 'siuu' && calm() ? 'siuu_still' : img.dataset.img;
  const src = (window.CRX_IMG || {})[key];
  if (src && img.getAttribute('src') !== src) img.src = src;
});
let beat = 1;
dash.draw('beat', (el) => {
  const g = dash.data('story_beats');
  if (g.status !== 'ok') {
    el.textContent = '—';
    return;
  }
  el.dataset.where = `beat=${beat}`;
  const to = g.data.find((r) => r.beat === beat)[el.dataset.field];
  if (el._at === undefined) {
    el._at = to;
    el.textContent = fmtInt(to);
  } else if (el._at !== to) {
    countTo(el, to);
  }
});
const markStop = () => {
  document.querySelectorAll('.route li').forEach((li) => {
    const n = Number(li.dataset.stop);
    li.classList.toggle('now', n === beat);
    li.classList.toggle('past', n < beat);
  });
  document.querySelectorAll('.pitch').forEach((p) => p.style.setProperty('--p', String((beat - 1) / 9)));
};
markStop();
const watch = new IntersectionObserver((entries) => {
  for (const e of entries) {
    if (e.isIntersecting) {
      beat = Number(e.target.dataset.beat);
      markStop();
      dash.draw('beat');
    }
  }
}, {root: document, rootMargin: '-45% 0px -45% 0px'});
document.querySelectorAll('.frame[data-beat]').forEach((f) => watch.observe(f));

/* Things slide and pop in as they reach the screen. */
document.querySelectorAll('.crx').forEach((c) => c.classList.add('live'));
const reveal = new IntersectionObserver((entries) => {
  for (const e of entries) {
    if (!e.isIntersecting) continue;
    e.target.classList.add('in');
    reveal.unobserve(e.target);
  }
}, {root: document, threshold: 0.06});
document.querySelectorAll('.frame, .card, .kpi, .story-end').forEach((n) => reveal.observe(n));

/* Photos lean towards the pointer. */
document.querySelectorAll('.photo-card').forEach((card) => {
  card.addEventListener('pointermove', (e) => {
    const box = card.getBoundingClientRect();
    card.style.setProperty('--ry', `${((e.clientX - box.left) / box.width - 0.5) * 12}deg`);
    card.style.setProperty('--rx', `${((e.clientY - box.top) / box.height - 0.5) * -12}deg`);
  });
  card.addEventListener('pointerleave', () => {
    card.style.setProperty('--ry', '0deg');
    card.style.setProperty('--rx', '0deg');
  });
});

/* Motion can be paused, which also swaps the moving clip for a still. */
document.querySelectorAll('.motion').forEach((b) => {
  b.addEventListener('click', () => {
    const on = b.getAttribute('aria-pressed') !== 'true';
    b.setAttribute('aria-pressed', String(on));
    document.querySelectorAll('.crx').forEach((c) => c.classList.toggle('still', on));
    dash.draw('photo');
  });
});

/* Tabs */
const openTab = (id, write) => {
  const page = document.getElementById(id);
  if (!page || !page.classList.contains('pg')) return;
  document.querySelectorAll('.pg').forEach((p) => {
    p.hidden = p !== page;
  });
  document.querySelectorAll('[role=tab]').forEach((t) => t.setAttribute('aria-selected', String(t.getAttribute('aria-controls') === id)));
  if (write) dash.setLink(id);
};
document.querySelectorAll('[role=tab]').forEach((tab) => {
  tab.addEventListener('click', () => openTab(tab.getAttribute('aria-controls'), true));
});
document.querySelectorAll('[data-goto]').forEach((b) => {
  b.addEventListener('click', () => {
    openTab(b.dataset.goto, true);
    window.scrollTo(0, 0);
  });
});
if (location.hash.length > 1) openTab(location.hash.slice(1), false);
