from typing import List, Optional
from pydantic import BaseModel


class FileChange(BaseModel):
    path: str
    change_type: str  # "added", "modified", "deleted"
    additions: int
    deletions: int


class MergeRequest(BaseModel):
    project: str
    mr_id: int
    title: str
    author: str
    description: str
    web_url: str
    files: List[FileChange]


class LintIssue(BaseModel):
    file: str
    line: int
    code: str
    message: str


class LintResult(BaseModel):
    success: bool
    issues: List[LintIssue]


class TestCaseResult(BaseModel):
    name: str
    status: str  # "passed", "failed", "skipped"
    message: Optional[str] = None


class TestResult(BaseModel):
    success: bool
    cases: List[TestCaseResult]


class ReviewRisk(BaseModel):
    level: str  # "low", "medium", "high"
    reason: str


class ReviewReport(BaseModel):
    mr: MergeRequest
    summary: str
    risks: List[ReviewRisk]
    lint_result: LintResult
    test_result: TestResult
    suggested_questions: List[str]

TestCaseResult.__test__ = False
TestResult.__test__ = False
