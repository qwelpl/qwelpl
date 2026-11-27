import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from html import escape
from pathlib import Path

LOGIN = "qwelpl"
OUT = Path(__file__).resolve().parent.parent / "assets"

THEMES = {
    "light": {
        "bg": "#ffffff",
        "card": "#f6f8fa",
        "border": "#d0d7de",
        "fg": "#1f2328",
        "mute": "#656d76",
        "faint": "#8c959f",
        "cells": ["#ebedf0", "#c4c9cf", "#9aa1a9", "#6e7781", "#32383f"],
        "bars": ["#24292f", "#57606a", "#8c959f", "#afb8c1", "#d0d7de", "#eaeef2"],
    },
    "dark": {
        "bg": "#0d1117",
        "card": "#11161d",
        "border": "#262c36",
        "fg": "#e6edf3",
        "mute": "#8b949e",
        "faint": "#6e7681",
        "cells": ["#161b22", "#2d333b", "#484f58", "#6e7681", "#c9d1d9"],
        "bars": ["#e6edf3", "#adbac7", "#768390", "#545d68", "#373e47", "#2d333b"],
    },
}

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace"

LINKS = [
    ("site", "tile-drop.com/q_welpl", "web"),
    ("email", "say hi", "mail"),
    ("instagram", "say hi (p2)", "ig"),
]

ICONS = {
    "star": '<path d="M0.00 -6.20 L1.59 -2.18 L5.90 -1.92 L2.57 0.83 L3.64 5.02 L0.00 2.70 L-3.64 5.02 L-2.57 0.83 L-5.90 -1.92 L-1.59 -2.18Z"/>',
    "pr": '<circle cx="-3.5" cy="-4.5" r="1.7"/><circle cx="-3.5" cy="4.5" r="1.7"/><path d="M-3.5 -2.8v5.6"/>'
    '<circle cx="3.5" cy="4.5" r="1.7"/><path d="M3.5 2.8V-1.5a2 2 0 0 0-2-2H-.5M1 -5.5l-2 2 2 2"/>',
    "commit": '<circle r="2.6"/><path d="M-7 0h4.4M2.6 0H7"/>',
    "review": '<path d="M-7 0c1.8-3.4 4.2-5 7-5s5.2 1.6 7 5c-1.8 3.4-4.2 5-7 5s-5.2-1.6-7-5z"/><circle r="2"/>',
    "repo": '<path d="M-5.5 5.5v-10a1.5 1.5 0 0 1 1.5-1.5h9.5v10H-4a1.5 1.5 0 0 0-1.5 1.5zm0 0a1.5 1.5 0 0 0 1.5 1.5h9.5v-3"/>',
    "issue": '<circle r="5.8"/><circle class="dotfill" r="1.3" stroke="none"/>',
    "user": '<circle cy="-2.6" r="2.8"/><path d="M-5.6 6c.6-3 2.8-4.6 5.6-4.6s5 1.6 5.6 4.6"/>',
}

HUES = [215, 155, 35, 280, 190, 12]
DRIFT = 72

LOOP = 14
LOOP_START = 4

LANG_ICONS = {
    "Swift": "swift",
    "Python": "py",
    "Jupyter Notebook": "py",
    "TypeScript": "ts",
    "JavaScript": "js",
    "HTML": "html",
    "CSS": "css",
    "C++": "cpp",
    "C": "c",
    "Java": "java",
    "Shell": "bash",
    "Ruby": "ruby",
    "Svelte": "svelte",
    "Go": "go",
    "Rust": "rust",
    "Kotlin": "kotlin",
    "Dart": "dart",
    "PHP": "php",
    "Lua": "lua",
}

DEP_ICONS = {
    "next": "nextjs",
    "react": "react",
    "svelte": "svelte",
    "vue": "vue",
    "@supabase/supabase-js": "supabase",
    "tailwindcss": "tailwind",
    "vite": "vite",
    "express": "express",
    "three": "threejs",
    "electron": "electron",
    "firebase": "firebase",
    "prisma": "prisma",
}

PROJECTS = [
    {
        "slug": "tiledrop",
        "name": "tiledrop",
        "desc": ["the thing powering my website.", ""],
        "tags": ["typescript", "web"],
    },
    {
        "slug": "barloom",
        "name": "barloom",
        "desc": ["a windows 11 style taskbar for macOS", "that replaces the dock."],
        "tags": ["swift", "macOS"],
    },
    {
        "slug": "peace",
        "name": "peace",
        "desc": ["a calmer front end for apple music with", "album art visualizers and synced lyrics."],
        "tags": ["swift", "macOS"],
    },
    {
        "slug": "quovine",
        "name": "quovine",
        "desc": ["a collaborative doc editor with live", "cursors, in-doc chat and version history."],
        "tags": ["next.js", "supabase"],
    },
    {
        "slug": "wildfire",
        "name": "wildfire",
        "desc": ["a daily word puzzle. burn the whole 5x5", "board in as few words as you can."],
        "tags": ["javascript", "game"],
    },
    {
        "slug": "mirror-repo",
        "name": "mirror-repo",
        "desc": ["one command for paired gitlab + github", "repos with push mirroring."],
        "tags": ["shell", "cli"],
    },
]


def gql(query, variables=None):
    token = os.environ["GH_TOKEN"]
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        body = json.load(r)
    if "errors" in body:
        raise RuntimeError(body["errors"])
    return body["data"]


