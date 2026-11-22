import os
import sys

from pr_automation import GitHub, git


def target_prs(api: GitHub, event_name: str, ref_name: str, number: str) -> list[dict]:
    if event_name == "push" and ref_name == "master":
        return []
    if event_name == "workflow_dispatch" and ref_name == "master":
        return []
    if event_name == "pull_request":
        return [api.pull_request(int(number))]
    return [
        pr for pr in api.pull_requests("open")
        if pr["head"]["ref"] == ref_name
        and pr["head"]["repo"]["full_name"] == api.repository
    ]


def check_pr(pr: dict) -> None:
    number = pr["number"]
    base_ref = pr["base"]["ref"]
    git("fetch", "--no-tags", "origin", f"+refs/heads/{base_ref}:refs/remotes/origin/ci-base")
    git("fetch", "--no-tags", "origin", f"+refs/pull/{number}/head:refs/remotes/origin/ci-head")
    base_sha = git("rev-parse", "refs/remotes/origin/ci-base").stdout.strip()
    head_sha = git("rev-parse", "refs/remotes/origin/ci-head").stdout.strip()
    if base_sha != pr["base"]["sha"] or head_sha != pr["head"]["sha"]:
        raise RuntimeError(f"PR #{number}: branch changed during merge check; rerun CI")
    check = git("merge-tree", "--write-tree", base_sha, head_sha, check=False)
    if check.returncode != 0:
        raise RuntimeError(
            f"PR #{number}: merge conflicts with {base_ref}; tests not started\n"
            f"{check.stdout}\n{check.stderr}"
        )
    print(f"PR #{number}: merge into {base_ref} is conflict-free")


def main() -> None:
    api = GitHub()
    event_name = os.environ["GITHUB_EVENT_NAME"]
    ref_name = os.environ["GITHUB_REF_NAME"]
    number = os.environ.get("PR_NUMBER", "")
    prs = target_prs(api, event_name, ref_name, number)
    if not prs and ref_name != "master":
        raise RuntimeError("Cannot identify an open PR for this branch; tests not started")
    for pr in prs:
        if pr["state"] != "open":
            raise RuntimeError(f"PR #{pr['number']} is not open")
        check_pr(pr)
    print("Merge gate passed")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
