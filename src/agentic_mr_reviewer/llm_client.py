from __future__ import annotations

import json
from typing import Any, Dict, List

from openai import OpenAI

from .config import get_settings
from .models import (
    FileChange,
    LintResult,
    ReviewRisk,
    TestResult,
    MergeRequest,
)


class LLMClient:
    """
    Very small wrapper around an LLM provider.
    You can swap this out for internal / self-hosted models.
    """

    def __init__(self):
        settings = get_settings()

        self._model = settings.llm_model
        api_key = settings.llm_api_key
        base_url = settings.llm_base_url or None

        # If api_key is missing or set to "dummy", run in dry-run mode
        self._enabled = bool(api_key and api_key != "dummy")

        if self._enabled:
            self._client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            self._client = None

    # ---------- prompts building helpers ----------

    @staticmethod
    def _build_summarise_changes_user_content(
        mr: MergeRequest,
        changes: List[FileChange],
        num_files: int,
        total_additions: int,
        total_deletions: int,
    ) -> str:
        file_lines = "\n".join(
            f"- {c.path} ({c.change_type}, +{c.additions} / -{c.deletions})"
            for c in changes
        )
        return f"""
Merge Request Title:
{mr.title}

Merge Request Description:
{mr.description}

Basic stats:
- Number of changed files: {num_files}
- Total additions: {total_additions}
- Total deletions: {total_deletions}

Changed files:
{file_lines}

Task:
Summarise the behavioural and structural impact of this merge request.
Emphasise what changed and where, not the raw line counts.
Output the answer as 3–7 bullet points.
"""

    @staticmethod
    def _build_assess_risks_user_content(
        mr: MergeRequest,
        changes: List[FileChange],
        summary: str,
        lint_result: LintResult,
        test_result: TestResult,
        num_files: int,
        total_additions: int,
        total_deletions: int,
    ) -> str:
        file_lines = "\n".join(
            f"- {c.path} ({c.change_type}, +{c.additions} / -{c.deletions})"
            for c in changes
        )

        if lint_result.issues:
            lint_summary = "\n".join(
                f"- {iss.file}:{iss.line} [{iss.code}] {iss.message}"
                for iss in lint_result.issues[:20]
            )
        else:
            lint_summary = "No lint issues detected."

        failed_cases = [c for c in test_result.cases if c.status == "failed"]
        if failed_cases:
            test_summary = "Some tests failed:\n" + "\n".join(
                f"- {c.name}: {c.message or 'no message'}"
                for c in failed_cases[:20]
            )
        else:
            test_summary = "All tests passed."

        return f"""
Merge Request:
- Title: {mr.title}
- Description: {mr.description}
- Number of changed files: {num_files}
- Total additions: {total_additions}
- Total deletions: {total_deletions}

Changed files:
{file_lines}

Summary of changes:
{summary}

Lint result:
{lint_summary}

Test result:
{test_summary}

Task:
Identify potential risks introduced by this merge request and return them in JSON:

{{ "risks": [ {{ "level": "low|medium|high", "reason": "..." }}, ... ] }}

If you see no meaningful risks, return {{ "risks": [] }}.
"""

    @staticmethod
    def _build_generate_questions_user_content(
        mr: MergeRequest,
        changes: List[FileChange],
        summary: str,
        risks: List[ReviewRisk],
        lint_result: LintResult,
        test_result: TestResult,
    ) -> str:
        file_lines = "\n".join(
            f"- {c.path} ({c.change_type})" for c in changes
        )

        risk_lines = (
            "\n".join(f"- [{r.level}] {r.reason}" for r in risks)
            if risks
            else "No significant risks identified."
        )

        if lint_result.issues:
            lint_summary = "\n".join(
                f"- {iss.file}:{iss.line} [{iss.code}] {iss.message}"
                for iss in lint_result.issues[:10]
            )
        else:
            lint_summary = "No lint issues detected."

        failed_cases = [c for c in test_result.cases if c.status == "failed"]
        if failed_cases:
            test_summary = "Some tests failed:\n" + "\n".join(
                f"- {c.name}: {c.message or 'no message'}"
                for c in failed_cases[:10]
            )
        else:
            test_summary = "All tests passed."

        return f"""
Merge Request:
- Title: {mr.title}
- Description: {mr.description}

Changed files:
{file_lines}

Summary of changes:
{summary}

Identified risks:
{risk_lines}

Lint result:
{lint_summary}

Test result:
{test_summary}

Task:
Generate a list of concrete, useful questions that a human reviewer could ask the author of this merge request.
Return them in JSON as:

{{ "questions": ["Q1?", "Q2?", "..."] }}

Aim for 3–10 questions depending on complexity.
"""

    # ---------- public methods ----------

    def _chat(self, system: str, user: str) -> str:
        if not self._enabled:
            # Dry-run fallback for demos / offline use
            return (
                "[LLM disabled – using placeholder summary]\n"
                "• This merge request modifies code in several files.\n"
                "• It appears related to data pipelines / Airflow DAGs.\n"
                "• Please run a manual review for detailed semantics."
            )

        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.1,
        )
        return resp.choices[0].message.content or ""

    def _chat_json(self, system: str, user: str) -> Dict[str, Any]:
        if not self._enabled:
            # Simple dry-run JSON output
            if "risks" in user:  # crude detection for assess_risks
                return {"risks": []}
            if "questions" in user:
                return {"questions": ["[LLM disabled] No questions generated."]}
            return {}

        text = self._chat(system, user)
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]
        return json.loads(text)

    def summarise_changes(
        self,
        mr: MergeRequest,
        changes: List[FileChange],
        num_files: int,
        total_additions: int,
        total_deletions: int,
    ) -> str:
        system = (
            "You are a senior software engineer summarising GitLab "
            "merge requests. Use 3–7 bullet points."
        )
        user = self._build_summarise_changes_user_content(
            mr, changes, num_files, total_additions, total_deletions
        )
        return self._chat(system, user)

    def assess_risks(
        self,
        mr: MergeRequest,
        changes: List[FileChange],
        summary: str,
        lint_result: LintResult,
        test_result: TestResult,
        num_files: int,
        total_additions: int,
        total_deletions: int,
    ) -> List[ReviewRisk]:
        system = (
            "You are a careful senior engineer assessing risks. "
            "Return JSON with a 'risks' list."
        )
        user = self._build_assess_risks_user_content(
            mr,
            changes,
            summary,
            lint_result,
            test_result,
            num_files,
            total_additions,
            total_deletions,
        )
        data = self._chat_json(system, user)
        risks_data = data.get("risks", [])
        return [ReviewRisk(**r) for r in risks_data]

    def generate_review_questions(
        self,
        mr: MergeRequest,
        changes: List[FileChange],
        summary: str,
        risks: List[ReviewRisk],
        lint_result: LintResult,
        test_result: TestResult,
    ) -> List[str]:
        system = (
            "You are a senior engineer generating review questions. "
            "Return JSON with a 'questions' list of strings."
        )
        user = self._build_generate_questions_user_content(
            mr, changes, summary, risks, lint_result, test_result
        )
        data = self._chat_json(system, user)
        return list(data.get("questions", []))
