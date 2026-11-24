import json
import os
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
]

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
        "slug": "tiledrop",
        "name": "tiledrop",
        "desc": ["the thing powering my website.", ""],
        "tags": ["typescript", "web"],
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
        contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}
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

    latest = next(r for r in u["repositories"]["nodes"] if r["name"] != LOGIN and not r["isFork"])

    return {
        "contributions": cal["totalContributions"],
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


def style(t, extra=""):
    return f"""<style>
.bg{{fill:{t['bg']}}}
.card{{fill:{t['card']};stroke:{t['border']};stroke-width:1}}
.fg{{fill:{t['fg']};font-family:{SANS}}}
.mute{{fill:{t['mute']};font-family:{SANS}}}
.faint{{fill:{t['faint']};font-family:{MONO}}}
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
            f'<tspan class="ghost">i build </tspan><tspan class="hl">{escape(word)}</tspan></text>'
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
    extra = f"""
.word{{font-family:{SANS};font-size:22px;opacity:0;animation:cyc {cycle}s ease-in-out infinite}}
.ghost{{fill:transparent}}
.hl{{fill:{t['fg']};font-weight:500}}
@keyframes cyc{{0%{{opacity:0}}{pct*0.15:.2f}%{{opacity:1}}{pct*0.85:.2f}%{{opacity:1}}{pct:.2f}%{{opacity:0}}100%{{opacity:0}}}}
.live{{fill:{t['fg']};animation:pulse 2.4s ease-in-out infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.25}}}}
.sep{{stroke:{t['border']};stroke-width:1}}
"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
{style(t, extra)}
<g transform="translate(10,0)">
<text x="2" y="48" class="mute r" font-size="18">hey there, i'm</text>
<text x="0" y="118" class="fg r" font-size="72" font-weight="700" style="animation-delay:.12s">aarav</text>
<text x="2" y="160" class="mute f" font-size="22" style="animation-delay:.9s">i build</text>
{''.join(cyc)}
</g>
<g class="f" style="animation-delay:.4s">
<rect class="card" x="{px + .5}" y="{py + .5}" width="{pw - 1}" height="{ph - 1}" rx="12"/>
<circle class="live" cx="{px + 26}" cy="{py + 25}" r="3.5"/>
<text x="{px + 38}" y="{py + 29}" class="mute" font-size="12">right now</text>
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


def card(t, p, i):
    w, h = 410, 132
    owner, _, repo = p["name"].rpartition(" / ")
    title = escape(repo)
    if owner:
        title = f'<tspan class="mute" font-weight="400">{escape(owner)} / </tspan>{title}'

    extra = f"""
.edge{{fill:none;stroke:{t['fg']};stroke-width:1.2;stroke-dasharray:1100;stroke-dashoffset:1100;opacity:.55;animation:draw 1.8s cubic-bezier(.6,0,.2,1) {0.15 * i:.2f}s forwards, fade-out 1.2s ease {1.9 + 0.15 * i:.2f}s forwards}}
@keyframes fade-out{{to{{opacity:0}}}}
.tag{{fill:none;stroke:{t['border']}}}
.arrow{{stroke:{t['mute']};stroke-width:1.5;fill:none;stroke-linecap:round;stroke-linejoin:round}}
"""
    d = 0.15 * i
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
<text x="24" y="38" class="fg r" font-size="17" font-weight="600" style="animation-delay:{d + 0.2:.2f}s">{title}</text>
<g class="r" style="animation-delay:{d + 0.3:.2f}s"><path class="arrow" d="M376 26 l8 8 l-8 8 M368 34 h15"/></g>
<text x="24" y="62" class="mute r" font-size="13" style="animation-delay:{d + 0.4:.2f}s">{escape(p['desc'][0])}</text>
<text x="24" y="80" class="mute r" font-size="13" style="animation-delay:{d + 0.48:.2f}s">{escape(p['desc'][1])}</text>
{''.join(tags)}
</svg>"""


def loop(first, delay, again="again"):
    return (
        f"animation:{first} {delay:.2f}s forwards,"
        f"{again} {LOOP}s cubic-bezier(.4,0,.2,1) {LOOP_START + delay:.2f}s infinite"
    )


def stats(t, s):
    w, h = 840, 250
    extra = f"""
