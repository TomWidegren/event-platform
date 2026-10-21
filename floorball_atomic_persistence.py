
"""
Coordinated Git persistence for completed floorball matches.

Persists the final monitoring snapshot in state.json and
the completed match status in match_registry.json together.

Both files are included in the same Git commit.

The module:
- Fetches the latest remote main branch.
- Merges the final snapshot into the latest state.
- Updates the relevant registry entry.
- Commits both files together.
- Retries rejected pushes.
- Preserves unrelated Watches and matches.

This module does not:
- Fetch external match data.
- Send notifications.
- Modify production workflows.
- Run automatically.

IMPORTANT:
The function uses git reset --hard and must only be called
from a dedicated, disposable Git working directory.

The implementation has not yet been verified.
"""

import json
import subprocess
from pathlib import Path

from floorball_registry_merge import merge_registry_changes


DEFAULT_BRANCH = "main"
MAX_ATTEMPTS = 3

STATE_FILE = "state.json"
REGISTRY_FILE = "match_registry.json"


def _git(repo_path, *args, check=True):
    """
    Execute a Git command in the supplied repository.
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


def _read_json(repo_path, filename):
    path = Path(repo_path) / filename

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _write_json(repo_path, filename, data):
    path = Path(repo_path) / filename

    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )


def persist_match_completion(
    repo_path,
    match_id,
    watch_id,
    final_fields,
    max_attempts=MAX_ATTEMPTS,
):
    """
    Persist a completed floorball match in one Git commit.

    Args:
        repo_path:
            Dedicated local Git working directory.

        match_id:
            iBIS MatchID.

        watch_id:
            Stable Event Platform Watch ID.

        final_fields:
            Normalized final match snapshot.

        max_attempts:
            Maximum number of persistence attempts.

    Returns:
        True if a new commit was successfully pushed.
        False if the same final state was already persisted.

    Raises:
        ValueError:
            Invalid match identity or final snapshot.

        KeyError:
            Match missing from the registry.

        RuntimeError:
            Git operation failed or persistence retries
            were exhausted.

    This function does not send the final-result
    notification. Notification coordination remains
    a separate design concern.
    """

    repo_path = Path(repo_path)

    if not repo_path.is_dir():
        raise ValueError("Repository path does not exist")

    if not isinstance(max_attempts, int) or max_attempts < 1:
        raise ValueError(
            "max_attempts must be a positive integer"
        )

    if not isinstance(match_id, int) or match_id <= 0:
        raise ValueError("Invalid MatchID")

    expected_watch_id = f"floorball-match-{match_id}"

    if watch_id != expected_watch_id:
        raise ValueError(
            "Watch ID does not match MatchID"
        )

    if not isinstance(final_fields, dict):
        raise ValueError(
            "Final snapshot must be a dictionary"
        )

    if final_fields.get("match_id") != match_id:
        raise ValueError(
            "Final snapshot MatchID mismatch"
        )

    if final_fields.get("has_final_result") is not True:
        raise ValueError(
            "Snapshot does not contain a final result"
        )

    for attempt in range(1, max_attempts + 1):
        print(
            f"Atomic persistence attempt "
            f"{attempt}/{max_attempts}"
        )

        # Start each attempt from the latest remote state.
        _git(
            repo_path,
            "fetch",
            "origin",
            DEFAULT_BRANCH,
        )

        _git(
            repo_path,
            "reset",
            "--hard",
            f"origin/{DEFAULT_BRANCH}",
        )

        state = _read_json(
            repo_path,
            STATE_FILE,
        )

        registry = _read_json(
            repo_path,
            REGISTRY_FILE,
        )

        if not isinstance(state, dict):
            raise ValueError("Invalid monitoring state")

        if not isinstance(registry, dict):
            raise ValueError("Invalid match registry")

        match_key = str(match_id)

        if match_key not in registry.get("matches", {}):
            raise KeyError(
                f"Match {match_id} missing from registry"
            )

        # Preserve all unrelated Watch state.
        updated_state = dict(state)

        from watcher import snapshot_for

        updated_state[watch_id] = {
            "snapshot": snapshot_for(final_fields),
            "fields": final_fields,
        }

        # Update only the Live-owned lifecycle field.
        updated_registry = merge_registry_changes(
            registry,
            {
                match_key: {
                    "monitoring_status": "completed",
                }
            },
            owner="live",
        )

        if (
            updated_state == state
            and updated_registry == registry
        ):
            print("Final match state already persisted")
            return False

        _write_json(
            repo_path,
            STATE_FILE,
            updated_state,
        )

        _write_json(
            repo_path,
            REGISTRY_FILE,
            updated_registry,
        )

        _git(
            repo_path,
            "add",
            STATE_FILE,
            REGISTRY_FILE,
        )

        _git(
            repo_path,
            "commit",
            "-m",
            f"Complete floorball match {match_id}",
        )

        push_result = _git(
            repo_path,
            "push",
            "origin",
            f"HEAD:refs/heads/{DEFAULT_BRANCH}",
            check=False,
        )

        if push_result.returncode == 0:
            print(
                "Final snapshot and registry completion "
                "persisted successfully"
            )
            return True

        if attempt < max_attempts:
            print(
                "Git push failed; refreshing state "
                "and retrying"
            )
            continue

        raise RuntimeError(
            "Unable to persist completed match after "
            f"{max_attempts} attempts.\n"
            f"{push_result.stderr.strip()}"
        )

    raise RuntimeError(
        "Atomic match persistence failed"
    )