def fetch():
    u = gql(
        """query($l:String!){user(login:$l){
        followers{totalCount}
        contributionsCollection{totalCommitContributions restrictedContributionsCount totalPullRequestContributions
        totalIssueContributions totalPullRequestReviewContributions
        contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}
        repositoriesContributedTo(first:1,contributionTypes:[COMMIT,PULL_REQUEST,ISSUE,PULL_REQUEST_REVIEW]){totalCount}
        repositories(first:100,privacy:PUBLIC,ownerAffiliations:OWNER,orderBy:{field:PUSHED_AT,direction:DESC}){
        totalCount nodes{name pushedAt isFork stargazerCount homepageUrl
        pkg:object(expression:"HEAD:package.json"){...on Blob{text}}
        languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name}}}}}}}""",
        {"l": LOGIN},
    )["user"]

    cal = u["contributionsCollection"]["contributionCalendar"]
    days = [(d["date"], d["contributionCount"]) for w in cal["weeks"] for d in w["contributionDays"]]

    langs = {}
    stars = 0
    for r in u["repositories"]["nodes"]:
        stars += r["stargazerCount"]
        if r["isFork"]:
            continue
        for e in r["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]

    longest = run = 0
    for _, n in days:
        run = run + 1 if n else 0
        longest = max(longest, run)
    current = 0
    for i, (_, n) in enumerate(reversed(days)):
        if n:
            current += 1
        elif i == 0:
            continue
        else:
            break

    frameworks = {}
    for r in u["repositories"]["nodes"]:
        if r["isFork"]:
            continue
        found = set()
        if r["pkg"]:
            try:
                pkg = json.loads(r["pkg"]["text"])
            except ValueError:
                pkg = {}
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            found |= {DEP_ICONS[d] for d in deps if d in DEP_ICONS}
        if "vercel.app" in (r["homepageUrl"] or ""):
            found.add("vercel")
        for f in found:
            frameworks[f] = frameworks.get(f, 0) + 1

    counts = gql(
        """query($p:String!,$i:String!){prs:search(query:$p,type:ISSUE,first:0){issueCount}
        issues:search(query:$i,type:ISSUE,first:0){issueCount}}""",
        {"p": f"author:{LOGIN} type:pr", "i": f"author:{LOGIN} type:issue"},
    )

    latest = next(r for r in u["repositories"]["nodes"] if r["name"] != LOGIN and not r["isFork"])

    return {
        "contributions": cal["totalContributions"],
        "gh": {
            "commits": u["contributionsCollection"]["totalCommitContributions"] + u["contributionsCollection"]["restrictedContributionsCount"],
            "prs": u["contributionsCollection"]["totalPullRequestContributions"],
            "issues": u["contributionsCollection"]["totalIssueContributions"],
            "reviews": u["contributionsCollection"]["totalPullRequestReviewContributions"],
            "contributed": u["repositoriesContributedTo"]["totalCount"],
            "all_prs": counts["prs"]["issueCount"],
            "all_issues": counts["issues"]["issueCount"],
        },
        "repos": u["repositories"]["totalCount"],
        "stars": stars,
        "followers": u["followers"]["totalCount"],
        "current": current,
        "longest": longest,
        "latest": latest,
        "days": days,
        "langs": sorted(langs.items(), key=lambda kv: -kv[1]),
        "frameworks": sorted(frameworks, key=lambda k: -frameworks[k]),
    }


def hsl(h, sat, light):
    import colorsys
    r, g, b = colorsys.hls_to_rgb(h / 360, light / 100, sat / 100)
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def drift(t):
    dark = t["bg"] == "#0d1117"
    levels = {
        1: (22, 32 if dark else 80),
        2: (26, 44 if dark else 66),
        3: (30, 58 if dark else 52),
        4: (32, 74 if dark else 36),
    }
    n = len(HUES)
    css = []
    for lvl, (sat, light) in levels.items():
        stops = []
        for i, h in enumerate(HUES + HUES[:1]):
            c = hsl(h, sat, light)
            stops.append(f"{100 * i / n:.2f}%{{fill:{c}}}")
            if i < n:
                stops.append(f"{100 * (i + 0.55) / n:.2f}%{{fill:{c}}}")
        keys = "".join(stops)
        css.append(f"@keyframes d{lvl}{{{keys}}}")
        css.append(f"@keyframes e{lvl}{{{keys.replace('fill:', 'stroke:')}}}")
        css.append(f".a{lvl}{{animation:d{lvl} {DRIFT}s ease-in-out infinite}}")
        css.append(f".s{lvl}{{animation:e{lvl} {DRIFT}s ease-in-out infinite}}")
    return "\n".join(css)


def style(t, extra=""):
    return f"""<style>
{drift(t)}
.bg{{fill:{t['bg']}}}
.card{{fill:{t['card']};stroke:{t['border']};stroke-width:1}}
.fg{{fill:{t['fg']};font-family:{SANS}}}
.mute{{fill:{t['mute']};font-family:{SANS}}}
.faint{{font-family:{MONO}}}
.ico,.arrow,.ic{{animation:e3 {DRIFT}s ease-in-out infinite}}
.tag{{animation:e2 {DRIFT}s ease-in-out infinite}}
.mono{{font-family:{MONO}}}
@keyframes rise{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes draw{{to{{stroke-dashoffset:0}}}}
.r{{opacity:0;animation:rise .8s cubic-bezier(.2,.7,.2,1) forwards}}
.f{{opacity:0;animation:fade 1s ease forwards}}
{extra}
</style>"""


def ago(iso):
    d = datetime.now(timezone.utc) - datetime.fromisoformat(iso.replace("Z", "+00:00"))
    if d.days >= 1:
        return f"{d.days}d ago"
    if d.seconds >= 3600:
        return f"{d.seconds // 3600}h ago"
    return "today"


def header(t, s):
    w, h = 840, 200
    words = ["macOS apps", "web tools", "word games", "dev utilities"]
    cycle = len(words) * 3
    pct = 100 / len(words)
    cyc = []
    for i, word in enumerate(words):
        cyc.append(
            f'<text x="2" y="160" class="word" style="animation-delay:{1.4 + i * 3}s">'
            f'<tspan class="ghost">i build </tspan><tspan class="hl a4">{escape(word)}</tspan></text>'
        )
    top = s["langs"][0][0].lower() if s["langs"] else "-"
    rows = [
        ("latest", s["latest"]["name"]),
        ("pushed", ago(s["latest"]["pushedAt"])),
        ("streak", f"{s['current']} days"),
        ("top lang", top),
        ("based in", "united states"),
    ]
    px, py, pw, ph = 500, 22, 340, 162
    panel = []
    for i, (k, v) in enumerate(rows):
        y = py + 56 + i * 21
        panel.append(
            f'<g class="r" style="animation-delay:{0.6 + i * 0.08:.2f}s">'
            f'<text x="{px + 22}" y="{y}" class="faint" font-size="12">{k}</text>'
            f'<text x="{px + pw - 22}" y="{y}" class="fg mono" font-size="12" text-anchor="end">{escape(v)}</text></g>'
        )
    duo = header_scene(1.35)
    extra = f"""
.word{{font-family:{SANS};font-size:22px;opacity:0;animation:cyc {cycle}s ease-in-out infinite}}
.ghost{{fill:transparent}}
.hl{{font-weight:500}}
@keyframes cyc{{0%{{opacity:0}}{pct*0.15:.2f}%{{opacity:1}}{pct*0.85:.2f}%{{opacity:1}}{pct:.2f}%{{opacity:0}}100%{{opacity:0}}}}
.sep{{stroke:{t['border']};stroke-width:1}}
{fig_css(t['bg'])}
{duo.css()}
"""
    hide = duo.svg(-0.5, scale=1.35)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
{style(t, extra)}
{hide}
<g transform="translate(10,0)">
<text x="2" y="48" class="mute r" font-size="18">hey there, i'm</text>
<text x="0" y="118" class="fg r" font-size="72" font-weight="700" style="animation-delay:.12s">aarav</text>
<text x="2" y="160" class="mute f" font-size="22" style="animation-delay:.9s">i build</text>
{''.join(cyc)}
</g>
<g class="f" style="animation-delay:.4s">
<rect class="card" x="{px + .5}" y="{py + .5}" width="{pw - 1}" height="{ph - 1}" rx="12"/>
<text x="{px + 22}" y="{py + 29}" class="mute" font-size="12">stuff abt me :D</text>
<line class="sep" x1="{px + 22}" y1="{py + 40}" x2="{px + pw - 22}" y2="{py + 40}"/>
</g>
{''.join(panel)}
</svg>"""


def pill(t, label, icon, i):
    tw = len(label) * 7.6
    w, h = int(tw + 50), 32
    extra = f"""
.pl{{fill:{t['card']};stroke:{t['border']};stroke-width:1}}
.ic{{stroke:{t['mute']};stroke-width:1.5;fill:none;stroke-linecap:round;stroke-linejoin:round}}
"""
    icons = {
        "web": '<circle cx="0" cy="0" r="6"/><path d="M-6 0h12M0-6c2.5 3 2.5 9 0 12M0-6c-2.5 3-2.5 9 0 12"/>',
        "mail": '<rect x="-6.5" y="-4.5" width="13" height="9" rx="1.5"/><path d="M-6 -3.5l6 4.5 6-4.5"/>',
        "ig": '<rect x="-6.5" y="-6.5" width="13" height="13" rx="3.8"/><circle r="3"/><circle cx="3.6" cy="-3.6" r=".35"/>',
        "gh": '<path d="M-5 -1l-3 3 3 3M5 -1l3 3-3 3M2 -6l-4 13"/>',
    }
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
{style(t, extra)}
<g class="r" style="animation-delay:{1.2 + i * 0.1:.2f}s">
<rect class="pl" x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{h / 2 - .5}"/>
<g class="ic" transform="translate(20,16)">{icons[icon]}</g>
<text x="34" y="20.5" class="fg" font-size="13" font-weight="500">{escape(label)}</text>
</g>
</svg>"""


def card(t, p, i, k=0):
    w, h = 410, 132
    owner, _, repo = p["name"].rpartition(" / ")
    title = escape(repo)
    if owner:
        title = f'<tspan class="mute" font-weight="400">{escape(owner)} / </tspan>{title}'

    who = card_scene(w, h - 3, k, 1.0)
    pk_css = who.css()
    pk = who.svg(-k * 2.3, scale=1.0)
    if k % 2:
        pk = f'<g transform="translate({w},0) scale(-1,1)">{pk}</g>'
    extra = f"""
.edge{{fill:none;stroke:{t['fg']};stroke-width:1.2;stroke-dasharray:1100;stroke-dashoffset:1100;opacity:.55;animation:draw 1.8s cubic-bezier(.6,0,.2,1) {0.15 * i:.2f}s forwards, fade-out 1.2s ease {1.9 + 0.15 * i:.2f}s forwards, e4 {DRIFT}s ease-in-out infinite}}
@keyframes fade-out{{to{{opacity:0}}}}
.tag{{fill:none;stroke:{t['border']}}}
.arrow{{stroke:{t['mute']};stroke-width:1.5;fill:none;stroke-linecap:round;stroke-linejoin:round}}
.ico{{stroke:{t['mute']};stroke-width:1.4;fill:none;stroke-linecap:round;stroke-linejoin:round}}
.dotfill{{fill:{t['mute']}}}
{fig_css(t['card'])}
{pk_css}
"""
    d = 0.15 * i
    meta = []
    mx = w - 24
    for j, (kind, n) in enumerate(reversed(p.get("meta", []))):
        label = str(n)
        mx -= len(label) * 7.2
        meta.append(
            f'<g class="f" style="animation-delay:{d + 0.8 + j * 0.08:.2f}s">'
            f'<g class="ico" transform="translate({mx - 12:.1f},106)">{ICONS[kind]}</g>'
            f'<text x="{mx:.1f}" y="110.5" class="mute mono" font-size="12">{label}</text></g>'
        )
        mx -= 34
    tags = []
    tx = 24
    for tag in p["tags"]:
        tw = len(tag) * 7.2 + 18
        tags.append(
            f'<g class="f" style="animation-delay:{d + 0.7:.2f}s"><rect class="tag" x="{tx}" y="96" width="{tw:.0f}" height="20" rx="10"/>'
            f'<text x="{tx + 9}" y="110" class="faint" font-size="11">{escape(tag)}</text></g>'
        )
        tx += tw + 8
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
{style(t, extra)}
<rect class="card" x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="12"/>
<rect class="edge" x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="12"/>
{pk}
<text x="24" y="38" class="fg r" font-size="17" font-weight="600" style="animation-delay:{d + 0.2:.2f}s">{title}</text>
<g class="r" style="animation-delay:{d + 0.3:.2f}s"><path class="arrow" d="M376 26 l8 8 l-8 8 M368 34 h15"/></g>
<text x="24" y="62" class="mute r" font-size="13" style="animation-delay:{d + 0.4:.2f}s">{escape(p['desc'][0])}</text>
<text x="24" y="80" class="mute r" font-size="13" style="animation-delay:{d + 0.48:.2f}s">{escape(p['desc'][1])}</text>
{''.join(tags)}
{''.join(meta)}
</svg>"""


def loop(first, delay, again="again"):
    return (
        f"animation:{first} {delay:.2f}s forwards,"
        f"{again} {LOOP}s cubic-bezier(.4,0,.2,1) {LOOP_START + delay:.2f}s infinite"
    )


def stats(t, s):
    w, h = 840, 250
    sr = stats_scene(w, 101.5, 1.25)
    extra = f"""
.cell{{opacity:0;transform-box:fill-box;transform-origin:center}}
@keyframes pop{{from{{opacity:0;transform:scale(.3)}}to{{opacity:1;transform:scale(1)}}}}
@keyframes wave{{0%{{opacity:1;transform:scale(1)}}2.5%{{opacity:.1;transform:scale(.35)}}6%{{opacity:1;transform:scale(1)}}100%{{opacity:1;transform:scale(1)}}}}
@keyframes again{{0%{{opacity:1;transform:translateY(0)}}2%{{opacity:0;transform:translateY(8px)}}6%{{opacity:1;transform:translateY(0)}}100%{{opacity:1;transform:translateY(0)}}}}
.sep{{stroke:{t['border']};stroke-width:1}}
{fig_css(t['card'])}
{sr.css()}
"""
    items = [
        (f"{s['contributions']:,}", "contributions"),
        (f"{s['repos']}", "public repos"),
        (f"{s['stars']}", "stars"),
        (f"{s['followers']}", "followers"),
        (f"{s['longest']}d", "longest streak"),
    ]
    cols = []
    cw = (w - 48) / len(items)
    for i, (v, label) in enumerate(items):
        x = 24 + i * cw
        cols.append(
            f'<text x="{x:.0f}" y="62" class="fg mono r" font-size="28" font-weight="600" style="{loop("rise .8s cubic-bezier(.2,.7,.2,1)", 0.1 + i * 0.1)}">{v}</text>'
            f'<text x="{x:.0f}" y="84" class="mute r" font-size="12" style="{loop("rise .8s cubic-bezier(.2,.7,.2,1)", 0.15 + i * 0.1)}">{label}</text>'
        )
    weeks = 53
    recent = s["days"][-(weeks * 7):]
    first = datetime.fromisoformat(recent[0][0]).weekday()
    offset = (first + 1) % 7
    peak = max([n for _, n in recent] + [1])
    size, gap = 11, 3
    gx0 = (w - weeks * (size + gap) + gap) / 2
    cells = []
    for idx, (_, n) in enumerate(recent):
        k = idx + offset
        col, row = divmod(k, 7)
        if col >= weeks:
            break
        if n == 0:
            lvl = 0
        else:
            lvl = min(4, 1 + int(3 * n / peak + 0.5))
        x = gx0 + col * (size + gap)
        y = 118 + row * (size + gap)
        delay = 0.5 + col * 0.025 + row * 0.02
        fill = "" if lvl else f' fill="{t["cells"][0]}"'
        cells.append(
            f'<g class="a{lvl}"><rect class="cell" x="{x:.1f}" y="{y}" width="{size}" height="{size}" rx="2.5"{fill} style="{loop("pop .5s cubic-bezier(.2,.7,.2,1)", delay, "wave")}"/></g>'
        )
    legend_x = w - 24 - 5 * 14 - 70
    legend = [f'<text x="{legend_x}" y="232" class="faint f" font-size="10" style="animation-delay:2s">less</text>']
    for i in range(5):
        legend.append(
            f'<g class="a{i}"><rect class="f" x="{legend_x + 30 + i * 14}" y="223" width="10" height="10" rx="2"{"" if i else " fill=" + chr(34) + t["cells"][0] + chr(34)} style="animation-delay:2s"/></g>'
        )
    legend.append(
        f'<text x="{legend_x + 30 + 5 * 14 + 4}" y="232" class="faint f" font-size="10" style="animation-delay:2s">more</text>'
    )
    updated = datetime.now(timezone.utc).strftime("%b %d, %Y").lower()
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
{style(t, extra)}
<rect class="card" x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="12"/>
{''.join(cols)}
<line class="sep f" x1="24" y1="102" x2="{w - 24}" y2="102" style="animation-delay:.4s"/>
{sr.svg(-4, scale=1.25)}
{''.join(cells)}
<text x="24" y="232" class="faint f" font-size="10" style="animation-delay:2s">last 12 months  ·  updated {updated}</text>
{''.join(legend)}
</svg>"""


def grade(s):
    g = s["gh"]
    exp = lambda x: 1 - 2 ** -x
    logn = lambda x: x / (1 + x)
    parts = [
        (2, exp(g["commits"] / 250)),
        (3, exp(g["all_prs"] / 50)),
        (1, exp(g["all_issues"] / 25)),
        (1, exp(g["reviews"] / 2)),
        (4, logn(s["stars"] / 50)),
        (1, logn(s["followers"] / 10)),
    ]
    pct = 100 * (1 - sum(w * v for w, v in parts) / sum(w for w, _ in parts))
    levels = [(1, "S"), (12.5, "A+"), (25, "A"), (37.5, "A-"), (50, "B+"), (62.5, "B"), (75, "B-"), (87.5, "C+"), (100, "C")]
    return next(l for t, l in levels if pct <= t), pct


def ghstats(t, s):
    w, h = 840, 220
    g = s["gh"]
    level, pct = grade(s)
    rx, ry, rr = 372, 118, 46
    import math
    circ = 2 * math.pi * rr
    rows = [
        ("commit", "commits", g["commits"]),
        ("pr", "pull requests", g["prs"]),
        ("issue", "issues", g["issues"]),
        ("review", "code reviews", g["reviews"]),
        ("repo", "contributed to", g["contributed"]),
    ]
    extra = f"""
@keyframes again{{0%{{opacity:1;transform:translateY(0)}}2%{{opacity:0;transform:translateY(8px)}}6%{{opacity:1;transform:translateY(0)}}100%{{opacity:1;transform:translateY(0)}}}}
.ico{{stroke:{t['mute']};stroke-width:1.4;fill:none;stroke-linecap:round;stroke-linejoin:round}}
.dotfill{{fill:{t['mute']}}}
.sep{{stroke:{t['border']};stroke-width:1}}
.bar{{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0)}}
@keyframes up{{to{{transform:scaleY(1)}}}}
@keyframes reup{{0%{{transform:scaleY(1)}}3%{{transform:scaleY(0)}}9%{{transform:scaleY(1)}}100%{{transform:scaleY(1)}}}}
.track{{fill:none;stroke:inherit;stroke-width:6}}
.arc{{fill:none;stroke:inherit;stroke-width:6;stroke-linecap:round;stroke-dasharray:{circ:.1f};stroke-dashoffset:{circ:.1f}}}
@keyframes fill{{to{{stroke-dashoffset:{circ - circ * (100 - pct) / 100:.1f}}}}}
@keyframes refill{{0%{{stroke-dashoffset:{circ - circ * (100 - pct) / 100:.1f}}}3%{{stroke-dashoffset:{circ:.1f}}}12%{{stroke-dashoffset:{circ - circ * (100 - pct) / 100:.1f}}}100%{{stroke-dashoffset:{circ - circ * (100 - pct) / 100:.1f}}}}}
"""
    items = []
    for i, (icon, label, n) in enumerate(rows):
        y = 70 + i * 30
        a = loop("rise .8s cubic-bezier(.2,.7,.2,1)", 0.2 + i * 0.08)
        items.append(
            f'<g class="r" style="{a}">'
            f'<g class="ico" transform="translate(32,{y - 4})">{ICONS[icon]}</g>'
            f'<text x="52" y="{y}" class="mute" font-size="13">{label}</text>'
            f'<text x="286" y="{y}" class="fg mono" font-size="13" font-weight="600" text-anchor="end">{n:,}</text></g>'
        )
    months = {}
    for d, n in s["days"]:
        months[d[:7]] = months.get(d[:7], 0) + n
    months = sorted(months.items())[-12:]
    peak = max([n for _, n in months] + [1])
    cx0, cx1, base, top = 470, 816, 176, 60
    bw = (cx1 - cx0) / len(months)
    bars = []
    for i, (m, n) in enumerate(months):
        bh = max(2, (base - top) * n / peak)
        x = cx0 + i * bw + 5
        shade = 4 if n == peak else 3
        bars.append(
            f'<g class="a{shade}"><rect class="bar" x="{x:.1f}" y="{base - bh:.1f}" width="{bw - 10:.1f}" height="{bh:.1f}" rx="3" '
            f'style="{loop("up .9s cubic-bezier(.6,0,.2,1)", 0.3 + i * 0.06, "reup")}"/></g>'
            f'<text x="{x + (bw - 10) / 2:.1f}" y="{base + 18}" class="faint f" font-size="10" text-anchor="middle" style="animation-delay:1s">'
            f'{datetime.strptime(m, "%Y-%m").strftime("%b").lower()[0]}</text>'
        )
        if n == peak:
            bars.append(
                f'<text x="{x + (bw - 10) / 2:.1f}" y="{base - bh - 8:.1f}" class="fg mono f" font-size="11" text-anchor="middle" style="animation-delay:1.2s">{n}</text>'
            )
    spots = [(cx0 - 14, base)] + [
        (cx0 + i * bw + bw / 2, base - max(2, (base - top) * n / peak)) for i, (_, n) in enumerate(months)
    ] + [(cx1 + 12, base)]
    best = 1 + max(range(len(months)), key=lambda i: months[i][1])
    gh = bars_scene(spots, best, base, 1.2)
    extra += fig_css(t['card']) + gh.css()
    hopper = gh.svg(LOOP_START - gh.T, scale=1.2)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
{style(t, extra)}
<rect class="card" x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="12"/>
<text x="24" y="34" class="fg r" font-size="14" font-weight="600">github stats</text>
<text x="286" y="34" class="faint r" font-size="11" text-anchor="end">past year</text>
<text x="476" y="34" class="fg r" font-size="14" font-weight="600">contributions by month</text>
<line class="sep f" x1="306" y1="24" x2="306" y2="{h - 24}" style="animation-delay:.3s"/>
<line class="sep f" x1="440" y1="24" x2="440" y2="{h - 24}" style="animation-delay:.3s"/>
<text x="{rx}" y="34" class="fg r" font-size="14" font-weight="600" text-anchor="middle">rank</text>
<g class="s1"><circle class="track f" cx="{rx}" cy="{ry}" r="{rr}" style="animation-delay:.2s"/></g>
<g class="s4"><circle class="arc" cx="{rx}" cy="{ry}" r="{rr}" transform="rotate(-90 {rx} {ry})" style="animation:fill 1.4s cubic-bezier(.6,0,.2,1) .4s forwards,refill {LOOP}s cubic-bezier(.4,0,.2,1) {LOOP_START + .4}s infinite"/></g>
<text x="{rx}" y="{ry + 10}" class="fg r" font-size="28" font-weight="700" text-anchor="middle" style="animation-delay:.9s">{level}</text>
<text x="{rx}" y="{ry + rr + 30}" class="faint r" font-size="11" text-anchor="middle" style="animation-delay:1s">top {pct:.0f}%</text>
{''.join(items)}
{hopper}
{''.join(bars)}
</svg>"""


def languages(t, s):
    w, h = 840, 112
    top = s["langs"][:5]
    rest = sum(v for _, v in s["langs"][5:])
    if rest:
        top.append(("other", rest))
    total = sum(v for _, v in top) or 1
    rope = rope_scene(40, 800, 45.5, 0.85)
    extra = """
.seg{transform-box:fill-box;transform-origin:left;transform:scaleX(0)}
@keyframes grow{to{transform:scaleX(1)}}
@keyframes regrow{0%{transform:scaleX(1)}3%{transform:scaleX(0)}9%{transform:scaleX(1)}100%{transform:scaleX(1)}}
""" + fig_css(t['card']) + rope.css()
    bx, bw = 24, w - 48
    segs = []
    legend = []
    x = bx
    lx = bx
    for i, (name, v) in enumerate(top):
        sw = bw * v / total
        paint = ""
        segs.append(
            f'<g class="a{max(4 - i, 1)}"><rect class="seg" x="{x:.2f}" y="46" width="{max(sw - 2, 1):.2f}" height="8" rx="2"{paint} style="{loop("grow 1s cubic-bezier(.6,0,.2,1)", 0.1 + i * 0.12, "regrow")}"/></g>'
        )
        x += sw
        label = f"{name.lower()}  {100 * v / total:.1f}%"
        legend.append(
            f'<g class="r" style="animation-delay:{0.6 + i * 0.08:.2f}s"><g class="a{max(4 - i, 1)}"><circle cx="{lx + 5}" cy="86" r="4"{paint} style="stroke:{t["border"]}"/></g>'
            f'<text x="{lx + 16}" y="90" class="mute" font-size="12">{escape(label)}</text></g>'
        )
        lx += len(label) * 6.6 + 40
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
{style(t, extra)}
<rect class="card" x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="12"/>
<clipPath id="c"><rect x="{bx}" y="46" width="{bw}" height="8" rx="4"/></clipPath>
<g clip-path="url(#c)">{''.join(segs)}</g>
{rope.svg(-1, scale=0.85)}
{''.join(legend)}
</svg>"""


ICON_NAMES = {
    "swift": "Swift", "py": "Python", "ts": "TypeScript", "js": "JavaScript", "html": "HTML",
    "css": "CSS", "cpp": "C++", "c": "C", "java": "Java", "bash": "Shell", "ruby": "Ruby",
    "svelte": "Svelte", "go": "Go", "rust": "Rust", "kotlin": "Kotlin", "dart": "Dart",
    "php": "PHP", "lua": "Lua", "nextjs": "Next.js", "react": "React", "vue": "Vue",
    "supabase": "Supabase", "tailwind": "Tailwind CSS", "vite": "Vite", "express": "Express",
    "threejs": "Three.js", "electron": "Electron", "firebase": "Firebase", "prisma": "Prisma",
    "vercel": "Vercel",
}


def stack_icons(s):
    icons = []
    for name, _ in s["langs"]:
        i = LANG_ICONS.get(name)
        if i and i not in icons:
            icons.append(i)
    for f in s["frameworks"]:
        if f not in icons:
            icons.append(f)
    return icons[:14]


def skillicon(icon, theme):
    url = f"https://skillicons.dev/icons?i={icon}&theme={theme}"
    req = urllib.request.Request(url, headers={"User-Agent": "profile-build"})
    with urllib.request.urlopen(req) as r:
        return r.read().decode()


def contributed():
    repos = gql(
        """query($l:String!){user(login:$l){repositoriesContributedTo(first:20,includeUserRepositories:false,
        contributionTypes:[COMMIT,PULL_REQUEST,ISSUE,PULL_REQUEST_REVIEW]){nodes{
        nameWithOwner name owner{login} url description stargazerCount isPrivate primaryLanguage{name}}}}}""",
        {"l": LOGIN},
    )["user"]["repositoriesContributedTo"]["nodes"]
    out = []
    for r in repos:
        if r["isPrivate"]:
            continue
        found = gql(
            """query($q:String!){search(query:$q,type:ISSUE,first:50){nodes{
            ...on PullRequest{merged} ...on Issue{number}}}}""",
            {"q": f"author:{LOGIN} repo:{r['nameWithOwner']}"},
        )["search"]["nodes"]
        merged = sum(1 for n in found if n.get("merged"))
        prs = sum(1 for n in found if "merged" in n)
        issues = sum(1 for n in found if "number" in n)
        tags = []
        if r["primaryLanguage"]:
            tags.append(r["primaryLanguage"]["name"].lower())
        meta = [("star", r["stargazerCount"])]
        if merged:
            meta.append(("pr", merged))
        if issues:
            meta.append(("issue", issues))
        out.append({
            "slug": "contrib-" + r["nameWithOwner"].replace("/", "-").lower(),
            "name": f"{r['owner']['login']} / {r['name']}",
            "desc": wrap(r["description"] or "", 46),
            "tags": tags,
            "meta": meta,
            "url": f"{r['url']}/pulls?q=is%3Apr+author%3A{LOGIN}" if prs else f"{r['url']}/issues?q=is%3Aissue+author%3A{LOGIN}",
            "stars": r["stargazerCount"],
        })
    return sorted(out, key=lambda c: -c["stars"])


def wrap(text, width):
    lines = [""]
    for word in text.split():
        if len(lines[-1]) + len(word) + 1 > width and lines[-1]:
            if len(lines) == 2:
                lines[-1] = lines[-1].rstrip(" ,.") + "..."
                break
            lines.append("")
        lines[-1] = (lines[-1] + " " + word).strip()
    return (lines + [""])[:2]


def pic(slug, alt, width="49%"):
    return (
        f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/{slug}-dark.svg">'
        f'<img alt="{escape(alt)}" src="assets/{slug}-light.svg" width="{width}"></picture>'
    )


def write_readme(contrib, icons):
    readme = OUT.parent / "README.md"
    text = readme.read_text()
    start = text.index("### contributed to")
    end = text.index("### activity")
    links = [f'<a href="{c["url"]}">{pic(c["slug"], c["name"])}</a>' for c in contrib]
    rows = ["&nbsp;".join(links[i:i + 2]) for i in range(0, len(links), 2)]
    block = "### contributed to\n\n" + "\n\n".join(rows) + "\n\n<br>\n\n"
    text = text[:start] + block + text[end:]
    start = text.index("### stack")
    tiles = []
    for icon in icons:
        name = ICON_NAMES.get(icon, icon)
        tiles.append(
            f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/stack/{icon}-dark.svg">'
            f'<img alt="{name}" title="{name}" src="assets/stack/{icon}-light.svg" height="40"></picture>'
        )
    text = text[:start] + "### stack\n\n" + "&nbsp;\n".join(tiles) + "\n"
    readme.write_text(text)


def fig_css(face):
    return f"""
.fig{{fill:none;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round}}
.eye{{fill:{face}}}
"""


# run cycle, as (phase, angle) loops
RUN_THIGH = [(0, -42), (.5, 38), (1, -42)]
RUN_SHIN = [(0, 12), (.3, 18), (.55, 62), (.78, 96), (1, 12)]
RUN_ARM = [(0, 42), (.5, -48), (1, 42)]
RUN_BOB = [(0, 0), (.25, -2.5), (.5, 0), (.75, -2.5), (1, 0)]

STAND = dict(t1=5, s1=3, t2=-5, s2=4, a1=-8, f1=-30, a2=10, f2=-22, tor=0, sink=0, body=0)
CHANNELS = ["pos", "face", "body", "sink", "tor", "t1", "s1", "t2", "s2", "a1", "f1", "a2", "f2", "head", "eyes"]


def cyc(keys, ph):
    ph %= 1
    for (p0, v0), (p1, v1) in zip(keys, keys[1:]):
        if p0 <= ph <= p1:
            return v0 + (v1 - v0) * (ph - p0) / (p1 - p0)
    return keys[-1][1]


def breaks(keys, ph0, ph1):
    import math
    out = []
    for n in range(math.floor(ph0), math.ceil(ph1) + 1):
        for p, _ in keys:
            if ph0 < n + p < ph1:
                out.append(n + p)
    return sorted(out)


def sink_for(t1, s1, t2, s2):
    import math
    foot = lambda a, b: 10 * math.cos(math.radians(a)) + 10 * math.cos(math.radians(a + b))
    return 20 - max(foot(t1, s1), foot(t2, s2))


class Actor:
    """A stick figure whose every joint is keyframed on one shared timeline, so it can run, slow down,
    stand, look around, jump and hide without swapping drawings."""

    def __init__(self, name, x, y, face=1):
        self.name, self.t = name, 0.0
        self.keys = {c: [] for c in CHANNELS}
        self.cur = dict(STAND, pos=(x, y), face=face, head=0, eyes=1.6)
        self.start = dict(self.cur)
        self.mark()

    # --- timeline plumbing ---
    def put(self, c, t, v):
        self.keys[c].append((t, v))
        self.cur[c] = v

    def mark(self, cs=None):
        for c in cs or CHANNELS:
            self.put(c, self.t, self.cur[c])

    def to(self, dur, **vals):
        if any(k in vals for k in ("t1", "s1", "t2", "s2")) and "sink" not in vals:
            legs = {k: vals.get(k, self.cur[k]) for k in ("t1", "s1", "t2", "s2")}
            vals["sink"] = sink_for(**legs)
        self.mark(list(vals))
        self.t += dur
        for c, v in vals.items():
            self.put(c, self.t, v)
        return self

    def wait(self, d):
        self.t += d
        return self

    # --- moves ---
    def stand(self, d=0.2):
        return self.to(d, **STAND)

    def turn(self):
        return self.to(0.16, face=-self.cur["face"])

    def face_to(self, x):
        if (x - self.cur["pos"][0]) * self.cur["face"] < 0:
            self.turn()

    def glance(self, eyes, head=0, d=0.22):
        return self.to(d, eyes=eyes, head=head)

    def tp(self, x, y=None):
        y = self.cur["pos"][1] if y is None else y
        return self.to(0.01, pos=(x, y))

    def run_to(self, x, speed=170, P=0.36, amp=1.0, balance=False):
        self.face_to(x)
        x0, y = self.cur["pos"]
        dur = abs(x - x0) / speed
        t0 = self.t
        blend = min(0.15, dur / 3)
        self.mark()
        self.glance(1.6, 0, d=0)
        self.t = t0
        phase = lambda t: (t - t0) / P
        legs = {
            "t1": (RUN_THIGH, 0, amp), "s1": (RUN_SHIN, 0, amp),
            "t2": (RUN_THIGH, .5, amp), "s2": (RUN_SHIN, .5, amp),
            "body": (RUN_BOB, 0, amp),
        }
        if balance:
            fixed = dict(a1=-85, f1=-15, a2=85, f2=15)
        else:
            legs.update({"a1": (RUN_ARM, .5, amp), "a2": (RUN_ARM, 0, amp)})
            fixed = dict(f1=-85 * min(1, amp + .3), f2=-85 * min(1, amp + .3))
        end = t0 + dur
        for c, (k, off, a) in legs.items():
            times = [t0 + blend] + [t0 + b * P - off * P for b in breaks(k, phase(t0 + blend) + off, phase(end) + off)] + [end]
            for t in sorted(set(round(q, 3) for q in times)):
                self.put(c, t, a * cyc(k, phase(t) + off))
        for c, v in fixed.items():
            self.put(c, t0 + blend, v)
            self.put(c, end, v)
        self.put("tor", t0 + blend, 9 * amp)
        self.put("tor", end, 9 * amp)
        self.put("sink", t0 + blend, 0)
        self.put("sink", end, 0)
        self.put("pos", t0, (x0, y))
        self.put("pos", end, (x, y))
        self.t = end
        self.to(0.2, pos=(x + self.cur["face"] * 4 * amp, y), **STAND)
        return self

    def walk_to(self, x, **kw):
        return self.run_to(x, speed=kw.pop("speed", 55), P=kw.pop("P", 0.6), amp=kw.pop("amp", 0.45), **kw)

    def crouch(self, d=0.12, deep=1.0):
        return self.to(d, t1=-40 * deep, s1=75 * deep, t2=-30 * deep, s2=70 * deep,
                       a1=25, f1=-40, a2=35, f2=-40, tor=14 * deep)

    def jump(self, h=14):
        self.crouch()
        self.to(0.14, body=-h * 0.7, t1=-8, s1=10, t2=6, s2=14, a1=-165, f1=-15, a2=-150, f2=-20, tor=-4, sink=0)
        self.to(0.12, body=-h)
        self.to(0.13, body=-h * 0.55, t1=-20, s1=25, t2=-10, s2=20, sink=0)
        self.to(0.1, body=0, a1=-120, a2=-110)
        self.crouch(0.08, 0.6)
        return self.stand(0.2)

    def hop_to(self, x, y, lift=12):
        self.face_to(x)
        x0, y0 = self.cur["pos"]
        self.crouch(0.08, 0.8)
        self.to(0.05, t1=-8, s1=10, t2=6, s2=14, a1=-160, a2=-150, f1=-15, f2=-15, tor=-3, sink=0)
        for k in range(1, 7):
            u = k / 6
            self.to(0.055, pos=(x0 + (x - x0) * u, y0 + (y - y0) * u - lift * 4 * u * (1 - u)))
        self.crouch(0.06, 0.6)
        return self.stand(0.12)

    def wave(self, n=3):
        self.glance(0, -6)
        self.to(0.18, a1=-150, f1=-40)
        for i in range(n * 2):
            self.to(0.2, f1=10 if i % 2 == 0 else -60)
        return self.to(0.2, a1=STAND["a1"], f1=STAND["f1"])

    def peek(self, d=1.4, lean=32):
        self.to(0.3, tor=lean, head=-6)
        self.glance(1.6, -10)
        self.wait(d / 2)
        self.glance(0.4, 8)
        self.wait(d / 2)
        return self.to(0.25, tor=0, head=0)

    def dance(self, beat=0.3):
        left = dict(a1=-160, f1=-10, a2=40, f2=-30, tor=-9, t1=-14, s1=12, t2=8, s2=6)
        right = dict(a1=40, f1=-30, a2=160, f2=10, tor=9, t1=8, s1=6, t2=-14, s2=12)
        self.glance(0, 0)
        for pose in (left, right, left, right):
            self.to(beat * 0.5, body=0, **pose)
            self.to(beat * 0.5, body=2.5)
        f = self.cur["face"]
        self.to(0.12, body=0, face=-f, a1=-90, f1=0, a2=90, f2=0, tor=0, **{k: STAND[k] for k in ("t1", "s1", "t2", "s2")})
        self.to(0.12, face=f)
        self.to(0.12, face=-f)
        self.to(0.12, face=f)
        self.jump(10)
        for i in range(4):
            sway = 10 if i % 2 == 0 else -10
            self.to(beat, a1=-150 - sway, f1=-15, a2=150 - sway, f2=15, tor=sway, body=1.5 if i % 2 else 0)
        self.stand(0.25)
        return self.glance(1.6, 0)

    def hug(self, hold=1.4):
        self.glance(1.6, 4)
        self.to(0.28, a1=-78, f1=-72, a2=-62, f2=-78, tor=12, body=-1)
        for i in range(3):
            self.to(hold / 3, tor=17 if i % 2 == 0 else 9, head=8 if i % 2 == 0 else 2)
        self.to(0.28, tor=0, head=0, body=0, **{k: STAND[k] for k in ("a1", "f1", "a2", "f2")})
        return self

    def look_around(self):
        self.glance(1.6, -8).wait(0.45)
        self.turn().glance(1.6, 4).wait(0.5)
        self.turn().glance(0, 0).wait(0.35)
        return self

    def finish(self, T=None):
        T = T or self.t + 0.01
        assert T >= self.t - 1e-6, (self.name, T, self.t)
        self.t = T
        for c in CHANNELS:
            self.put(c, T, self.start[c])
        self.T = T
        return self

    # --- output ---
    def fmt(self, c, v):
        if c == "pos":
            return f"transform:translate({v[0]:.1f}px,{v[1]:.1f}px)"
        if c == "face":
            return f"transform:scaleX({v:.2f})"
        if c in ("body", "sink"):
            return f"transform:translateY({v:.1f}px)"
        if c == "eyes":
            return f"transform:translateX({v:.1f}px)"
        return f"transform:rotate({v:.0f}deg)"

    def css(self):
        out = []
        for c, pts in self.keys.items():
            pts = sorted(pts, key=lambda q: q[0])
            slim = [pts[0]]
            for i in range(1, len(pts) - 1):
                if not (pts[i][1] == slim[-1][1] == pts[i + 1][1]):
                    slim.append(pts[i])
            slim.append(pts[-1])
            keys = "".join(f"{100 * t / self.T:.3f}%{{{self.fmt(c, v)}}}" for t, v in slim)
            out.append(f"@keyframes {self.name}-{c}{{{keys}}}")
        return "\n".join(out)

    def svg(self, delay=0.0, cls="s4", scale=1.0):
        st = lambda c: f"animation:{self.name}-{c} {self.T:.2f}s linear {delay:.2f}s infinite"
        g = lambda c, inner: f'<g style="{st(c)}">{inner}</g>'
        leg = lambda a, b: g(a, '<line x1="0" y1="0" x2="0" y2="10"/><g transform="translate(0,10)">'
                             + g(b, '<line x1="0" y1="0" x2="0" y2="10"/>') + '</g>')
        arm = lambda a, b: g(a, '<line x1="0" y1="0" x2="0" y2="7"/><g transform="translate(0,7)">'
                             + g(b, '<line x1="0" y1="0" x2="0" y2="7"/>') + '</g>')
        face = g("eyes", '<circle class="eye" cx="-1.9" cy="-1" r=".9"/><circle class="eye" cx="1.9" cy="-1" r=".9"/>')
        upper = (
            '<line x1="0" y1="0" x2="0" y2="-15"/>'
            f'<g transform="translate(0,-13)">{arm("a2", "f2")}{arm("a1", "f1")}</g>'
            f'<g transform="translate(0,-20.6)">{g("head", "<circle class=\"a4\" stroke=\"none\" r=\"5.4\"/>" + face)}</g>'
        )
        body = f'<g transform="translate(0,-20)">{leg("t2", "s2")}{leg("t1", "s1")}{g("tor", upper)}</g>'
        fig = g("face", g("body", g("sink", body)))
        return f'<g class="{cls}"><g class="fig">{g("pos", f"<g transform=\"scale({scale})\">{fig}</g>")}</g></g>'


class Duo:
    """Figures that share one clock, so they can react to each other."""

    def __init__(self, *actors):
        self.actors = actors

    def finish(self, T=None):
        T = T or max(a.t for a in self.actors) + 0.01
        for a in self.actors:
            a.finish(T)
        self.T = T
        return self

    def css(self):
        return "\n".join(a.css() for a in self.actors)

    def svg(self, delay=0.0, scale=1.0):
        cls = ["s4", "s3"]
        return "".join(a.svg(delay, cls[i % 2], scale) for i, a in enumerate(self.actors))


def sync(*xs):
    t = max(a.t for a in xs)
    for a in xs:
        a.wait(t - a.t)


def face_each(a, b):
    a.face_to(b.cur["pos"][0])
    b.face_to(a.cur["pos"][0])


def high_five(a, b):
    sync(a, b)
    face_each(a, b)
    sync(a, b)
    for x in (a, b):
        x.glance(1.6, -4)
        x.crouch(0.1, 0.5)
        x.to(0.14, body=-7, t1=-6, s1=8, t2=6, s2=10, sink=0, a1=-155, f1=-25, tor=-4)
        x.to(0.1, body=-8)
        x.to(0.14, body=0, a1=-140)
        x.crouch(0.07, 0.5)
        x.stand(0.2)
    sync(a, b)


def approach(mover, other, gap):
    d = 1 if other.cur["pos"][0] > mover.cur["pos"][0] else -1
    mover.run_to(other.cur["pos"][0] - d * (gap + 4))


def dance_off(a, b):
    sync(a, b)
    face_each(a, b)
    sync(a, b)
    a.dance()
    b.dance()
    sync(a, b)


def hug(a, b, S):
    approach(a, b, 9 * S)
    sync(a, b)
    face_each(a, b)
    sync(a, b)
    a.hug()
    b.hug()
    sync(a, b)


def tap(a, b):
    """a reaches out and taps b, who jumps and spins round."""
    sync(a, b)
    a.to(0.15, a1=-95, f1=-30, tor=6).wait(0.15).to(0.18, a1=STAND["a1"], f1=STAND["f1"], tor=-6)
    b.wait(0.2).glance(-1.6, 6, d=0.1)
    b.jump(16)
    b.turn()
    a.wait(0.3).to(0.2, tor=0)
    sync(a, b)


def header_scene(S):
    g = 176
    a = Actor("ha", 600, g, face=-1)
    b = Actor("hb", 720, g, face=-1)
    a.wait(1).walk_to(525).peek().run_to(340).look_around()
    b.wait(4.2).walk_to(340 + 18 * S, speed=60)
    tap(b, a)
    hug(b, a, S)
    b.run_to(b.cur["pos"][0] + 26 * S)
    dance_off(a, b)
    for x in (a, b):
        x.glance(0, 0).wait(0.4)
    b.turn().run_to(650)
    a.wait(0.35).run_to(690)
    sync(a, b)
    for x in (a, b):
        x.wait(1.2)
    a.run_to(600)
    b.run_to(720).turn()
    return Duo(a, b).finish()


def card_scene(w, g, k, S):
    a = Actor("pa", w + 30, g, face=-1)
    b = Actor("pb", w + 30, g, face=-1)
    a.wait(0.5).run_to(250).look_around()
    b.wait(2.4).walk_to(w - 22).glance(1.6, -6).wait(0.3)
    sync(a, b)
    a.turn().glance(1.6, 0).wave(2)
    b.wait(0.45).wave(2)
    sync(a, b)
    if k % 3 == 0:
        b.run_to(250 + 18 * S)
        high_five(a, b)
    elif k % 3 == 1:
        b.run_to(250 + 30 * S)
        dance_off(a, b)
    else:
        hug(b, a, S)
    a.turn().run_to(-30)
    b.wait(0.35).run_to(-30)
    sync(a, b)
    for x in (a, b):
        x.tp(w + 30).wait(0.6 + (k % 3) * 0.6)
    return Duo(a, b).finish()


def stats_scene(w, g, S):
    a = Actor("sa", w + 40, g, face=-1)
    b = Actor("sb", w + 90, g, face=-1)
    a.wait(1).run_to(620)
    b.wait(1.3).run_to(620 + 22 * S)
    sync(a, b)
    for x in (a, b):
        x.glance(1.6, 16).wait(0.8)
    a.turn().glance(1.6, 0)
    b.wait(0.2).glance(1.6, -4)
    sync(a, b)
    dance_off(a, b)
    b.run_to(430)
    a.wait(0.3).run_to(430 + 22 * S)
    sync(a, b)
    b.turn().wave(2)
    a.wait(0.3).wave(2)
    sync(a, b)
    b.turn().run_to(-40)
    a.wait(0.3).run_to(-90)
    sync(a, b)
    a.wait(2).tp(w + 40).turn()
    b.wait(2).tp(w + 90).turn()
    return Duo(a, b).finish()


def bars_scene(spots, best, floor, S):
    left, right = spots[0], spots[-1]
    a = Actor("ga", right[0], floor, face=-1)
    b = Actor("gb", 870, floor, face=-1)
    a.run_to(left[0] + 10)
    b.wait(0.25).run_to(left[0] - 6).glance(1.6, 0)
    a.glance(0, 0).wait(0.25).turn().glance(1.6, -6).wait(0.2)
    sync(a, b)
    b.turn().glance(1.6, -10)
    for j, (x, y) in enumerate(spots[1:], 1):
        lift = 10 + max(0, a.cur["pos"][1] - y) * 0.6
        a.hop_to(x, y, lift)
        if j == best:
            sync(a, b)
            a.glance(0.6, 14).wave(2)
            b.wait(0.3).jump(13).wave(1)
            sync(a, b)
            b.glance(1.6, -10)
    assert a.t < 14.2, a.t
    a.run_to(left[0] - 6 + 18 * S)
    b.face_to(a.cur["pos"][0])
    high_five(b, a)
    b.turn().run_to(right[0])
    a.wait(0.3).run_to(right[0] - 24 * S)
    sync(a, b)
    for x in (a, b):
        x.look_around()
    b.run_to(870)
    a.run_to(right[0]).wait(0.6)
    if a.cur["face"] > 0:
        a.turn()
    if b.cur["face"] > 0:
        b.turn()
    return Duo(a, b).finish(28)


def rope_scene(x0, x1, y, S):
    a = Actor("la", x0, y, face=1)
    b = Actor("lb", x1, y, face=-1)
    mid = (x0 + x1) / 2
    gap = 26 * S

    def meet(lead, duck, extra):
        near = 7 * S if extra == "hug" else gap / 2
        lead.walk_to(mid - lead.cur["face"] * near, balance=True)
        duck.walk_to(mid - duck.cur["face"] * near, balance=True)
        sync(lead, duck)
        for x in (lead, duck):
            x.glance(1.6, 0).wait(0.4)
        if extra == "hug":
            lead.hug()
            duck.hug()
        else:
            lead.dance()
            duck.dance()
        sync(lead, duck)
        duck.crouch(0.3, 1.1).wait(0.9)
        lead.wait(0.2).hop_to(mid + lead.cur["face"] * gap, y, 28 * S)
        sync(lead, duck)
        duck.stand(0.25)
        for x in (lead, duck):
            x.turn().glance(0, 0)
        lead.wave(2)
        duck.wait(0.3).wave(1)
        sync(lead, duck)
        lead.turn()
        duck.turn()

    meet(a, b, "hug")
    a.walk_to(x1, balance=True).turn()
    b.walk_to(x0, balance=True).turn()
    sync(a, b)
    meet(b, a, "dance")
    b.walk_to(x1, balance=True).turn()
    a.walk_to(x0, balance=True).turn()
    return Duo(a, b).finish()


def tint(svg):
    head, _, body = svg.partition("</style>")
    body, _, tail = body.rpartition("</svg>")
    return f'{head}</style>\n<g class="a3">{body}</g>\n</svg>{tail}'


def tiledrop_users():
    try:
        req = urllib.request.Request("https://tile-drop.com", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            html = r.read().decode()
        return int(re.search(r'target\\*":(\d+)', html).group(1))
    except Exception:
        return None


def main():
    OUT.mkdir(exist_ok=True)
    users = tiledrop_users()
    for p in PROJECTS:
        if p["slug"] == "tiledrop" and users is not None:
            p["meta"] = [("user", f"{users:,} users")]
    s = fetch()
    contrib = contributed()
    icons = stack_icons(s)
    (OUT / "stack").mkdir(exist_ok=True)
    for old in (OUT / "stack").glob("*.svg"):
        if old.name.rsplit("-", 1)[0] not in icons:
            old.unlink()
    for old in OUT.glob("stack-*.svg"):
        old.unlink()
    for name, t in THEMES.items():
        (OUT / f"header-{name}.svg").write_text(tint(header(t, s)))
        (OUT / f"stats-{name}.svg").write_text(tint(stats(t, s)))
        (OUT / f"ghstats-{name}.svg").write_text(tint(ghstats(t, s)))
        (OUT / f"langs-{name}.svg").write_text(tint(languages(t, s)))
        for i, (slug, label, icon) in enumerate(LINKS):
            (OUT / f"link-{slug}-{name}.svg").write_text(tint(pill(t, label, icon, i)))
        for i, p in enumerate(PROJECTS):
            (OUT / f"{p['slug']}-{name}.svg").write_text(tint(card(t, p, i % 2, i)))
        for icon in icons:
            (OUT / "stack" / f"{icon}-{name}.svg").write_text(skillicon(icon, name))
        for i, c in enumerate(contrib):
            (OUT / f"{c['slug']}-{name}.svg").write_text(tint(card(t, c, i % 2, i + len(PROJECTS))))
    for old in OUT.glob("contrib-*.svg"):
        if not any(old.name.startswith(c["slug"] + "-") for c in contrib):
            old.unlink()
    write_readme(contrib, icons)
    print(json.dumps({k: v for k, v in s.items() if k not in ("days", "langs", "latest")}))


if __name__ == "__main__":
    main()
