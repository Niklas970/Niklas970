"""Erzeugt Neon-Karten (SVG) aus GitHub-Daten. Nur Standardbibliothek."""
import json, os, sys, urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

USER = "Niklas970"
TZ = ZoneInfo("Europe/Berlin")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
COLORS = ["#00e5ff", "#0b8bff", "#7fe9ff", "#6a5cff", "#00b8d9", "#8fb3c9"]
F = 'font-family="Segoe UI, Helvetica, Arial, sans-serif"'
M = 'font-family="Consolas, Menlo, monospace"'
W, H = 520, 230


def req(url, data=None):
    r = urllib.request.Request(url, data=data, headers={"Accept": "application/vnd.github+json"})
    if TOKEN:
        r.add_header("Authorization", f"Bearer {TOKEN}")
    return json.load(urllib.request.urlopen(r, timeout=30))


def graphql(query):
    return req("https://api.github.com/graphql", json.dumps({"query": query}).encode())["data"]


def card(title, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{title}">'
            f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="16" fill="#0a1626" stroke="#123a5e" stroke-width="1.5"/>'
            f'<text x="28" y="44" {F} font-size="21" font-weight="700" fill="#00e5ff">{title}</text>{body}</svg>')


def collect():
    repos = [r for r in req(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner") if not r["fork"]]
    user = req(f"https://api.github.com/users/{USER}")
    d = {"user": user, "repos": repos, "bytes": {}, "by_repo": {}, "hours": [0] * 24, "weeks": [], "total": 0}
    for r in repos:
        if r.get("language"):
            d["by_repo"][r["language"]] = d["by_repo"].get(r["language"], 0) + 1
        try:
            for lang, n in req(r["languages_url"]).items():
                d["bytes"][lang] = d["bytes"].get(lang, 0) + n
        except Exception as e:
            print("Sprachen", r["name"], e)
        try:
            for c in req(f"https://api.github.com/repos/{USER}/{r['name']}/commits?author={USER}&per_page=100"):
                t = datetime.fromisoformat(c["commit"]["author"]["date"].replace("Z", "+00:00"))
                d["hours"][t.astimezone(TZ).hour] += 1
        except Exception as e:
            print("Commits", r["name"], e)
    try:
        q = 'query{user(login:"%s"){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{contributionCount}}}}}}' % USER
        cal = graphql(q)["user"]["contributionsCollection"]["contributionCalendar"]
        d["total"] = cal["totalContributions"]
        d["weeks"] = [sum(x["contributionCount"] for x in w["contributionDays"]) for w in cal["weeks"]]
    except Exception as e:
        print("Kalender", e)
    return d


def langs_card(d):
    items = sorted(d["bytes"].items(), key=lambda kv: -kv[1])[:6]
    total = sum(n for _, n in items) or 1
    out, x = [], 28.0
    if not items:
        out.append(f'<text x="28" y="120" {F} font-size="16" fill="#8fb3c9">Noch keine Daten</text>')
    for i, (lang, n) in enumerate(items):
        w = 464 * n / total
        out.append(f'<rect x="{x:.1f}" y="62" width="{max(w,2):.1f}" height="10" fill="{COLORS[i]}"/>')
        x += w
        cx, cy = 28 + (i % 2) * 232, 108 + (i // 2) * 34
        out.append(f'<circle cx="{cx+6}" cy="{cy}" r="6" fill="{COLORS[i]}"/><text x="{cx+20}" y="{cy+5}" {F} font-size="16" fill="#e7f3ff">{lang} {100*n/total:.1f}%</text>')
    return card("Meistgenutzte Sprachen", "".join(out))


def hours_card(d):
    hs, mx, out = d["hours"], max(d["hours"]) or 1, []
    bw = 464 / 24
    for h, n in enumerate(hs):
        bh = 110 * n / mx
        out.append(f'<rect x="{28+h*bw+2:.1f}" y="{180-bh:.1f}" width="{bw-4:.1f}" height="{max(bh,2):.1f}" rx="3" fill="#00e5ff" opacity="{0.35+0.65*n/mx:.2f}"/>')
    for h in (0, 6, 12, 18, 23):
        out.append(f'<text x="{28+h*bw+bw/2:.1f}" y="202" {M} font-size="12" fill="#8fb3c9" text-anchor="middle">{h:02d}</text>')
    out.append(f'<text x="492" y="44" {F} font-size="13" fill="#8fb3c9" text-anchor="end">Uhrzeit MEZ/MESZ</text>')
    return card("Commits nach Uhrzeit", "".join(out))


def profile_card(d):
    u, out = d["user"], []
    facts = [("Contributions (12 Mon.)", d["total"]), ("Öffentliche Repos", len(d["repos"])),
             ("Follower", u["followers"])]
    for i, (k, v) in enumerate(facts):
        out.append(f'<text x="28" y="{74+i*38}" {F} font-size="13" fill="#8fb3c9">{k}</text><text x="28" y="{92+i*38}" {M} font-size="20" font-weight="700" fill="#e7f3ff">{v}</text>')
    wk = d["weeks"] or [0]
    mx, n = max(wk) or 1, len(wk)
    x0, x1, yb, ht = 250, 492, 195, 120
    pts = [(x0 + (x1 - x0) * i / max(n - 1, 1), yb - ht * v / mx) for i, v in enumerate(wk)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    out.append(f'<defs><linearGradient id="ar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#00e5ff" stop-opacity="0.45"/><stop offset="1" stop-color="#00e5ff" stop-opacity="0"/></linearGradient></defs>')
    out.append(f'<polygon points="{x0},{yb} {line} {x1},{yb}" fill="url(#ar)"/><polyline points="{line}" fill="none" stroke="#00e5ff" stroke-width="2.5" stroke-linejoin="round"/>')
    out.append(f'<text x="492" y="44" {F} font-size="13" fill="#8fb3c9" text-anchor="end">letztes Jahr</text>')
    return card(f"{USER}", "".join(out))


def stats_card(d):
    u = d["user"]
    stars = sum(r["stargazers_count"] for r in d["repos"])
    rows = [("Sterne", stars), ("Öffentliche Repos", len(d["repos"])), ("Follower", u["followers"]),
            ("Folge ich", u["following"]), ("Contributions (12 Mon.)", d["total"])]
    out = []
    for i, (k, v) in enumerate(rows):
        y = 84 + i * 26
        out.append(f'<circle cx="34" cy="{y-5}" r="4" fill="#00e5ff"/><text x="48" y="{y}" {F} font-size="16" fill="#8fb3c9">{k}</text><text x="492" y="{y}" {M} font-size="17" font-weight="700" fill="#e7f3ff" text-anchor="end">{v}</text>')
    return card("Stats", "".join(out))


if __name__ == "__main__":
    try:
        d = collect()
    except Exception as e:
        print("Fehler:", e)
        sys.exit(1)
    for name, fn in [("profile", profile_card), ("stats", stats_card), ("hours", hours_card), ("langs", langs_card)]:
        open(f"{name}.svg", "w").write(fn(d))
