from pathlib import Path
import subprocess
from unittest.mock import Mock

import pytest

from check_pr_merge import target_prs
from pr_automation import mergeable, order_pulls
from rebase_prs import merged_branches, rebase_head, same_repository_prs


@pytest.fixture
def root_pr() -> dict:
    return {
        "number": 1,
        "base": {"ref": "master", "sha": "initial"},
        "head": {"ref": "feature/root", "sha": "root", "repo": {"full_name": "owner/repo"}},
        "merged_at": None,
    }


@pytest.fixture
def child_pr() -> dict:
    return {
        "number": 2,
        "base": {"ref": "feature/root", "sha": "root"},
        "head": {"ref": "feature/child", "sha": "child", "repo": {"full_name": "owner/repo"}},
        "merged_at": None,
    }


def test_parent_rebased_before_stacked_child(root_pr: dict, child_pr: dict) -> None:
    unordered = [child_pr, root_pr]

    ordered = order_pulls(unordered)

    assert ordered == [root_pr, child_pr]


def test_circular_pr_stack_is_rejected(root_pr: dict, child_pr: dict) -> None:
    root_pr["base"]["ref"] = "feature/child"

    with pytest.raises(ValueError, match="Circular"):
        order_pulls([root_pr, child_pr])


def test_rebase_only_targets_same_repository(root_pr: dict, child_pr: dict) -> None:
    child_pr["head"]["repo"]["full_name"] = "someone/fork"

    result = same_repository_prs([root_pr, child_pr], "owner/repo")

    assert result == [root_pr]


def test_merged_base_keeps_original_sha(root_pr: dict) -> None:
    root_pr["merged_at"] = "2026-11-22T12:00:00Z"

    result = merged_branches([root_pr], "owner/repo")

    assert result == {"feature/root": "root"}


def test_unmerged_base_is_not_considered_complete(root_pr: dict) -> None:
    result = merged_branches([root_pr], "owner/repo")

    assert result == {}


def test_manual_ci_dispatch_selects_matching_pr(root_pr: dict, child_pr: dict) -> None:
    api = Mock()
    api.repository = "owner/repo"
    api.pull_requests.return_value = [root_pr, child_pr]

    result = target_prs(api, "workflow_dispatch", "feature/child", "")

    assert result == [child_pr]
    api.pull_requests.assert_called_once_with("open")


def test_pull_request_event_checks_its_pr(root_pr: dict) -> None:
    api = Mock()
    api.pull_request.return_value = root_pr

    result = target_prs(api, "pull_request", "1/merge", "1")

    assert result == [root_pr]
    api.pull_request.assert_called_once_with(1)


def test_ci_on_master_requires_no_pr_lookup() -> None:
    api = Mock()

    result = target_prs(api, "push", "master", "")

    assert result == []
    api.pull_request.assert_not_called()
    api.pull_requests.assert_not_called()


def test_manual_ci_without_matching_pr_is_blocked(root_pr: dict) -> None:
    api = Mock()
    api.repository = "owner/repo"
    api.pull_requests.return_value = [root_pr]

    result = target_prs(api, "workflow_dispatch", "feature/unknown", "")

    assert result == []


def run_git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def git_repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    run_git(tmp_path, "init", "-q", "-b", "master")
    run_git(tmp_path, "config", "user.name", "Test")
    run_git(tmp_path, "config", "user.email", "test@example.invalid")
    (tmp_path / "shared.txt").write_text("original\n", encoding="utf-8")
    run_git(tmp_path, "add", ".")
    run_git(tmp_path, "commit", "-qm", "initial")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_merge_gate_allows_separate_changes(git_repository: Path) -> None:
    run_git(git_repository, "switch", "-qc", "topic")
    (git_repository / "topic.txt").write_text("topic\n", encoding="utf-8")
    run_git(git_repository, "add", ".")
    run_git(git_repository, "commit", "-qm", "topic")
    head_sha = run_git(git_repository, "rev-parse", "HEAD")
    run_git(git_repository, "switch", "-q", "master")
    (git_repository / "master.txt").write_text("master\n", encoding="utf-8")
    run_git(git_repository, "add", ".")
    run_git(git_repository, "commit", "-qm", "master")
    base_sha = run_git(git_repository, "rev-parse", "HEAD")

    result = mergeable(base_sha, head_sha)

    assert result is True


def test_merge_gate_rejects_real_conflicts(git_repository: Path) -> None:
    run_git(git_repository, "switch", "-qc", "topic")
    (git_repository / "shared.txt").write_text("topic\n", encoding="utf-8")
    run_git(git_repository, "commit", "-qam", "topic")
    head_sha = run_git(git_repository, "rev-parse", "HEAD")
    run_git(git_repository, "switch", "-q", "master")
    (git_repository / "shared.txt").write_text("master\n", encoding="utf-8")
    run_git(git_repository, "commit", "-qam", "master")
    base_sha = run_git(git_repository, "rev-parse", "HEAD")

    result = mergeable(base_sha, head_sha)

    assert result is False