.cell{{opacity:0;transform-box:fill-box;transform-origin:center}}
@keyframes pop{{from{{opacity:0;transform:scale(.3)}}to{{opacity:1;transform:scale(1)}}}}
@keyframes wave{{0%{{opacity:1;transform:scale(1)}}2.5%{{opacity:.1;transform:scale(.35)}}6%{{opacity:1;transform:scale(1)}}100%{{opacity:1;transform:scale(1)}}}}
@keyframes again{{0%{{opacity:1;transform:translateY(0)}}2%{{opacity:0;transform:translateY(8px)}}6%{{opacity:1;transform:translateY(0)}}100%{{opacity:1;transform:translateY(0)}}}}
.sep{{stroke:{t['border']};stroke-width:1}}
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
        cells.append(
            f'<rect class="cell" x="{x:.1f}" y="{y}" width="{size}" height="{size}" rx="2.5" fill="{t["cells"][lvl]}" style="{loop("pop .5s cubic-bezier(.2,.7,.2,1)", delay, "wave")}"/>'
        )
    legend_x = w - 24 - 5 * 14 - 70
    legend = [f'<text x="{legend_x}" y="232" class="faint f" font-size="10" style="animation-delay:2s">less</text>']
    for i in range(5):
        legend.append(
            f'<rect class="f" x="{legend_x + 30 + i * 14}" y="223" width="10" height="10" rx="2" fill="{t["cells"][i]}" style="animation-delay:2s"/>'
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
{''.join(cells)}
<text x="24" y="232" class="faint f" font-size="10" style="animation-delay:2s">last 12 months  ·  updated {updated}</text>
{''.join(legend)}
</svg>"""


def languages(t, s):
    w, h = 840, 96
    top = s["langs"][:5]
    rest = sum(v for _, v in s["langs"][5:])
    if rest:
        top.append(("other", rest))
    total = sum(v for _, v in top) or 1
    extra = """
.seg{transform-box:fill-box;transform-origin:left;transform:scaleX(0)}
@keyframes grow{to{transform:scaleX(1)}}
@keyframes regrow{0%{transform:scaleX(1)}3%{transform:scaleX(0)}9%{transform:scaleX(1)}100%{transform:scaleX(1)}}
"""
    bx, bw = 24, w - 48
    segs = []
    legend = []
    x = bx
    lx = bx
    for i, (name, v) in enumerate(top):
        sw = bw * v / total
        segs.append(
            f'<rect class="seg" x="{x:.2f}" y="28" width="{max(sw - 2, 1):.2f}" height="8" rx="2" fill="{t["bars"][i]}" style="{loop("grow 1s cubic-bezier(.6,0,.2,1)", 0.1 + i * 0.12, "regrow")}"/>'
        )
        x += sw
        label = f"{name.lower()}  {100 * v / total:.1f}%"
        legend.append(
            f'<g class="r" style="animation-delay:{0.6 + i * 0.08:.2f}s"><circle cx="{lx + 5}" cy="70" r="4" fill="{t["bars"][i]}" stroke="{t["border"]}"/>'
            f'<text x="{lx + 16}" y="74" class="mute" font-size="12">{escape(label)}</text></g>'
        )
        lx += len(label) * 6.6 + 40
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
{style(t, extra)}
<rect class="card" x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="12"/>
<clipPath id="c"><rect x="{bx}" y="28" width="{bw}" height="8" rx="4"/></clipPath>
<g clip-path="url(#c)">{''.join(segs)}</g>
{''.join(legend)}
</svg>"""


def stack(s, theme):
    icons = []
    for name, _ in s["langs"]:
        i = LANG_ICONS.get(name)
        if i and i not in icons:
            icons.append(i)
    for f in s["frameworks"]:
        if f not in icons:
            icons.append(f)
    url = f"https://skillicons.dev/icons?i={','.join(icons[:14])}&theme={theme}&perline=14"
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
        if r["stargazerCount"]:
            tags.append(f"{r['stargazerCount']} stars")
        if merged:
            tags.append(f"{merged} merged pr" + ("s" if merged > 1 else ""))
        if issues:
            tags.append(f"{issues} issue" + ("s" if issues > 1 else ""))
        out.append({
            "slug": "contrib-" + r["nameWithOwner"].replace("/", "-").lower(),
            "name": f"{r['owner']['login']} / {r['name']}",
            "desc": wrap(r["description"] or "", 46),
            "tags": tags,
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


def write_readme(contrib):
    readme = OUT.parent / "README.md"
    text = readme.read_text()
    start = text.index("### contributed to")
    end = text.index("### activity")
    links = [f'<a href="{c["url"]}">{pic(c["slug"], c["name"])}</a>' for c in contrib]
    rows = ["&nbsp;".join(links[i:i + 2]) for i in range(0, len(links), 2)]
    block = "### contributed to\n\n" + "\n\n".join(rows) + "\n\n<br>\n\n"
    readme.write_text(text[:start] + block + text[end:])


def main():
    OUT.mkdir(exist_ok=True)
    s = fetch()
    contrib = contributed()
    for name, t in THEMES.items():
        (OUT / f"header-{name}.svg").write_text(header(t, s))
        (OUT / f"stats-{name}.svg").write_text(stats(t, s))
        (OUT / f"langs-{name}.svg").write_text(languages(t, s))
        for i, (slug, label, icon) in enumerate(LINKS):
            (OUT / f"link-{slug}-{name}.svg").write_text(pill(t, label, icon, i))
        for i, p in enumerate(PROJECTS):
            (OUT / f"{p['slug']}-{name}.svg").write_text(card(t, p, i % 2))
        (OUT / f"stack-{name}.svg").write_text(stack(s, name))
        for i, c in enumerate(contrib):
            (OUT / f"{c['slug']}-{name}.svg").write_text(card(t, c, i % 2))
    for old in OUT.glob("contrib-*.svg"):
        if not any(old.name.startswith(c["slug"] + "-") for c in contrib):
            old.unlink()
    write_readme(contrib)
    print(json.dumps({k: v for k, v in s.items() if k not in ("days", "langs", "latest")}))


if __name__ == "__main__":
    main()
