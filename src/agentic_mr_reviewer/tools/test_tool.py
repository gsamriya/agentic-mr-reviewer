from __future__ import annotations

import subprocess
from typing import List

from ..models import TestCaseResult, TestResult


def run_tests(pytest_args: List[str] | None = None) -> TestResult:
    """
    Run pytest and convert output into a coarse-grained TestResult.

    For now we only check overall exit code, without parsing individual tests.
    can later extend this to use `pytest --json-report` or similar.
    """
    pytest_args = pytest_args or []

    cmd = ["pytest", "-q", *pytest_args]
    proc = subprocess.run(cmd, capture_output=True, text=True)

    success = proc.returncode == 0
    cases: list[TestCaseResult] = []

    # Naive: treat stdout lines as "tests"
    # Later: parse pytest output or use a plugin.
    if not success:
        cases.append(
            TestCaseResult(
                name="pytest",
                status="failed",
                message=proc.stdout + "\n" + proc.stderr,
            )
        )
    else:
        cases.append(TestCaseResult(name="pytest", status="passed"))

    return TestResult(success=success, cases=cases)
