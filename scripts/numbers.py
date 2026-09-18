import json
import urllib.request
from pathlib import Path


USERNAME = "Aakansha-Sharma1"
OUTPUT = Path("assets/numbers.svg")


def github_get(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Aakansha-Sharma1-profile-generator",
            "Accept": "application/vnd.github+json",
        },
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_profile():
    return github_get(
        f"https://api.github.com/users/{USERNAME}"
    )


def fetch_repositories():
    repositories = []
    page = 1

    while True:
        url = (
            f"https://api.github.com/users/{USERNAME}/repos"
            f"?per_page=100&page={page}"
        )

        batch = github_get(url)

        if not batch:
            break

        repositories.extend(batch)

        if len(batch) < 100:
            break

        page += 1

    return repositories


def generate_svg(profile, repositories):
    public_repos = profile.get("public_repos", 0)
    followers = profile.get("followers", 0)

    stars = sum(
        repo.get("stargazers_count", 0)
        for repo in repositories
        if not repo.get("fork", False)
    )

    forks = sum(
        repo.get("forks_count", 0)
        for repo in repositories
        if not repo.get("fork", False)
    )

    stats = [
        ("PUBLIC REPOS", public_repos),
        ("FOLLOWERS", followers),
        ("STARS", stars),
        ("FORKS", forks),
    ]

    width = 900
    height = 190

    card_width = 205
    card_height = 105
    gap = 15
    start_x = 20
    start_y = 50

    cards = []

    for index, (label, value) in enumerate(stats):
        x = start_x + index * (card_width + gap)

        cards.append(
            f'''
            <rect
                x="{x}"
                y="{start_y}"
                width="{card_width}"
                height="{card_height}"
                rx="12"
                class="card"
            />

            <text
                x="{x + card_width / 2}"
                y="{start_y + 45}"
                text-anchor="middle"
                class="value"
            >
                {value}
            </text>

            <text
                x="{x + card_width / 2}"
                y="{start_y + 78}"
                text-anchor="middle"
                class="label"
            >
                {label}
            </text>
            '''
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg"
    width="{width}"
    height="{height}"
    viewBox="0 0 {width} {height}">

    <style>
        .title {{
            font-family: monospace;
            font-size: 16px;
            font-weight: bold;
            fill: #24292f;
        }}

        .card {{
            fill: #f6f8fa;
            stroke: #d0d7de;
            stroke-width: 1;
        }}

        .value {{
            font-family: monospace;
            font-size: 28px;
            font-weight: bold;
            fill: #0969da;
        }}

        .label {{
            font-family: monospace;
            font-size: 11px;
            font-weight: bold;
            fill: #57606a;
            letter-spacing: 1px;
        }}
    </style>

    <rect
        width="100%"
        height="100%"
        rx="12"
        fill="#ffffff"
    />

    <text x="20" y="28" class="title">
        ~/ the numbers
    </text>

    {''.join(cards)}

    </svg>
'''

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")

    print(f"Public repositories: {public_repos}")
    print(f"Followers: {followers}")
    print(f"Stars: {stars}")
    print(f"Forks: {forks}")
    print(f"Generated: {OUTPUT}")


def main():
    print(f"Reading GitHub statistics for {USERNAME}...")

    profile = fetch_profile()
    repositories = fetch_repositories()

    generate_svg(profile, repositories)


if __name__ == "__main__":
    main()
