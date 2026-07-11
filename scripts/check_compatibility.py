#!/usr/bin/env python3
"""Validate the compatibility publication's critical legacy link surface."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
REFERENCE_LINK = re.compile(r"^\[[^\]]+\]:\s+(\S+)", re.MULTILINE)


def local_target(source: Path, value: str) -> Path | None:
    value = value.strip().strip("<>")
    parsed = urlsplit(value)
    if parsed.scheme or value.startswith("#"):
        return None
    return (source.parent / unquote(parsed.path)).resolve()


def main() -> None:
    failures: list[str] = []
    for relative in ("README.md", "docs/index.md"):
        source = ROOT / relative
        text = source.read_text(encoding="utf-8")
        targets = MARKDOWN_LINK.findall(text) + REFERENCE_LINK.findall(text)
        for value in targets:
            target = local_target(source, value)
            if target is not None and not target.exists():
                failures.append(f"{relative}: missing local link target {value}")

    required = (
        "docs/index.html",
        "docs/index.md",
        "docs/okf-bundle-authoring.md",
        "docs/use-okf-explorer.md",
        "docs/ai-okf-usage.md",
        "gov-ckan/index.html",
        "gov-ckan/okf-explorer.json",
        "compatibility-map.json",
    )
    for relative in required:
        if not (ROOT / relative).is_file():
            failures.append(f"missing required compatibility file {relative}")

    mapping = json.loads((ROOT / "compatibility-map.json").read_text(encoding="utf-8"))
    if mapping.get("documentation_snapshot_commit") != "650a928":
        failures.append("compatibility-map.json: unexpected documentation snapshot")

    ckan = json.loads((ROOT / "gov-ckan/okf-explorer.json").read_text(encoding="utf-8"))
    if ckan.get("kind") != "okf-moved" or "gov-ckan/okf-explorer.json" not in ckan.get("moved_to", ""):
        failures.append("gov-ckan/okf-explorer.json: invalid moved descriptor")

    root_html = (ROOT / "index.html").read_text(encoding="utf-8")
    fallback = (ROOT / "404.html").read_text(encoding="utf-8")
    for label, needle, text in (
        ("root", "GOV.UK CKAN data", root_html),
        ("root", "docs/index.html", root_html),
        ("404", "path.startsWith('/docs/')", fallback),
        ("404", "ai-engineering-lab-hackathon-london-2026", fallback),
    ):
        if needle not in text:
            failures.append(f"{label}: missing {needle}")

    if failures:
        raise SystemExit("compatibility validation failed:\n- " + "\n- ".join(failures))
    print(f"compatibility validation passed: {len(required)} critical files and README links")


if __name__ == "__main__":
    main()
