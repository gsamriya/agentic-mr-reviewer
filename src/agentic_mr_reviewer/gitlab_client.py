from __future__ import annotations

from typing import List
import urllib.parse

import httpx

from .config import get_settings
from .models import FileChange, MergeRequest


class GitLabClient:
    """
    Basic Minimal GitLab API wrapper for MR metadata & changes.
    """

    def __init__(self, base_url: str | None = None, token: str | None = None):
        settings = get_settings()
        self.base_url = base_url or settings.gitlab_url.rstrip("/")
        self.token = token or settings.gitlab_token

        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Private-Token": self.token,
                "User-Agent": "agentic-mr-reviewer/0.1",
            },
            timeout=20.0,
        )

    def _project_path(self, project: str) -> str:
        # e.g. "group/subgroup/project" → URL-encoded path
        return urllib.parse.quote_plus(project)

    def get_merge_request(self, project: str, mr_id: int) -> MergeRequest:
        project_path = self._project_path(project)
        # `iid` is the MR ID within project
        url = f"/api/v4/projects/{project_path}/merge_requests/{mr_id}"
        resp = self._client.get(url)
        resp.raise_for_status()
        data = resp.json()

        return MergeRequest(
            project=project,
            mr_id=mr_id,
            title=data["title"],
            author=data["author"]["name"],
            description=data.get("description") or "",
            web_url=data["web_url"],
            files=[],  # filled in by get_mr_changes
        )

    def get_mr_changes(self, project: str, mr_id: int) -> List[FileChange]:
        project_path = self._project_path(project)
        url = f"/api/v4/projects/{project_path}/merge_requests/{mr_id}/changes"
        resp = self._client.get(url)
        resp.raise_for_status()
        data = resp.json()

        changes: List[FileChange] = []
        for ch in data.get("changes", []):
            changes.append(
                FileChange(
                    path=ch["new_path"],
                    change_type=self._detect_change_type(ch),
                    additions=ch.get("additions", 0),
                    deletions=ch.get("deletions", 0),
                )
            )
        return changes

    @staticmethod
    def _detect_change_type(change: dict) -> str:
        if change.get("new_file"):
            return "added"
        if change.get("deleted_file"):
            return "deleted"
        if change.get("renamed_file"):
            return "renamed"
        return "modified"
