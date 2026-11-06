/* A small stand-in for the dashboard runtime, so the same app.js runs as a plain static site. */
(function () {
  const DATASETS = {
    matches: 'match_statistics', goals: 'goal_statistics', seasons: 'season_statistics', clubs: 'club_statistics', overview: 'career_overview',
    intl: 'international_statistics', euro: 'euro_statistics', wc: 'world_cup_statistics', tmatches: 'tournament_matches', trophies: 'trophies',
    awards: 'individual_awards', milestones: 'career_milestones', quality: 'data_quality_report', sources: 'data_sources', transfers: 'career_transfers',
  };
  const tables = new Map();
  const calcs = new Map();
  const painters = new Map();
  const listeners = [];
  const state = {};
  let ready = false;

  const inView = (el) => !el.closest('[hidden]');
  const paint = (el) => {
    const fn = painters.get(el.dataset.draw);
    if (!fn || !inView(el)) return;
    try {
      fn(el);
    } catch (err) {
      console.error(`Drawing ${el.dataset.draw} failed`, err);
    }
  };
  const paintAll = (root = document) => {
    if (!ready) return;
    listeners.forEach((fn) => fn());
    root.querySelectorAll('[data-draw]').forEach(paint);
  };

  window.dash = {
    colors: [],
    calc(id, spec) {
      calcs.set(id, spec);
    },
    data(id) {
      return tables.has(id) ? {status: 'ok', data: tables.get(id)} : {status: 'loading', data: []};
    },
    draw(name, fn) {
      if (fn) {
        painters.set(name, fn);
        return;
      }
      if (ready) document.querySelectorAll(`[data-draw="${name}"]`).forEach(paint);
    },
    onData(fn) {
      listeners.push(fn);
    },
    params: () => ({...state}),
    setParams(next) {
      for (const [k, v] of Object.entries(next)) {
        if (v === null || v === undefined) delete state[k];
        else state[k] = v;
      }
      paintAll();
    },
    setLink(id) {
      history.replaceState(null, '', `#${id}`);
    },
  };

  const load = async () => {
    await Promise.all(Object.entries(DATASETS).map(async ([id, file]) => {
      const res = await fetch(`data/${file}.csv`);
      if (!res.ok) throw new Error(`${file}: ${res.status}`);
      tables.set(id, d3.csvParse((await res.text()).replace(/^﻿/, '')));
    }));
    for (const [id, spec] of calcs) tables.set(id, spec.fn(...spec.inputs.map((k) => tables.get(k))));
    ready = true;
    paintAll();

    /* A tab drawn for the first time, and anything that changes width, is drawn again. */
    new MutationObserver((changes) => {
      for (const c of changes) if (!c.target.hidden) paintAll(c.target);
    }).observe(document.querySelector('.crx'), {subtree: true, attributes: true, attributeFilter: ['hidden']});
    let wide = window.innerWidth;
    let wait;
    window.addEventListener('resize', () => {
      if (window.innerWidth === wide) return;
      wide = window.innerWidth;
      clearTimeout(wait);
      wait = setTimeout(() => document.querySelectorAll('.chart[data-draw]').forEach(paint), 150);
    });
  };
  window.addEventListener('DOMContentLoaded', () => load().catch((err) => {
    console.error(err);
    document.querySelectorAll('.load-error').forEach((n) => {
      n.hidden = false;
    });
  }));
})();