def test_ci_tests_wait_for_merge_gate() -> None:
    workflow_path = Path(__file__).resolve().parents[1] / ".github/workflows/ci.yml"

    content = workflow_path.read_text(encoding="utf-8")

    assert "  merge-check:" in content
    assert "    needs: merge-check" in content
    assert "    if: needs.merge-check.result == 'success'" in content
    assert "python scripts/check_pr_merge.py" in content
    assert content.index("  merge-check:") < content.index("  unit-tests:")


def test_rebase_is_only_automatic_after_master_changes() -> None:
    workflow_path = Path(__file__).resolve().parents[1] / ".github/workflows/rebase-prs.yml"

    content = workflow_path.read_text(encoding="utf-8")

    assert "branches: [master]" in content
    assert "cancel-in-progress: false" in content
    assert "python scripts/rebase_prs.py" in content
    assert "actions: write" in content
    assert "pull-requests: write" in content


def test_rebase_preserves_child_changes_after_parent_moves(git_repository: Path) -> None:
    initial_sha = run_git(git_repository, "rev-parse", "HEAD")
    run_git(git_repository, "switch", "-qc", "feature/root")
    (git_repository / "root.txt").write_text("root\n", encoding="utf-8")
    run_git(git_repository, "add", ".")
    run_git(git_repository, "commit", "-qm", "root")
    original_root = run_git(git_repository, "rev-parse", "HEAD")
    run_git(git_repository, "switch", "-qc", "feature/child")
    (git_repository / "child.txt").write_text("child\n", encoding="utf-8")
    run_git(git_repository, "add", ".")
    run_git(git_repository, "commit", "-qm", "child")
    original_child = run_git(git_repository, "rev-parse", "HEAD")
    run_git(git_repository, "switch", "-q", "master")
    (git_repository / "master.txt").write_text("master\n", encoding="utf-8")
    run_git(git_repository, "add", ".")
    run_git(git_repository, "commit", "-qm", "master")
    updated_master = run_git(git_repository, "rev-parse", "HEAD")

    updated_root = rebase_head(original_root, initial_sha, updated_master)
    updated_child = rebase_head(original_child, original_root, updated_root)

    assert run_git(git_repository, "merge-base", updated_root, updated_child) == updated_root
    assert run_git(git_repository, "show", f"{updated_child}:root.txt") == "root"
    assert run_git(git_repository, "show", f"{updated_child}:child.txt") == "child"
    assert run_git(git_repository, "show", f"{updated_child}:master.txt") == "master"


def test_rebase_conflicts_abort_without_changing_original_branch(git_repository: Path) -> None:
    original_master = run_git(git_repository, "rev-parse", "HEAD")
    run_git(git_repository, "switch", "-qc", "feature/conflicting")
    (git_repository / "shared.txt").write_text("feature\n", encoding="utf-8")
    run_git(git_repository, "commit", "-qam", "feature")
    old_head = run_git(git_repository, "rev-parse", "HEAD")
    run_git(git_repository, "switch", "-q", "master")
    (git_repository / "shared.txt").write_text("master\n", encoding="utf-8")
    run_git(git_repository, "commit", "-qam", "master")
    updated_master = run_git(git_repository, "rev-parse", "HEAD")

    with pytest.raises(RuntimeError, match="Rebase conflict"):
        rebase_head(old_head, original_master, updated_master)

    assert run_git(git_repository, "rev-parse", "HEAD") == old_head
    assert run_git(git_repository, "rev-parse", "feature/conflicting") == old_head


def test_reusing_a_head_branch_for_multiple_prs_is_blocked(root_pr: dict) -> None:
    second = {
        "number": 3,
        "base": {"ref": "master"},
        "head": {"ref": "feature/root"},
    }

    with pytest.raises(ValueError, match="same head branch"):
        order_pulls([root_pr, second])


def test_ci_docs_only_skips_expensive_steps_without_skipping_required_check() -> None:
    workflow_path = Path(__file__).resolve().parents[1] / ".github/workflows/ci.yml"

    workflow = workflow_path.read_text(encoding="utf-8")

    assert "github.rest.pulls.listFiles" in workflow
    assert "github.rest.repos.compareCommitsWithBasehead" in workflow
    assert "file.previous_filename" in workflow
    assert "paths.every(path =>" in workflow
    assert "core.setOutput('run_tests', String(!docsOnly))" in workflow
    assert "runs-on: ${{ needs.merge-check.outputs.run_tests == 'false' && 'ubuntu-latest' || 'windows-latest' }}" in workflow
    assert "if: needs.merge-check.outputs.run_tests == 'false'" in workflow
    assert workflow.count("if: needs.merge-check.outputs.run_tests == 'true'") == 8
    assert "  unit-tests:" in workflow
