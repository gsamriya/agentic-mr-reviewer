from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List

from ..models import LintIssue, LintResult


def run_lint(paths: List[str]) -> LintResult:
    """
    Run ruff on the specified paths.
    Very simple parser: expects `file:line:col: CODE message`.
    """

    if not paths:
        return LintResult(success=True, issues=[])

    # Filter only existing files
    real_paths = [p for p in paths if Path(p).exists()]
    if not real_paths:
        return LintResult(success=True, issues=[])

    cmd = ["ruff", "check", "--exit-zero", "--format", "text", *real_paths]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    issues: list[LintIssue] = []
    for line in proc.stdout.splitlines():
        # naive parse: path:line:col: CODE message
        try:
            path_part, rest = line.split(":", 1)
            line_part, rest = rest.split(":", 1)
            _col, rest = rest.split(":", 1)
            rest = rest.strip()
            if " " in rest:
                code, msg = rest.split(" ", 1)
            else:
                code, msg = rest, ""
            issues.append(
                LintIssue(
                    file=path_part.strip(),
                    line=int(line_part.strip()),
                    code=code.strip(),
                    message=msg.strip(),
                )
            )
        except ValueError:
            # ignore lines that don't match expected format
            continue

    success = len(issues) == 0
    return LintResult(success=success, issues=issues)
