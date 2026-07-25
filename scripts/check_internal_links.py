#!/usr/bin/env python3
"""Validate internal links in the compatibility publication.

The compatibility site is both a GitHub repository and a GitHub Pages project.
Consequently the same local target can appear as a Markdown-relative path, a
project-root Pages URL, or a same-repository GitHub ``blob``/``tree`` URL.
This checker resolves all three forms without making network requests.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
PAGES_HOST = "chris-page-gov.github.io"
PAGES_PREFIXES = ("/ai-infrastructure-wiki", "/ai-infrastructure-wiki-compat")
GITHUB_HOST = "github.com"
GITHUB_REPOSITORIES = {
    ("chris-page-gov", "ai-infrastructure-wiki"),
    ("chris-page-gov", "ai-infrastructure-wiki-compat"),
}
SKIP_PARTS = {".git", "_site", "node_modules"}
LEGACY_LEAF_PREFIXES = {
    "document",
    "federated",
    "frameworks",
    "glossary",
    "organisations",
    "research",
    "stack",
    "standards",
    "uk-government",
}

MARKDOWN_INLINE_LINK = re.compile(r"!?\[[^\]]*\]\(\s*(<[^>]+>|[^\s)]+)")
MARKDOWN_REFERENCE_LINK = re.compile(r"^\s*\[[^\]]+\]:\s*(<[^>]+>|\S+)")
HTML_LINK = re.compile(
    r"""(?:href|src)\s*=\s*(?P<quote>["'])(?P<target>.*?)(?P=quote)""",
    re.IGNORECASE,
)
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")


def authored_pages() -> list[Path]:
    """Return every authored Markdown/HTML page in the publication."""

    pages: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".md", ".html"}:
            continue
        if any(part in SKIP_PARTS for part in path.relative_to(ROOT).parts):
            continue
        pages.append(path)
    return sorted(pages)


def markdown_targets(text: str) -> list[tuple[int, str]]:
    targets: list[tuple[int, str]] = []
    fence_marker: str | None = None
    for line_number, line in enumerate(text.splitlines(), start=1):
        fence = FENCE.match(line)
        if fence:
            marker = fence.group(1)[0]
            if fence_marker is None:
                fence_marker = marker
            elif marker == fence_marker:
                fence_marker = None
            continue
        if fence_marker is not None:
            continue
        targets.extend(
            (line_number, match.group(1))
            for match in MARKDOWN_INLINE_LINK.finditer(line)
        )
        reference = MARKDOWN_REFERENCE_LINK.match(line)
        if reference:
            targets.append((line_number, reference.group(1)))
        targets.extend(
            (line_number, match.group("target"))
            for match in HTML_LINK.finditer(line)
        )
    return targets


def html_targets(text: str) -> list[tuple[int, str]]:
    targets: list[tuple[int, str]] = []
    for match in HTML_LINK.finditer(text):
        line_number = text.count("\n", 0, match.start()) + 1
        targets.append((line_number, match.group("target")))
    return targets


def pages_relative_path(path: str) -> str | None:
    for prefix in PAGES_PREFIXES:
        if path == prefix or path == f"{prefix}/":
            return ""
        if path.startswith(f"{prefix}/"):
            return path[len(prefix) + 1 :]
    return None


def github_relative_path(path: str) -> str | None:
    parts = [part for part in path.split("/") if part]
    if len(parts) < 2 or tuple(parts[:2]) not in GITHUB_REPOSITORIES:
        return None
    remainder = parts[2:]
    if not remainder:
        return ""
    if remainder[0] in {"blob", "tree"}:
        if len(remainder) < 2:
            return ""
        remainder = remainder[2:]
    return "/".join(remainder)


def internal_url_path(target: str) -> str | None:
    parsed = urlsplit(target)
    if parsed.scheme not in {"http", "https"}:
        return None
    if parsed.netloc == PAGES_HOST:
        return pages_relative_path(unquote(parsed.path))
    if parsed.netloc == GITHUB_HOST:
        return github_relative_path(unquote(parsed.path))
    return None


def nested_internal_urls(target: str) -> list[str]:
    """Return compatibility-host URLs embedded in query parameters."""

    parsed = urlsplit(target)
    nested: list[str] = []
    for values in parse_qs(parsed.query).values():
        for value in values:
            if internal_url_path(value) is not None:
                nested.append(value)
    return nested


def candidate_path(source: Path, target: str) -> Path | None:
    target = target.strip().strip("<>")
    if not target or target.startswith("#"):
        return source

    parsed = urlsplit(target)
    if parsed.scheme:
        relative = internal_url_path(target)
        if relative is None:
            return None
        return (ROOT / relative).resolve()

    relative_path = unquote(parsed.path)
    if not relative_path:
        return source
    project_relative = pages_relative_path(relative_path)
    if project_relative is not None:
        return (ROOT / project_relative).resolve()
    if relative_path.startswith("/"):
        return (ROOT / relative_path.lstrip("/")).resolve()
    return (source.parent / relative_path).resolve()


def target_exists(path: Path) -> bool:
    try:
        path.relative_to(ROOT)
    except ValueError:
        return False
    if path.exists():
        return True
    if not path.suffix:
        return (
            path.with_suffix(".md").is_file()
            or path.with_suffix(".html").is_file()
            or (path / "index.html").is_file()
            or (path / "index.md").is_file()
        )
    return False


def delegated_legacy_leaf(source: Path, target: Path) -> bool:
    """Recognise links intentionally served by the legacy-family 404 router.

    The exact archived standard pages are immutable. Links from those legacy
    leaves into the wider extracted OKF corpus are served by the compatibility
    fallback rather than rewritten locally.
    """

    try:
        source_parts = source.relative_to(ROOT).parts
        target_parts = target.relative_to(ROOT).parts
    except ValueError:
        return False
    return (
        bool(source_parts)
        and source_parts[0] in LEGACY_LEAF_PREFIXES
        and bool(target_parts)
        and target_parts[0] in LEGACY_LEAF_PREFIXES
    )


def main() -> None:
    failures: list[str] = []
    checked = 0
    delegated = 0
    pages = authored_pages()

    for source in pages:
        text = source.read_text(encoding="utf-8")
        targets = (
            markdown_targets(text)
            if source.suffix.lower() == ".md"
            else html_targets(text)
        )
        for line_number, target in targets:
            candidates = [target, *nested_internal_urls(target)]
            for candidate in candidates:
                path = candidate_path(source, candidate)
                if path is None:
                    continue
                checked += 1
                if target_exists(path):
                    continue
                if delegated_legacy_leaf(source, path):
                    delegated += 1
                    continue
                try:
                    rendered = path.relative_to(ROOT).as_posix()
                except ValueError:
                    rendered = str(path)
                failures.append(
                    f"{source.relative_to(ROOT)}:{line_number}: "
                    f"missing internal target {candidate!r} -> {rendered}"
                )

    if failures:
        raise SystemExit(
            "internal link validation failed:\n- " + "\n- ".join(failures)
        )
    print(
        "internal link validation passed: "
        f"{len(pages)} authored pages, {checked} internal links, "
        f"{delegated} explicit legacy-family fallbacks"
    )


if __name__ == "__main__":
    main()
