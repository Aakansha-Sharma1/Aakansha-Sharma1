#!/usr/bin/env python3

import json
import math
import os
import urllib.request


USERNAME = "Aakansha-Sharma1"

OUTPUT_DOMAIN = "assets/radar-domain.svg"
OUTPUT_TECH = "assets/radar-tech.svg"

API_URL = (
    "https://api.github.com/users/"
    + USERNAME
    + "/repos?per_page=100&sort=updated"
)


def github_get(url):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": USERNAME,
        },
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def get_repositories():
    print("Scanning GitHub repositories for " + USERNAME + "...")

    repositories = github_get(API_URL)

    repositories = [
        repo
        for repo in repositories
        if not repo.get("fork", False)
        and not repo.get("archived", False)
        and repo.get("name") != USERNAME
    ]

    print("Found " + str(len(repositories)) + " repositories.")
    return repositories


def get_repository_tree(repo):
    owner = repo["owner"]["login"]
    name = repo["name"]
    branch = repo.get("default_branch", "main")

    url = (
        "https://api.github.com/repos/"
        + owner
        + "/"
        + name
        + "/git/trees/"
        + branch
        + "?recursive=1"
    )

    try:
        return github_get(url)
    except Exception:
        return {"tree": []}


def analyse_repositories(repositories):
    language_bytes = {}
    file_names = []
    repository_text = []

    for repo in repositories:
        languages_url = repo.get("languages_url")

        if languages_url:
            try:
                languages = github_get(languages_url)

                for language, amount in languages.items():
                    language_bytes[language] = (
                        language_bytes.get(language, 0) + amount
                    )
            except Exception:
                pass

        repository_text.append(
            (
                str(repo.get("name", ""))
                + " "
                + str(repo.get("description", ""))
                + " "
                + " "
                .join(repo.get("topics", []))
            ).lower()
        )

        tree = get_repository_tree(repo)

        for item in tree.get("tree", []):
            path = item.get("path", "")

            if path:
                file_names.append(path.lower())

    return language_bytes, file_names, repository_text


def contains_any(text, words):
    for word in words:
        if word in text:
            return True

    return False


def calculate_scores(language_bytes, file_names, repository_text):
    language_total = sum(language_bytes.values())

    if language_total == 0:
        language_total = 1

    c_bytes = language_bytes.get("C", 0)
    cpp_bytes = language_bytes.get("C++", 0)

    assembly_bytes = (
        language_bytes.get("Assembly", 0)
        + language_bytes.get("NASM", 0)
    )

    python_bytes = language_bytes.get("Python", 0)

    javascript_bytes = (
        language_bytes.get("JavaScript", 0)
        + language_bytes.get("TypeScript", 0)
    )

    linux_tooling_bytes = (
        language_bytes.get("Shell", 0)
        + language_bytes.get("PowerShell", 0)
        + language_bytes.get("Makefile", 0)
        + language_bytes.get("Dockerfile", 0)
    )

    c_cpp_score = min(
        10.0,
        10.0 * (c_bytes + cpp_bytes) / language_total * 2.0,
    )

    assembly_score = min(
        10.0,
        10.0 * assembly_bytes / language_total * 3.0,
    )

    python_score = min(
        10.0,
        10.0 * python_bytes / language_total * 3.0,
    )

    javascript_score = min(
        10.0,
        10.0 * javascript_bytes / language_total * 2.0,
    )

    tooling_score = min(
        10.0,
        10.0 * linux_tooling_bytes / language_total * 4.0,
    )

    all_text = " ".join(repository_text)

    os_keywords = [
        "operating system",
        "operating-system",
        "kernel",
        "os development",
        "osdev",
        "bootloader",
        "memory management",
        "process management",
        "paging",
        "filesystem",
    ]

    systems_keywords = [
        "systems programming",
        "system programming",
        "kernel",
        "assembly",
        "low level",
        "low-level",
        "memory",
        "process",
        "scheduler",
        "paging",
        "interrupt",
        "x86",
    ]

    cybersecurity_keywords = [
        "cybersecurity",
        "cyber security",
        "security",
        "forensic",
        "forensics",
        "malware",
        "threat",
        "intrusion",
        "sentinel",
        "guardrail",
        "authentication",
        "vulnerability",
    ]

    ai_keywords = [
        "artificial intelligence",
        "machine learning",
        "deep learning",
        "ai",
        "ml",
        "llm",
        "prompt",
        "copilot",
        "neural",
    ]

    open_source_keywords = [
        "open source",
        "opensource",
        "github",
        "contribution",
    ]

    os_hits = 0
    systems_hits = 0
    cybersecurity_hits = 0
    ai_hits = 0
    open_source_hits = 0

    for keyword in os_keywords:
        if keyword in all_text:
            os_hits += 1

    for keyword in systems_keywords:
        if keyword in all_text:
            systems_hits += 1

    for keyword in cybersecurity_keywords:
        if keyword in all_text:
            cybersecurity_hits += 1

    for keyword in ai_keywords:
        if keyword in all_text:
            ai_hits += 1

    for keyword in open_source_keywords:
        if keyword in all_text:
            open_source_hits += 1

    asm_file_count = 0
    c_file_count = 0
    python_file_count = 0

    for name in file_names:
        if name.endswith(".asm") or name.endswith(".s"):
            asm_file_count += 1

        if name.endswith(".c") or name.endswith(".h"):
            c_file_count += 1

        if name.endswith(".py"):
            python_file_count += 1

    os_score = min(
        10.0,
        2.5 * os_hits + 1.0 * min(asm_file_count, 3),
    )

    systems_score = min(
        10.0,
        2.0 * systems_hits
        + 2.0 * min(asm_file_count, 3)
        + 1.5 * min(c_file_count, 3),
    )

    cybersecurity_score = min(
        10.0,
        2.5 * cybersecurity_hits,
    )

    ai_score = min(
        10.0,
        2.5 * ai_hits,
    )

    open_source_score = min(
        10.0,
        2.0 * open_source_hits
        + min(len(repositories := repository_text), 5) * 0.5,
    )

    if os_score == 0 and asm_file_count > 0:
        os_score = 1.5

    if systems_score == 0 and c_file_count > 0:
        systems_score = 1.5

    return {
        "Operating Systems": round(os_score, 1),
        "Systems Programming": round(systems_score, 1),
        "Cybersecurity": round(cybersecurity_score, 1),
        "Artificial Intelligence": round(ai_score, 1),
        "Open Source": round(open_source_score, 1),
        "C / C++": round(c_cpp_score, 1),
        "Assembly": round(assembly_score, 1),
        "Python": round(python_score, 1),
        "JavaScript / TypeScript": round(javascript_score, 1),
        "Linux / Tooling": round(tooling_score, 1),
    }


