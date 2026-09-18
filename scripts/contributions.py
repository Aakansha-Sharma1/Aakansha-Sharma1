import re
import urllib.request
from pathlib import Path


USERNAME = "Aakansha-Sharma1"
OUTPUT = Path("assets/contributions.svg")


def fetch_contributions():
    url = (
        f"https://github.com/{USERNAME}"
        "?action=show"
        "&controller=profiles"
        "&tab=contributions"
        f"&user_id={USERNAME}"
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html, */*",
            "X-Requested-With": "XMLHttpRequest",
        },
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8")


def parse_cells(html):
    pattern = re.compile(
        r'data-date="([^"]+)"[^>]*data-level="([^"]+)"'
    )

    cells = []

    for date, level in pattern.findall(html):
        try:
            level = int(level)
        except ValueError:
            continue

        cells.append((date, level))

    return cells


def generate_svg(cells):
    width = 900
    height = 190

    cell_size = 12
    gap = 3
    step = cell_size + gap

    # GitHub's calendar is arranged in columns by week.
    # Reconstruct the position from the date.
    from datetime import date

    parsed = []

    for date_string, level in cells:
        try:
            year, month, day = map(int, date_string.split("-"))
            current = date(year, month, day)
        except ValueError:
            continue

        parsed.append((current, level))

    if not parsed:
        raise RuntimeError("No contribution cells found.")

    parsed.sort(key=lambda item: item[0])

    first_date = parsed[0][0]

    # Align the first date to Sunday.
    first_sunday = first_date.fromordinal(
        first_date.toordinal() - (first_date.weekday() + 1) % 7
    )

    rects = []

    for current, level in parsed:
        days = (current - first_sunday).days

        column = days // 7
        row = days % 7

        x = 80 + column * step
        y = 28 + row * step

        rects.append(
            f'<rect x="{x}" y="{y}" width="{cell_size}" '
            f'height="{cell_size}" rx="2" class="level-{level}"/>'
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
            fill: #c9d1d9;
        }}

        .month {{
            font-family: monospace;
            font-size: 10px;
            fill: #8b949e;
        }}

        .day {{
            font-family: monospace;
            font-size: 9px;
            fill: #8b949e;
        }}

        .level-0 {{ fill: #161b22; }}
        .level-1 {{ fill: #0e4429; }}
        .level-2 {{ fill: #006d32; }}
        .level-3 {{ fill: #26a641; }}
        .level-4 {{ fill: #39d353; }}
    </style>

    <rect width="100%" height="100%" rx="12" fill="#0d1117"/>

    <text x="20" y="20" class="title">
        ~/ contribution calendar
    </text>

    <text x="20" y="48" class="day">Mon</text>
    <text x="20" y="78" class="day">Wed</text>
    <text x="20" y="108" class="day">Fri</text>

    {''.join(rects)}

    </svg>
'''

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")


def main():
    print(f"Reading GitHub contributions for {USERNAME}...")

    html = fetch_contributions()
    cells = parse_cells(html)

    print(f"Found {len(cells)} contribution cells.")

    if not cells:
        raise RuntimeError(
            "No contribution cells found. "
            "GitHub contribution fragment format may have changed."
        )

    generate_svg(cells)

    print(f"Generated: {OUTPUT}")


if __name__ == "__main__":
    main()
