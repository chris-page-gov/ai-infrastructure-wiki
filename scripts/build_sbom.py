#!/usr/bin/env python3
"""Build/check the compatibility publication's deterministic CycloneDX SBOM."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "release-assurance" / "compat.sbom.cdx.json"
ACTION = re.compile(
    r"^\s*(?:-\s+)?uses:\s+([^@\s]+)@([0-9a-f]{40})\b",
    re.MULTILINE,
)


def build() -> dict[str, object]:
    usages: dict[tuple[str, str], set[str]] = {}
    for workflow in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        for name, revision in ACTION.findall(workflow.read_text(encoding="utf-8")):
            usages.setdefault((name, revision), set()).add(
                workflow.relative_to(ROOT).as_posix()
            )
    if not usages:
        raise ValueError("no commit-pinned workflow Actions found")
    components = []
    for (name, revision), workflows in sorted(usages.items()):
        reference = f"pkg:github/{name}@{revision}"
        components.append(
            {
                "bom-ref": reference,
                "name": name,
                "properties": [
                    {"name": "okf:ref-kind", "value": "commit-sha"},
                    {
                        "name": "okf:workflows",
                        "value": ", ".join(sorted(workflows)),
                    },
                ],
                "purl": reference,
                "type": "application",
                "version": revision,
            }
        )
    root_ref = "pkg:github/chris-page-gov/ai-infrastructure-wiki@compat"
    preserved = ROOT / "preserved-routes.sha256"
    return {
        "bomFormat": "CycloneDX",
        "components": components,
        "dependencies": [
            {
                "dependsOn": [row["bom-ref"] for row in components],
                "ref": root_ref,
            }
        ],
        "metadata": {
            "component": {
                "bom-ref": root_ref,
                "licenses": [{"license": {"id": "MIT"}}],
                "name": "ai-infrastructure-wiki compatibility publication",
                "type": "application",
                "version": "compat-snapshot",
            },
            "properties": [
                {
                    "name": "okf:preserved-routes-sha256",
                    "value": hashlib.sha256(preserved.read_bytes()).hexdigest(),
                }
            ],
            "tools": {
                "components": [
                    {
                        "name": "build_sbom.py",
                        "type": "application",
                        "version": "1.0.0",
                    }
                ]
            },
        },
        "specVersion": "1.6",
        "version": 1,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = json.dumps(build(), indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != rendered:
            print(f"stale or missing compatibility SBOM: {OUTPUT.relative_to(ROOT)}")
            return 1
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(rendered, encoding="utf-8")
    count = len(json.loads(rendered)["components"])
    print(f"compatibility CycloneDX SBOM passed: {count} pinned Action components")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
