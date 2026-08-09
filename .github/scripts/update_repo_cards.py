import urllib.request
import json
import re
import os
import base64
import sys

username = "joaoAngelo2"
token = os.environ.get("GITHUB_TOKEN", "")

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}

def gh(url):
    req = urllib.request.Request(url, headers=headers)
    return json.loads(urllib.request.urlopen(req).read())

def fetch_avatar_b64(avatar_url):
    try:
        req = urllib.request.Request(avatar_url + "&size=80", headers={"User-Agent": "github-actions"})
        data = urllib.request.urlopen(req, timeout=8).read()
        return "data:image/png;base64," + base64.b64encode(data).decode()
    except:
        return ""

def get_last_committer_avatar(repo_name):
    try:
        commits = gh(f"https://api.github.com/repos/{username}/{repo_name}/commits?per_page=1")
        if commits and commits[0].get("author") and commits[0]["author"].get("avatar_url"):
            return fetch_avatar_b64(commits[0]["author"]["avatar_url"])
    except:
        pass
    return fetch_avatar_b64(f"https://github.com/{username}.png")

lang_colors = {
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Kotlin":     "#A97BFF",
    "Java":       "#b07219",
    "Python":     "#3572A5",
}

def make_svg(repo_name, description, language, stars, forks, avatar_data, width=340):
    color = lang_colors.get(language, "#8b949e")
    lang  = language or "Unknown"
    desc  = description or "No description provided."
    if len(desc) > 46:
        desc = desc[:45] + "…"
    clip_id = "av_" + re.sub(r"[^a-zA-Z0-9]", "_", repo_name)[:12]

    if avatar_data:
        avatar_el = (
            f'  <clipPath id="{clip_id}"><circle cx="34" cy="40" r="17"/></clipPath>\n'
            f'  <image href="{avatar_data}" x="17" y="23" width="34" height="34" clip-path="url(#{clip_id})"/>\n'
            f'  <circle cx="34" cy="40" r="17" fill="none" stroke="#6FF3E940" stroke-width="1.5"/>'
        )
    else:
        avatar_el = '  <circle cx="34" cy="40" r="17" fill="#6FF3E915" stroke="#6FF3E940" stroke-width="1.5"/>'

    return (
        f'<svg width="{width}" height="80" viewBox="0 0 {width} 80" '
        f'xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">\n'
        f'  <rect width="{width}" height="80" rx="8" fill="#0d1117" stroke="#30363d" stroke-width="1"/>\n'
        f'{avatar_el}\n'
        f'  <text x="63" y="31" font-family="JetBrains Mono,monospace" font-size="13" font-weight="500" fill="#6FF3E9">{repo_name}</text>\n'
        f'  <text x="63" y="47" font-family="JetBrains Mono,monospace" font-size="10" fill="#8b949e">{desc}</text>\n'
        f'  <circle cx="63" cy="64" r="4" fill="{color}"/>\n'
        f'  <text x="72" y="67" font-family="JetBrains Mono,monospace" font-size="10" fill="#8b949e">{lang}</text>\n'
        f'  <text x="{width - 68}" y="67" font-family="JetBrains Mono,monospace" font-size="10" fill="#8b949e">&#9733; {stars}  &#9902; {forks}</text>\n'
        f'</svg>'
    )

repos = gh(f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated")

sections = {
    "react":      {"langs": ["JavaScript", "TypeScript"], "keywords": ["react", "next", "vite"]},
    "typescript": {"langs": ["TypeScript"],               "keywords": []},
    "java":       {"langs": ["Java"],                     "keywords": []},
    "android":    {"langs": ["Kotlin", "Java"],           "keywords": ["android"]},
}

os.makedirs(".github/cards", exist_ok=True)

with open("README.md", "r") as f:
    readme = f.read()

for section, criteria in sections.items():
    cards_md = ""
    for repo in repos:
        if repo.get("fork"):
            continue
        lang  = repo.get("language") or ""
        name  = repo["name"]
        namel = name.lower()
        lang_match = lang in criteria["langs"]
        if section == "react":
            if not (lang_match and any(kw in namel for kw in criteria["keywords"])):
                continue
        else:
            if not lang_match:
                continue

        print(f"  Gerando card: {name}")
        avatar = get_last_committer_avatar(name)
        svg = make_svg(
            name,
            repo.get("description", ""),
            lang,
            repo.get("stargazers_count", 0),
            repo.get("forks_count", 0),
            avatar
        )
        svg_path = f".github/cards/{section}_{name}.svg"
        with open(svg_path, "w") as f:
            f.write(svg)

        cards_md += f'<img src="{svg_path}" alt="{name}" />\n'

    if not cards_md:
        cards_md = "_Nenhum repositório encontrado._\n"

    readme = re.sub(
        f"<!--START_SECTION:{section}-->.*?<!--END_SECTION:{section}-->",
        f"<!--START_SECTION:{section}-->\n{cards_md}<!--END_SECTION:{section}-->",
        readme,
        flags=re.DOTALL
    )

with open("README.md", "w") as f:
    f.write(readme)

print("Concluído.")