def polar_point(cx, cy, radius, angle):
    x = cx + radius * math.cos(angle)
    y = cy + radius * math.sin(angle)

    return x, y


def polygon_points(cx, cy, radius, count):
    points = []

    for index in range(count):
        angle = (
            -math.pi / 2
            + 2 * math.pi * index / count
        )

        x, y = polar_point(
            cx,
            cy,
            radius,
            angle,
        )

        points.append(
            "{:.2f},{:.2f}".format(x, y)
        )

    return " ".join(points)


def create_radar_svg(title, subtitle, skills, scores):
    width = 900
    height = 760

    cx = 450
    cy = 365
    radius = 210

    svg = []

    svg.append(
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'width="900" height="760" viewBox="0 0 900 760">'
    )

    svg.append(
        '<defs>'
        '<linearGradient id="background" '
        'x1="0%" y1="0%" x2="100%" y2="100%">'
        '<stop offset="0%" stop-color="#07111f"/>'
        '<stop offset="100%" stop-color="#111827"/>'
        '</linearGradient>'
        '<linearGradient id="radar" '
        'x1="0%" y1="0%" x2="100%" y2="100%">'
        '<stop offset="0%" stop-color="#22d3ee"/>'
        '<stop offset="50%" stop-color="#3b82f6"/>'
        '<stop offset="100%" stop-color="#a855f7"/>'
        '</linearGradient>'
        '</defs>'
    )

    svg.append(
        '<rect x="10" y="10" width="880" height="740" '
        'rx="28" fill="url(#background)" '
        'stroke="#1e293b" stroke-width="2"/>'
    )

    svg.append(
        '<text x="450" y="62" text-anchor="middle" '
        'font-family="monospace" font-size="30" '
        'font-weight="700" fill="#f8fafc">'
        + title
        + "</text>"
    )

    svg.append(
        '<text x="450" y="96" text-anchor="middle" '
        'font-family="monospace" font-size="15" '
        'fill="#94a3b8">'
        + subtitle
        + "</text>"
    )

    count = len(skills)

    # Radar rings.
    for level in range(2, 11, 2):
        ring_radius = (
            radius * level / 10.0
        )

        ring_points = polygon_points(
            cx,
            cy,
            ring_radius,
            count,
        )

        svg.append(
            '<polygon points="'
            + ring_points
            + '" fill="none" '
            + 'stroke="#334155" '
            + 'stroke-width="1"/>'
        )

    # Axis lines.
    for index in range(count):
        angle = (
            -math.pi / 2
            + 2 * math.pi * index / count
        )

        x, y = polar_point(
            cx,
            cy,
            radius,
            angle,
        )

        svg.append(
            '<line x1="'
            + str(cx)
            + '" y1="'
            + str(cy)
            + '" x2="'
            + "{:.2f}".format(x)
            + '" y2="'
            + "{:.2f}".format(y)
            + '" stroke="#334155" stroke-width="1"/>'
        )

    # Data polygon.
    data_points = []

    for index, skill in enumerate(skills):
        angle = (
            -math.pi / 2
            + 2 * math.pi * index / count
        )

        value_radius = (
            radius * scores[skill] / 10.0
        )

        x, y = polar_point(
            cx,
            cy,
            value_radius,
            angle,
        )

        data_points.append(
            "{:.2f},{:.2f}".format(x, y)
        )

    data_points = " ".join(data_points)

    svg.append(
        '<polygon points="'
        + data_points
        + '" fill="#3b82f6" '
        + 'fill-opacity="0.20" '
        + 'stroke="url(#radar)" '
        + 'stroke-width="3"/>'
    )

    # Points and labels.
    for index, skill in enumerate(skills):
        angle = (
            -math.pi / 2
            + 2 * math.pi * index / count
        )

        point_radius = (
            radius * scores[skill] / 10.0
        )

        point_x, point_y = polar_point(
            cx,
            cy,
            point_radius,
            angle,
        )

        svg.append(
            '<circle cx="'
            + "{:.2f}".format(point_x)
            + '" cy="'
            + "{:.2f}".format(point_y)
            + '" r="5" fill="#22d3ee"/>'
        )

        label_radius = radius + 5

        label_x, label_y = polar_point(
            cx,
            cy,
            label_radius,
            angle,
        )

        if label_x < cx - 20:
            anchor = "end"
        elif label_x > cx + 20:
            anchor = "start"
        else:
            anchor = "middle"

        svg.append(
            '<text x="'
            + "{:.2f}".format(label_x)
            + '" y="'
            + "{:.2f}".format(label_y)
            + '" text-anchor="'
            + anchor
            + '" dominant-baseline="middle" '
            + 'font-family="monospace" '
            + 'font-size="15" font-weight="600" '
            + 'fill="#e2e8f0">'
            + skill
            + "</text>"
        )

        score_x, score_y = polar_point(
            cx,
            cy,
            label_radius + 45,
            angle,
        )

        svg.append(
            '<text x="'
            + "{:.2f}".format(score_x)
            + '" y="'
            + "{:.2f}".format(score_y)
            + '" text-anchor="'
            + anchor
            + '" dominant-baseline="middle" '
            + 'font-family="monospace" '
            + 'font-size="13" fill="#64748b">'
            + "{:.1f}/10".format(scores[skill])
            + "</text>"
        )

    svg.append(
        '<text x="450" y="715" text-anchor="middle" '
        'font-family="monospace" font-size="13" '
        'fill="#64748b">'
        'Scores are automatically derived from public repository data'
        '</text>'
    )

    svg.append("</svg>")

    return "\n".join(svg)


