#!/usr/bin/env python3
"""Validate the compatibility publication's critical legacy link surface."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
REFERENCE_LINK = re.compile(r"^\[[^\]]+\]:\s+(\S+)", re.MULTILINE)
LEGISLATION = "https://chris-page-gov.github.io/okf-uk-legislation"
EXPLORER = "https://chris-page-gov.github.io/okf-explorer"
GOVERNMENT_APIS = "https://chris-page-gov.github.io/okf-uk-government-apis"
GOV_UK_CKAN = (
    "https://chris-page-gov.github.io/"
    "ai-engineering-lab-hackathon-london-2026/gov-ckan"
)


def validate_snapshot(failures: list[str]) -> int:
    """Prove the archived README/docs bytes remain the approved snapshot."""

    manifest_path = ROOT / "snapshot-files.sha256"
    expected: dict[str, str] = {}
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        expected[relative] = digest

    actual_paths = {"README.md"}
    actual_paths.update(
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "docs").rglob("*")
        if path.is_file()
    )
    if actual_paths != set(expected):
        missing = sorted(set(expected) - actual_paths)
        added = sorted(actual_paths - set(expected))
        if missing:
            failures.append(f"documentation snapshot: missing files {missing}")
        if added:
            failures.append(f"documentation snapshot: unrecorded files {added}")

    for relative, expected_digest in expected.items():
        path = ROOT / relative
        if not path.is_file():
            continue
        actual_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_digest != expected_digest:
            failures.append(f"documentation snapshot: digest mismatch for {relative}")
    return len(expected)


def validate_moved_descriptor(
    failures: list[str], relative: str, expected_target: str
) -> None:
    path = ROOT / relative
    if path.suffix == ".yamlld":
        try:
            fields = dict(
                line.split(":", 1)
                for line in path.read_text(encoding="utf-8").splitlines()
                if ":" in line and not line.startswith('"@context"')
            )
        except OSError as error:
            failures.append(f"{relative}: cannot read YAML-LD moved descriptor: {error}")
            return
        fields = {key.strip(): value.strip() for key, value in fields.items()}
        if fields.get("schema") != "okf-moved.v1":
            failures.append(f"{relative}: invalid moved schema")
        if fields.get("kind") != "okf-moved":
            failures.append(f"{relative}: invalid moved kind")
        if fields.get("moved_to") != expected_target:
            failures.append(
                f"{relative}: expected moved_to {expected_target}, "
                f"got {fields.get('moved_to')}"
            )
        return

    try:
        descriptor = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        failures.append(f"{relative}: cannot read JSON moved descriptor: {error}")
        return
    if descriptor.get("schema") != "okf-moved.v1":
        failures.append(f"{relative}: invalid moved schema")
    if descriptor.get("kind") != "okf-moved":
        failures.append(f"{relative}: invalid moved kind")
    if descriptor.get("moved_to") != expected_target:
        failures.append(
            f"{relative}: expected moved_to {expected_target}, "
            f"got {descriptor.get('moved_to')}"
        )


def local_target(source: Path, value: str) -> Path | None:
    value = value.strip().strip("<>")
    parsed = urlsplit(value)
    if parsed.scheme or value.startswith("#"):
        return None
    return (source.parent / unquote(parsed.path)).resolve()


def main() -> None:
    failures: list[str] = []
    snapshot_count = validate_snapshot(failures)
    mapping = json.loads((ROOT / "compatibility-map.json").read_text(encoding="utf-8"))
    machine_routes = mapping.get("machine_routes", {})
    static_redirects = mapping.get("static_redirects", {})

    for relative in ("README.md", "docs/index.md"):
        source = ROOT / relative
        text = source.read_text(encoding="utf-8")
        targets = MARKDOWN_LINK.findall(text) + REFERENCE_LINK.findall(text)
        for value in targets:
            target = local_target(source, value)
            if target is not None and not target.exists():
                failures.append(f"{relative}: missing local link target {value}")

    essential = {
        "docs/index.html",
        "docs/index.md",
        "docs/okf-bundle-authoring.md",
        "docs/use-okf-explorer.md",
        "docs/ai-okf-usage.md",
        "compatibility-map.json",
        "snapshot-files.sha256",
        "legislation/index.md",
        "legislation/log.md",
        "uk-government-apis/index.md",
        "uk-government-apis/log.md",
        "whole-law/index.md",
        "whole-law/log.md",
        "evaluation/whole-law/README.md",
        "scripts/check_redirects.mjs",
    }
    required = sorted(essential | set(machine_routes) | set(static_redirects))
    for relative in required:
        if not (ROOT / relative).is_file():
            failures.append(f"missing required compatibility file {relative}")

    if mapping.get("documentation_snapshot_commit") != "650a928":
        failures.append("compatibility-map.json: unexpected documentation snapshot")
    if mapping.get("documentation_snapshot_manifest") != "snapshot-files.sha256":
        failures.append("compatibility-map.json: missing documentation snapshot manifest")

    canonical = mapping.get("canonical", {})
    expected_canonical = {
        "explorer": f"{EXPLORER}/",
        "explorer_repository": "https://github.com/chris-page-gov/okf-explorer",
        "explorer_registry": f"{EXPLORER}/okf-registry.json",
        "explorer_evaluation": (
            f"{EXPLORER}/evaluation/okf-explorer/questions.json"
        ),
        "gov_uk_ckan_descriptor": f"{GOV_UK_CKAN}/okf-explorer.json",
        "gov_uk_ckan": {
            "publication": f"{GOV_UK_CKAN}/",
            "repository": (
                "https://github.com/chris-page-gov/"
                "ai-engineering-lab-hackathon-london-2026"
            ),
            "descriptor": f"{GOV_UK_CKAN}/okf-explorer.json",
            "evaluation": f"{EXPLORER}/evaluation/gov-ckan/questions.json",
        },
        "uk_government_apis": {
            "publication": f"{GOVERNMENT_APIS}/",
            "repository": "https://github.com/chris-page-gov/okf-uk-government-apis",
            "descriptor": f"{GOVERNMENT_APIS}/okf-explorer.json",
            "yaml_ld": f"{GOVERNMENT_APIS}/okf-bundle.yamlld",
            "json_ld": f"{GOVERNMENT_APIS}/okf-bundle.jsonld",
            "documentation": (
                f"{GOVERNMENT_APIS}/docs/UK-Government-API-OKF.md"
            ),
        },
        "legislation": {
            "publication": f"{LEGISLATION}/",
            "repository": "https://github.com/chris-page-gov/okf-uk-legislation",
            "descriptor": f"{LEGISLATION}/okf-explorer.json",
            "yaml_ld": f"{LEGISLATION}/okf-bundle.yamlld",
            "json_ld": f"{LEGISLATION}/okf-bundle.jsonld",
            "documentation": f"{LEGISLATION}/docs/",
            "evaluation": f"{LEGISLATION}/evaluation/",
            "evaluation_schema": f"{LEGISLATION}/evaluation/answer-schema.json",
            "evaluation_questions": f"{LEGISLATION}/evaluation/questions.json",
        },
        "whole_law": {
            "publication": f"{LEGISLATION}/whole-law/",
            "descriptor": f"{LEGISLATION}/whole-law/okf-explorer.json",
            "yaml_ld": f"{LEGISLATION}/whole-law/okf-bundle.yamlld",
            "json_ld": f"{LEGISLATION}/whole-law/okf-bundle.jsonld",
            "markdown_index": f"{LEGISLATION}/whole-law/index.md",
            "documentation": f"{LEGISLATION}/whole-law/docs/",
            "evaluation": f"{LEGISLATION}/whole-law/evaluation/",
            "evaluation_schema": (
                f"{LEGISLATION}/whole-law/evaluation/answer-schema.json"
            ),
            "evaluation_questions": (
                f"{LEGISLATION}/whole-law/evaluation/questions.json"
            ),
        },
    }
    if canonical != expected_canonical:
        failures.append("compatibility-map.json: canonical URL contract changed")

    for relative, expected_target in machine_routes.items():
        validate_moved_descriptor(failures, relative, expected_target)

    discovered_moved = set()
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix not in {".json", ".jsonld", ".yamlld"}:
            continue
        text = path.read_text(encoding="utf-8")
        if '"kind": "okf-moved"' in text or "kind: okf-moved" in text:
            discovered_moved.add(path.relative_to(ROOT).as_posix())
    if discovered_moved != set(machine_routes):
        missing = sorted(set(machine_routes) - discovered_moved)
        unregistered = sorted(discovered_moved - set(machine_routes))
        if missing:
            failures.append(f"machine route manifest: missing moved files {missing}")
        if unregistered:
            failures.append(
                f"machine route manifest: unregistered moved files {unregistered}"
            )

    for relative, expected_target in static_redirects.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        expected_origin = (
            f"{urlsplit(expected_target).scheme}://{urlsplit(expected_target).netloc}"
        )
        if expected_target not in text and expected_origin not in text:
            failures.append(f"{relative}: missing canonical target {expected_target}")
        if "location.replace" not in text:
            failures.append(f"{relative}: missing location.replace redirect")
        if "location.search" not in text or "location.hash" not in text:
            failures.append(f"{relative}: redirect does not preserve query and fragment")

    root_html = (ROOT / "index.html").read_text(encoding="utf-8")
    fallback = (ROOT / "404.html").read_text(encoding="utf-8")
    ckan_html = (ROOT / "gov-ckan/index.html").read_text(encoding="utf-8")
    for label, needle, text in (
        ("root", "GOV.UK CKAN data", root_html),
        ("root", "UK Government APIs and data discovery", root_html),
        ("root", "docs/index.html", root_html),
        ("root", f"{LEGISLATION}/whole-law/", root_html),
        (
            "gov-ckan",
            "ai-engineering-lab-hackathon-london-2026%2Fgov-ckan%2Fokf-explorer.json",
            ckan_html,
        ),
        ("404", "path.startsWith('/docs/')", fallback),
        ("404", "ai-engineering-lab-hackathon-london-2026", fallback),
        ("404", "path.startsWith('/evaluation/legislation/')", fallback),
        ("404", "path.startsWith('/evaluation/whole-law/')", fallback),
        ("404", "path.startsWith('/legislation/evaluation/')", fallback),
        ("404", "path.startsWith('/legislation/docs/')", fallback),
        ("404", "path.startsWith('/docs/uk-legislation/')", fallback),
        ("404", "path.startsWith('/whole-law/')", fallback),
        ("404", "path.startsWith('/data-gov-uk/')", fallback),
        ("404", "path.startsWith('/data.gov.uk/')", fallback),
        ("404", "location.search + location.hash", fallback),
    ):
        if needle not in text:
            failures.append(f"{label}: missing {needle}")

    if failures:
        raise SystemExit("compatibility validation failed:\n- " + "\n- ".join(failures))
    print(
        "compatibility validation passed: "
        f"{len(required)} critical files, "
        f"{snapshot_count} immutable snapshot files, "
        f"{len(machine_routes)} moved descriptors, "
        f"and {len(static_redirects)} static redirects"
    )


if __name__ == "__main__":
    main()
