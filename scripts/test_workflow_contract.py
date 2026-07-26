#!/usr/bin/env python3
"""Verify that compatibility Pages deployment is gated by validation."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CI = ROOT / ".github" / "workflows" / "ci.yml"
PAGES = ROOT / ".github" / "workflows" / "pages.yml"
VALIDATION_COMMAND = "sh scripts/validate_compatibility_publication.sh"
PINNED_ACTION = re.compile(
    r"^\s*(?:-\s+)?uses:\s+\S+@([0-9a-f]{40})(?:\s+#.*)?$"
)


def job_block(workflow: str, job: str) -> str:
    """Return one top-level job block from a GitHub Actions workflow."""

    lines = workflow.splitlines()
    marker = f"  {job}:"
    try:
        start = lines.index(marker)
    except ValueError as error:
        raise AssertionError(f"missing {job!r} job") from error

    end = len(lines)
    for index in range(start + 1, len(lines)):
        if re.fullmatch(r"  [A-Za-z0-9_-]+:", lines[index]):
            end = index
            break
    return "\n".join(lines[start:end])


class WorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ci = CI.read_text(encoding="utf-8")
        cls.pages = PAGES.read_text(encoding="utf-8")

    def test_both_workflows_use_the_same_validation_entrypoint(self) -> None:
        self.assertIn(VALIDATION_COMMAND, job_block(self.ci, "validate"))
        self.assertIn(VALIDATION_COMMAND, job_block(self.pages, "validate"))

    def test_pages_deploy_requires_validation(self) -> None:
        deploy = job_block(self.pages, "deploy")
        self.assertRegex(deploy, r"(?m)^    needs: validate$")

    def test_pages_write_permissions_are_deploy_scoped(self) -> None:
        pre_jobs = self.pages.split("\njobs:\n", 1)[0]
        self.assertIn("permissions:\n  contents: read", pre_jobs)
        self.assertNotIn("pages: write", pre_jobs)
        self.assertNotIn("id-token: write", pre_jobs)

        validate = job_block(self.pages, "validate")
        self.assertNotIn("pages: write", validate)
        self.assertNotIn("id-token: write", validate)

        deploy = job_block(self.pages, "deploy")
        self.assertIn("permissions:\n      contents: read", deploy)
        self.assertIn("pages: write", deploy)
        self.assertIn("id-token: write", deploy)

    def test_all_workflow_actions_are_commit_pinned(self) -> None:
        for path, workflow in ((CI, self.ci), (PAGES, self.pages)):
            action_lines = [
                line for line in workflow.splitlines() if "uses:" in line
            ]
            self.assertGreater(action_lines, [], path.as_posix())
            for line in action_lines:
                self.assertIsNotNone(
                    PINNED_ACTION.fullmatch(line),
                    f"{path.relative_to(ROOT)} has an unpinned action: {line.strip()}",
                )


if __name__ == "__main__":
    unittest.main()
