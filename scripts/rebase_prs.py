import sys
import subprocess

from pr_automation import GitHub, git, merge_base, mergeable, order_pulls


def same_repository_prs(prs: list[dict], repository: str) -> list[dict]:
    return [pr for pr in prs if pr["head"]["repo"]["full_name"] == repository]


def merged_branches(prs: list[dict], repository: str) -> dict[str, str]:
    return {
        pr["head"]["ref"]: pr["head"]["sha"] for pr in prs
        if pr["merged_at"] and pr["head"]["repo"]["full_name"] == repository
    }


def rebase_head(head_sha: str, previous_base: str, next_base: str) -> str:
    if git("merge-base", "--is-ancestor", next_base, head_sha, check=False).returncode == 0:
        return head_sha
    fork = merge_base(previous_base, head_sha)
    git("switch", "--detach", head_sha)
    try:
        git("rebase", "--onto", next_base, fork)
    except subprocess.CalledProcessError as error:
        git("rebase", "--abort", check=False)
        raise RuntimeError(f"Rebase conflict: {error.stdout} {error.stderr}") from error
    updated = git("rev-parse", "HEAD").stdout.strip()
    if not mergeable(next_base, updated):
        raise RuntimeError("Rebased branch still has merge conflicts")
    return updated


def update_pr(api: GitHub, pr: dict, previous_base: str, next_base: str, retarget: bool) -> str:
    head_sha = pr["head"]["sha"]
    head_ref = pr["head"]["ref"]
    if git("rev-parse", f"refs/remotes/origin/{head_ref}").stdout.strip() != head_sha:
        raise RuntimeError("Branch head changed while preparing rebase")
    next_sha = rebase_head(head_sha, previous_base, next_base)
    if next_sha != head_sha:
        git("push", f"--force-with-lease=refs/heads/{head_ref}:{head_sha}",
            "origin", f"{next_sha}:refs/heads/{head_ref}")
    if retarget:
        api.retarget(pr["number"], "master")
    if next_sha != head_sha or retarget:
        api.dispatch_ci(head_ref)
    return next_sha


def main() -> None:
    api = GitHub()
    git("config", "user.name", "github-actions[bot]")
    git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    git("fetch", "--no-tags", "origin", "+refs/heads/*:refs/remotes/origin/*")
    pulls = same_repository_prs(api.pull_requests("open"), api.repository)
    historical = merged_branches(api.pull_requests("closed"), api.repository)
    by_head = {pr["head"]["ref"]: pr for pr in pulls}
    master_sha = git("rev-parse", "refs/remotes/origin/master").stdout.strip()
    updated = {}
    failures = []
    for pr in order_pulls(pulls):
        base_ref = pr["base"]["ref"]
        head_ref = pr["head"]["ref"]
        parent = by_head.get(base_ref)
        if parent and base_ref not in updated:
            failures.append(f"PR #{pr['number']}: parent {base_ref} could not be rebased")
            continue
        if parent:
            next_base = updated[base_ref]
            previous_base = parent["head"]["sha"]
            retarget = False
        elif base_ref == "master":
            next_base = master_sha
            previous_base = pr["base"]["sha"]
            retarget = False
        elif historical.get(base_ref) == pr["base"]["sha"]:
            next_base = master_sha
            previous_base = pr["base"]["sha"]
            retarget = True
        else:
            failures.append(f"PR #{pr['number']}: unmanaged base {base_ref}")
            continue
        try:
            updated[head_ref] = update_pr(api, pr, previous_base, next_base, retarget)
            print(f"PR #{pr['number']}: verified {head_ref}")
        except Exception as error:
            failures.append(f"PR #{pr['number']}: {error}")
    for failure in failures:
        print(failure, file=sys.stderr)
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
