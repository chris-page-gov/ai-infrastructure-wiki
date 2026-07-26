#!/usr/bin/env python3
"""Focused tests for the compatibility publication's URL resolution rules."""

from __future__ import annotations

import unittest
from pathlib import Path
from urllib.parse import quote

import check_internal_links as links


class InternalLinkResolutionTests(unittest.TestCase):
    source = links.ROOT / "docs" / "index.md"

    def test_markdown_relative_target(self) -> None:
        target = links.candidate_path(self.source, "../standards/dcat.md")
        self.assertEqual(target, links.ROOT / "standards" / "dcat.md")
        self.assertTrue(links.target_exists(target))

    def test_pages_project_target(self) -> None:
        target = links.candidate_path(
            self.source,
            "https://chris-page-gov.github.io/"
            "ai-infrastructure-wiki/constraints/source-constraints.yamlld",
        )
        self.assertEqual(
            target, links.ROOT / "constraints" / "source-constraints.yamlld"
        )
        self.assertTrue(links.target_exists(target))

    def test_pages_project_root_relative_target(self) -> None:
        target = links.candidate_path(
            self.source, "/ai-infrastructure-wiki/docs/index.md"
        )
        self.assertEqual(target, links.ROOT / "docs" / "index.md")
        self.assertTrue(links.target_exists(target))

    def test_same_repository_github_target(self) -> None:
        target = links.candidate_path(
            self.source,
            "https://github.com/chris-page-gov/ai-infrastructure-wiki/"
            "blob/main/standards/w3c-prov.md",
        )
        self.assertEqual(target, links.ROOT / "standards" / "w3c-prov.md")
        self.assertTrue(links.target_exists(target))

    def test_encoded_bundle_target_is_checked(self) -> None:
        bundle = (
            "https://chris-page-gov.github.io/ai-infrastructure-wiki/"
            "legislation/okf-explorer.json"
        )
        explorer = (
            "https://chris-page-gov.github.io/okf-explorer/"
            f"?bundle={quote(bundle, safe='')}"
        )
        self.assertEqual(links.nested_internal_urls(explorer), [bundle])

    def test_missing_target_is_not_accepted(self) -> None:
        target = links.candidate_path(self.source, "does-not-exist.md")
        self.assertIsInstance(target, Path)
        self.assertFalse(links.target_exists(target))

    def test_fenced_example_is_not_treated_as_a_link(self) -> None:
        text = "```md\n[example](does-not-exist.md)\n```\n[real](index.md)\n"
        self.assertEqual(links.markdown_targets(text), [(4, "index.md")])


if __name__ == "__main__":
    unittest.main()
