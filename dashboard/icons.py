"""Line icons drawn for this dashboard, inlined so they take the colour of their text."""
import re

P = {
    "ball": '<circle cx="12" cy="12" r="10"/><path d="M12 7l4.5 3.3-1.7 5.2H9.2L7.5 10.3zM12 7V2.2M16.5 10.3l4.6-1.6M14.8 15.5l2.9 4M9.2 15.5l-2.9 4M7.5 10.3L2.9 8.7"/>',
    "trophy": '<path d="M7 4h10v6a5 5 0 0 1-10 0zM7 5H4v2a3 3 0 0 0 3 3M17 5h3v2a3 3 0 0 1-3 3M12 15v4M8 20h8"/>',
    "crown": '<path d="M3 20h18M4 17L3 6l5 4 4-7 4 7 5-4-1 11z"/>',
    "star": '<path d="M12 3l2.7 5.8 6.3.8-4.6 4.4 1.2 6.3L12 17l-5.6 3.1 1.2-6.3L3 9.6l6.3-.8z"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "flame": '<path d="M12 3c1 4 6 6 6 11a6 6 0 0 1-12 0c0-2 1-3.5 2-4.5 0 2 1 3 2 3 0-3 0-6 2-9.5z"/>',
    "pin": '<path d="M12 22s7-6.5 7-12a7 7 0 1 0-14 0c0 5.5 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/>',
    "plane": '<path d="M2 12l20-9-6 19-4-8zM12 14l4-4"/>',
    "shield": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
    "flag": '<path d="M5 21V4M5 4h13l-3 4 3 4H5"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "bars": '<path d="M5 20V10M11 20V4M17 20v-7M2 20h20"/>',
    "check": '<circle cx="12" cy="12" r="10"/><path d="M8 12l3 3 5-6"/>',
    "shirt": '<path d="M8 3L3 6l2 4 2-1v12h10V9l2 1 2-4-5-3c-1 2-7 2-8 0z"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2c3 3 4 6.5 4 10s-1 7-4 10c-3-3-4-6.5-4-10s1-7 4-10z"/>',
    "bolt": '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
    "book": '<path d="M4 5a2 2 0 0 1 2-2h14v16H6a2 2 0 0 0-2 2zM8 7h8"/>',
    "up": '<path d="M3 17l6-6 4 4 8-8M15 7h6v6"/>',
    "scale": '<path d="M12 3v18M7 21h10M5 7h14M5 7l-3 7h6zM19 7l-3 7h6z"/>',
    "boot": '<path d="M4 4h6l1 6 8 3a3 3 0 0 1 2 3v2H4zM7 21v-3M13 21v-3M19 21v-3"/>',
    "medal": '<path d="M8 2l4 7 4-7"/><circle cx="12" cy="15.5" r="6.5"/>',
    "pause": '<path d="M9 5v14M15 5v14"/>',
    "wave": '<path d="M2 9c3-3 5-3 8 0s5 3 8 0 3-2 4-2M2 16c3-3 5-3 8 0s5 3 8 0 3-2 4-2"/>',
    "home": '<path d="M3 11l9-8 9 8M5 9.5V21h14V9.5"/>',
    "alert": '<path d="M12 3l10 18H2zM12 10v5M12 18v.5"/>',
}


def icon(name, cls="i"):
    return f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{P[name]}</svg>'


RULES = [
    (r"ballon|award|major", "crown"), (r"golden shoe", "boot"), (r"trophy|trophies|cabinet|honour", "trophy"),
    (r"assist", "target"), (r"per 90|minutes per|rate", "bolt"), (r"minute|time", "clock"), (r"hat-trick|peak|best|longest|running", "flame"),
    (r"goal", "ball"), (r"cap|appearance|match|apps", "shirt"), (r"tournament|stage", "medal"), (r"yellow|red card|open|gap|keep in mind|fail|blocked", "alert"),
    (r"pass|check|explained|coverage", "check"), (r"source", "book"), (r"opponent|region|home, away|born", "globe"), (r"year|season", "calendar"),
    (r"move|career", "plane"), (r"age|progress", "up"), (r"moment|record|first club|world cups", "star"), (r"spell|volume|compar", "scale"),
]


def icon_for(label):
    low = re.sub(r"<[^>]+>", "", label).lower()
    for rx, name in RULES:
        if re.search(rx, low):
            return icon(name)
    return icon("bars")
