from __future__ import annotations

from .gitlab_client import GitLabClient
from .llm_client import LLMClient
from .models import ReviewReport
from .tools import diff_tool, lint_tool, test_tool



class MRReviewer:
    """
    Main orchestrator that wires GitLab client, tools and LLM together.
    """

    def __init__(
        self,
        gitlab_client: GitLabClient | None = None,
        llm_client: LLMClient | None = None,
    ):
        self._gitlab = gitlab_client or GitLabClient()
        self._llm = llm_client or LLMClient()

    def review_merge_request(self, project: str, mr_id: int) -> ReviewReport:
        # 1) Fetch MR & changes
        mr = self._gitlab.get_merge_request(project, mr_id)
        changes = self._gitlab.get_mr_changes(project, mr_id)

        stats = diff_tool.summarise_changes(changes)
        num_files = stats["num_files"]
        total_additions = stats["total_additions"]
        total_deletions = stats["total_deletions"]

        # 2) Run lint on changed paths
        changed_paths = [c.path for c in changes if c.change_type != "deleted"]
        lint_result = lint_tool.run_lint(changed_paths)

        # 3) Run tests (basic for now)
        test_result = test_tool.run_tests()

        # 4) Ask LLM to summarise + assess risks + suggest questions
        summary = self._llm.summarise_changes(
            mr,
            changes,
            num_files=num_files,
            total_additions=total_additions,
            total_deletions=total_deletions,
        )

        risks = self._llm.assess_risks(
            mr,
            changes,
            summary=summary,
            lint_result=lint_result,
            test_result=test_result,
            num_files=num_files,
            total_additions=total_additions,
            total_deletions=total_deletions,
        )

        questions = self._llm.generate_review_questions(
            mr,
            changes,
            summary=summary,
            risks=risks,
            lint_result=lint_result,
            test_result=test_result,
        )

        return ReviewReport(
            mr=mr,
            summary=summary,
            risks=risks,
            lint_result=lint_result,
            test_result=test_result,
            suggested_questions=questions,
        )
