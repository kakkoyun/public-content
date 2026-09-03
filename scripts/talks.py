#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Generate and validate talks/INDEX.md from talks/talks.yaml."""

from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
TALKS_YAML = REPO_ROOT / "talks" / "talks.yaml"
INDEX_MD = REPO_ROOT / "talks" / "INDEX.md"
GITMODULES = REPO_ROOT / ".gitmodules"

TOOLING_LABELS = {
    "gslides": "Google Slides",
    "obsidian": "Obsidian",
    "marp": "Marp",
    "repo-hosted": "Repo-hosted",
    "none": "—",
}


def load_talks() -> list[dict]:
    data = yaml.safe_load(TALKS_YAML.read_text())
    return data.get("talks", []) or []


def parse_date(value) -> datetime.date | None:
    if isinstance(value, datetime.date):
        return value
    try:
        return datetime.date.fromisoformat(str(value))
    except ValueError:
        return None


def submodule_paths() -> list[str]:
    if not GITMODULES.exists():
        return []
    paths = re.findall(r"^\s*path\s*=\s*(\S+)\s*$", GITMODULES.read_text(), re.MULTILINE)
    return paths


def slides_source_path(talk: dict) -> str | None:
    slides = talk.get("slides")
    if not isinstance(slides, dict):
        return None
    source = slides.get("source")
    if not source or re.match(r"^[a-z]+://", source):
        return None
    return source


def repo_relative_paths(talk: dict) -> list[tuple[str, str]]:
    """Return (field_label, path) pairs that should exist on disk."""
    out = []
    slides = talk.get("slides")
    if isinstance(slides, dict):
        for field in ("source", "pdf"):
            value = slides.get(field)
            if value and not re.match(r"^[a-z]+://", value):
                out.append((f"slides.{field}", value))
    resources = talk.get("resources")
    if resources and not re.match(r"^[a-z]+://", resources):
        out.append(("resources", resources))
    return out


def index_link_target(path: str) -> str:
    """talks/INDEX.md lives one directory below the repo root, so a
    repo-relative path needs a '../' prefix to resolve; a URL is used as-is."""
    if re.match(r"^[a-z]+://", path):
        return path
    return f"../{path}"


def fmt_link(label: str, url: str | None, *, relative: bool = False) -> str:
    if not url:
        return "—"
    target = index_link_target(url) if relative else url
    return f"[{label}]({target})"


def generate() -> None:
    talks = load_talks()
    talks_sorted = sorted(talks, key=lambda t: (parse_date(t["date"]) or datetime.date.min), reverse=True)

    lines: list[str] = []
    lines.append("# Talks Index")
    lines.append("")
    lines.append("Generated from `talks/talks.yaml` by `scripts/talks.py generate`. Do not hand-edit.")
    lines.append("")
    lines.append(
        "Legend: **Tooling** = deck-authoring tool used "
        "(Google Slides / Obsidian / Marp / Repo-hosted / — no deck exists). "
        "**Slides** links to the deck source (repo-relative or hosted). "
        "**Repo** links to the talk's own repo, when it has one."
    )
    lines.append("")

    year = None
    for talk in talks_sorted:
        date = parse_date(talk["date"])
        talk_year = date.year if date else "Unknown"
        if talk_year != year:
            year = talk_year
            if lines[-1]:
                lines.append("")
            lines.append(f"## {year}")
            lines.append("")
            lines.append("| Date | Talk | Event | Tooling | Slides | Repo | Video | Blog |")
            lines.append("|---|---|---|---|---|---|---|---|")

        events = talk.get("events") or []
        event_name = ", ".join(e["name"] for e in events) if events else "—"
        videos = [e["video"] for e in events if e.get("video")]

        slides = talk.get("slides")
        if slides == "none" or slides is None:
            slides_cell = "—"
        else:
            source = slides.get("source")
            hosted = slides.get("hosted")
            pdf = slides.get("pdf")
            cell_parts = []
            if source:
                cell_parts.append(fmt_link("source", source, relative=True))
            if pdf:
                cell_parts.append(fmt_link("pdf", pdf, relative=True))
            if hosted:
                cell_parts.append(fmt_link("hosted", hosted))
            slides_cell = ", ".join(cell_parts) if cell_parts else "—"

        title = talk["title"]
        blog = talk.get("blog")
        title_cell = fmt_link(title, blog) if blog else title

        tooling_label = TOOLING_LABELS.get(talk["tooling"], talk["tooling"])
        repo_cell = fmt_link("repo", talk.get("repo")) if talk.get("repo") else "—"
        video_cell = ", ".join(fmt_link("video", v) for v in videos) if videos else "—"
        blog_cell = fmt_link("blog", blog) if blog else "—"

        lines.append(
            f"| {date.isoformat() if date else talk['date']} | {title_cell} | {event_name} "
            f"| {tooling_label} | {slides_cell} | {repo_cell} | {video_cell} | {blog_cell} |"
        )

    lines.append("")
    INDEX_MD.write_text("\n".join(lines) + "\n")
    print(f"wrote {INDEX_MD.relative_to(REPO_ROOT)} ({len(talks)} talks)")


def check() -> int:
    talks = load_talks()
    errors: list[str] = []
    warnings: list[str] = []

    seen_ids: set[str] = set()
    for talk in talks:
        tid = talk.get("id")
        if not tid:
            errors.append("entry missing required field 'id'")
            continue
        if tid in seen_ids:
            errors.append(f"{tid}: duplicate id")
        seen_ids.add(tid)

        for field in ("title", "date", "tooling", "visibility"):
            if field not in talk:
                errors.append(f"{tid}: missing required field '{field}'")

        if "date" in talk and parse_date(talk["date"]) is None:
            errors.append(f"{tid}: unparseable date {talk['date']!r}")

        if REPO_ROOT.name == "private-content" and talk.get("visibility") == "public":
            errors.append(f"{tid}: visibility 'public' not allowed in private-content")

        for label, rel_path in repo_relative_paths(talk):
            candidate = (REPO_ROOT / rel_path).resolve()
            if REPO_ROOT.resolve() not in (candidate, *candidate.parents):
                errors.append(f"{tid}: {label} path escapes repo root: {rel_path}")
            elif not candidate.exists():
                errors.append(f"{tid}: {label} path does not exist: {rel_path}")

        if not talk.get("blog") and talk.get("visibility") == "public":
            warnings.append(f"{tid}: no 'blog' link")

        slides = talk.get("slides")
        if slides is None:
            warnings.append(f"{tid}: no slides link at all (add 'slides: none # reason' to silence)")

    declared_submodules = set(submodule_paths())
    referenced_submodules: set[str] = set()
    for talk in talks:
        source = slides_source_path(talk)
        if not source:
            continue
        for sub in declared_submodules:
            if source == sub or source.startswith(sub + "/"):
                referenced_submodules.add(sub)
                break

    for sub in declared_submodules - referenced_submodules:
        warnings.append(f"submodule {sub} has no talks.yaml entry referencing it")

    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if errors:
        print(f"check failed: {len(errors)} error(s), {len(warnings)} warning(s)", file=sys.stderr)
        return 1
    print(f"check passed: {len(talks)} talks, {len(warnings)} warning(s)")
    return 0


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in ("generate", "check"):
        print("usage: talks.py {generate|check}", file=sys.stderr)
        return 2
    if sys.argv[1] == "generate":
        generate()
        return 0
    return check()


if __name__ == "__main__":
    raise SystemExit(main())
