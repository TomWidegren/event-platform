
"""
Git persistence for the Event Platform floorball match registry.

This module persists owner-specific registry changes through Git.

It uses floorball_registry_merge.merge_registry_changes to
preserve unrelated matches and enforce field ownership.

The implementation:
- Fetches the latest remote main branch.
- Applies changes to the latest registry.
- Commits and pushes the merged result.
- Retries non-fast-forward push conflicts.
- Never intentionally replaces remote state with a stale copy.

This module does not:
- Call iBIS or other external APIs.
- Send notifications.
- Modify state.json.
- Run automatically without being explicitly called.

Tests use temporary local Git repositories.
"""

import json
import subprocess
from pathlib import Path

from floorball_registry_merge import merge_registry_changes


REGISTRY_FILE = "match_registry.json"
DEFAULT_BRANCH = "main"
MAX_ATTEMPTS = 3


def _git(repo_path, *args, check=True):
    """
    Run a Git command in the specified repository.
    """
    result = subprocess.run(
        ["git", *args],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=False,
    )

    if check and result.returncode != 0:
        raise RuntimeError(
            f"Git command failed: {' '.join(args)}\n"
            f"{result.stderr.strip()}"
        )

    return result


def _read_registry(repo_path):
    """
    Read the registry from the working tree.
    """
    path = Path(repo_path) / REGISTRY_FILE

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _write_registry(repo_path, registry):
    """
    Write the registry to the working tree.
    """
    path = Path(repo_path) / REGISTRY_FILE

    path.write_text(
        json.dumps(
            registry,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )


def persist_registry_changes(
    repo_path,
    changes,
    owner,
    max_attempts=MAX_ATTEMPTS,
):
    """
    Persist owner-specific registry changes safely through Git.

    Args:
        repo_path:
            Path to an existing Git working repository.

        changes:
            MatchID-keyed field changes.

        owner:
            "discovery" or "live".

        max_attempts:
            Maximum number of fetch/merge/push attempts.

    Returns:
        True if changes were successfully persisted.
        False if no actual registry change was necessary.

    Raises:
        ValueError:
            Invalid input or unauthorized field updates.

        RuntimeError:
            Git failure or exhausted retry attempts.

    Important:
        This function assumes that the working repository is
        dedicated to the persistence operation and does not
        contain unrelated uncommitted changes.
    """

    repo_path = Path(repo_path)

    if not repo_path.is_dir():
        raise ValueError("Repository path does not exist")

    if not isinstance(max_attempts, int) or max_attempts < 1:
        raise ValueError("max_attempts must be a positive integer")

    if not isinstance(changes, dict):
        raise TypeError("Changes must be a dictionary")

    if owner not in ("discovery", "live"):
        raise ValueError("Invalid registry owner")

    for attempt in range(1, max_attempts + 1):
        print(
            f"Registry persistence attempt "
            f"{attempt}/{max_attempts}"
        )

        # Obtain the latest remote branch state.
        _git(
            repo_path,
            "fetch",
            "origin",
            DEFAULT_BRANCH,
        )

        # Reset the dedicated working tree to the latest
        # remote state before applying any registry changes.
        _git(
            repo_path,
            "reset",
            "--hard",
            f"origin/{DEFAULT_BRANCH}",
        )

        current_registry = _read_registry(repo_path)

        updated_registry = merge_registry_changes(
            current_registry,
            changes,
            owner,
        )

        if updated_registry == current_registry:
            print("No registry changes required")
            return False

        _write_registry(
            repo_path,
            updated_registry,
        )

        _git(
            repo_path,
            "add",
            REGISTRY_FILE,
        )

        _git(
            repo_path,
            "commit",
            "-m",
            f"Update floorball registry ({owner})",
        )

        push_result = _git(
            repo_path,
            "push",
            "origin",
            f"HEAD:refs/heads/{DEFAULT_BRANCH}",
            check=False,
        )

        if push_result.returncode == 0:
            print("Registry changes persisted successfully")
            return True

        # A failed push may be caused by a concurrent update.
        # Fetch the latest state and retry the field-based merge.
        if attempt < max_attempts:
            print(
                "Git push failed; refreshing registry "
                "and retrying"
            )
            continue

        raise RuntimeError(
            "Unable to persist registry changes after "
            f"{max_attempts} attempts.\n"
            f"{push_result.stderr.strip()}"
        )

    raise RuntimeError("Registry persistence failed")