def write_file(path, content):
    directory = os.path.dirname(path)

    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        file.write(content)


def print_scores(scores):
    print("")
    print("Skill scores:")

    for skill, score in scores.items():
        print(
            "  "
            + "{:<28}".format(skill)
            + "{:.1f}/10".format(score)
        )


def main():
    repositories = get_repositories()

    language_bytes, file_names, repository_text = (
        analyse_repositories(repositories)
    )

    scores = calculate_scores(
        language_bytes,
        file_names,
        repository_text,
    )

    domain_skills = [
        "Operating Systems",
        "Systems Programming",
        "Cybersecurity",
        "Artificial Intelligence",
        "Open Source",
    ]

    technology_skills = [
        "C / C++",
        "Assembly",
        "Python",
        "JavaScript / TypeScript",
        "Linux / Tooling",
    ]

    domain_scores = {
        skill: scores[skill]
        for skill in domain_skills
    }

    technology_scores = {
        skill: scores[skill]
        for skill in technology_skills
    }

    domain_svg = create_radar_svg(
        "GitHub Domain Radar",
        "Automatically derived from "
        + str(len(repositories))
        + " public repositories",
        domain_skills,
        domain_scores,
    )

    technology_svg = create_radar_svg(
        "GitHub Technology Radar",
        "Automatically derived from "
        + str(len(repositories))
        + " public repositories",
        technology_skills,
        technology_scores,
    )

    write_file(
        OUTPUT_DOMAIN,
        domain_svg,
    )

    write_file(
        OUTPUT_TECH,
        technology_svg,
    )

    print("")
    print("Detected languages:")

    for language, amount in sorted(
        language_bytes.items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        print(
            "  "
            + "{:<16}".format(language)
            + str(amount)
            + " bytes"
        )

    print_scores(scores)

    print("")
    print("Generated:")
    print("  " + OUTPUT_DOMAIN)
    print("  " + OUTPUT_TECH)


if __name__ == "__main__":
    main()
