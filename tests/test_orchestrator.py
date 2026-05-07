from agentic_mr_reviewer.models import (
    MergeRequest,
    FileChange,
    LintResult,
    LintIssue,
    TestResult,
    TestCaseResult,
    ReviewRisk,
)
from agentic_mr_reviewer.orchestrator import MRReviewer


class DummyGitLab:
    def get_merge_request(self, project: str, mr_id: int) -> MergeRequest:
        return MergeRequest(
            project=project,
            mr_id=mr_id,
            title="Dummy MR",
            author="Tester",
            description="Dummy description",
            web_url="https://gitlab.example.com/dummy",
            files=[],
        )

    def get_mr_changes(self, project: str, mr_id: int):
        return [
            FileChange(
                path="foo.py",
                change_type="modified",
                additions=10,
                deletions=2,
            )
        ]


class DummyLLM:
    def summarise_changes(self, *args, **kwargs) -> str:
        return "- Dummy summary"

    def assess_risks(self, *args, **kwargs):
        return [ReviewRisk(level="low", reason="Dummy")]

    def generate_review_questions(self, *args, **kwargs):
        return ["Why is this dummy?"]


def test_orchestrator_basic(monkeypatch):
    # monkeypatch tools to avoid running real ruff/pytest
    import agentic_mr_reviewer.tools.lint_tool as lint_tool
    import agentic_mr_reviewer.tools.test_tool as test_tool

    monkeypatch.setattr(
        lint_tool, "run_lint", lambda paths: LintResult(success=True, issues=[])
    )
    monkeypatch.setattr(
        test_tool,
        "run_tests",
        lambda pytest_args=None: TestResult(
            success=True, cases=[TestCaseResult(name="pytest", status="passed")]
        ),
    )

    reviewer = MRReviewer(gitlab_client=DummyGitLab(), llm_client=DummyLLM())
    report = reviewer.review_merge_request("group/proj", 1)

    assert report.mr.title == "Dummy MR"
    assert report.summary
    assert report.risks
    assert report.suggested_questions
