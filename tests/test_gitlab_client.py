from agentic_mr_reviewer.gitlab_client import GitLabClient


def test_gitlab_client_has_base_url_and_token(monkeypatch):
    monkeypatch.setenv("GITLAB_URL", "https://gitlab.example.com")
    monkeypatch.setenv("GITLAB_TOKEN", "dummy")

    client = GitLabClient()
    assert client.base_url == "https://gitlab.example.com"
    assert client.token == "dummy"
