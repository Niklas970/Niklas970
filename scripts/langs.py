import json, os, urllib.request

USER = "Niklas970"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
COLORS = ["#00e5ff", "#0b8bff", "#7fe9ff", "#6a5cff", "#00b8d9", "#8fb3c9"]


def api(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    return json.load(urllib.request.urlopen(req))


def collect():
    totals = {}
    repos = api(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner")
    for r in repos:
        if r["fork"]:
            continue
        for lang, n in api(r["languages_url"]).items():
            totals[lang] = totals.get(lang, 0) + n
    return totals


def render(totals):
    items = sorted(totals.items(), key=lambda kv: -kv[1])[:6]
    total = sum(n for _, n in items) or 1
    F = 'font-family="Segoe UI, Helvetica, Arial, sans-serif"'
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="520" height="230" viewBox="0 0 520 230" role="img" aria-label="Meistgenutzte Sprachen">',
        '<rect x="1" y="1" width="518" height="228" rx="16" fill="#0a1626" stroke="#123a5e" stroke-width="1.5"/>',
        f'<text x="28" y="48" {F} font-size="22" font-weight="700" fill="#00e5ff">Meistgenutzte Sprachen</text>',
    ]
    if not items:
        out.append(f'<text x="28" y="120" {F} font-size="16" fill="#8fb3c9">Daten werden beim ersten Lauf berechnet</text>')
    x = 28.0
    for i, (lang, n) in enumerate(items):
        w = 464 * n / total
        out.append(f'<rect x="{x:.1f}" y="68" width="{max(w,2):.1f}" height="10" fill="{COLORS[i]}"/>')
        x += w
        col, row = i % 2, i // 2
        cx, cy = 28 + col * 232, 112 + row * 34
        out.append(f'<circle cx="{cx+6}" cy="{cy}" r="6" fill="{COLORS[i]}"/>')
        out.append(f'<text x="{cx+20}" y="{cy+5}" {F} font-size="16" fill="#e7f3ff">{lang} {100*n/total:.1f}%</text>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    try:
        data = collect()
    except Exception as e:
        print("Fehler:", e)
        raise SystemExit(1)
    open("langs.svg", "w").write(render(data))
