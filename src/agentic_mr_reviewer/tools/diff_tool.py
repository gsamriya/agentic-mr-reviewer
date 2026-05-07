from __future__ import annotations

from typing import List

from ..models import FileChange


def summarise_changes(changes: List[FileChange]) -> dict:
    """
    Compute simple stats over a list of FileChange objects.
    """
    num_files = len(changes)
    total_additions = sum(c.additions for c in changes)
    total_deletions = sum(c.deletions for c in changes)
    by_type: dict[str, int] = {}
    for ch in changes:
        by_type[ch.change_type] = by_type.get(ch.change_type, 0) + 1

    return {
        "num_files": num_files,
        "total_additions": total_additions,
        "total_deletions": total_deletions,
        "by_type": by_type,
    }
