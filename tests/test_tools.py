from agentic_mr_reviewer.tools.diff_tool import summarise_changes
from agentic_mr_reviewer.models import FileChange


def test_summarise_changes_basic():
    changes = [
        FileChange(path="a.py", change_type="added", additions=10, deletions=0),
        FileChange(path="b.py", change_type="modified", additions=5, deletions=3),
    ]
    stats = summarise_changes(changes)
    assert stats["num_files"] == 2
    assert stats["total_additions"] == 15
    assert stats["total_deletions"] == 3
