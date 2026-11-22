import json
import os
import subprocess
from urllib.request import Request, urlopen


class GitHub:
    def __init__(self) -> None:
        self.repository = os.environ["GITHUB_REPOSITORY"]
        self.token = os.environ["GITHUB_TOKEN"]

    def request(self, method: str, path: str, payload: dict | None = None):
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            f"https://api.github.com/repos/{self.repository}/{path}",
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
            },
        )
        with urlopen(request, timeout=30) as response:
            content = response.read()
        return json.loads(content) if content else None

    def pull_requests(self, state: str) -> list[dict]:
        result = []
        page = 1
        while True:
            batch = self.request("GET", f"pulls?state={state}&per_page=100&page={page}")
            result.extend(batch)
            if len(batch) != 100:
                return result
            page += 1

    def pull_request(self, number: int) -> dict:
        return self.request("GET", f"pulls/{number}")

    def retarget(self, number: int, branch: str) -> None:
        self.request("PATCH", f"pulls/{number}", {"base": branch})

    def dispatch_ci(self, branch: str) -> None:
        self.request("POST", "actions/workflows/ci.yml/dispatches", {"ref": branch})


def git(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments], check=check, text=True, capture_output=True
    )


def order_pulls(pulls: list[dict]) -> list[dict]:
    heads = {pr["head"]["ref"] for pr in pulls}
    if len(heads) != len(pulls):
        raise ValueError("Multiple pull requests use the same head branch")
    pending = list(pulls)
    ordered = []
    while pending:
        ready = [pr for pr in pending if pr["base"]["ref"] not in heads]
        if not ready:
            raise ValueError("Circular or self-referential pull request stack")
        ordered.extend(ready)
        pending = [pr for pr in pending if pr not in ready]
        heads.difference_update(pr["head"]["ref"] for pr in ready)
    return ordered


def mergeable(base_sha: str, head_sha: str) -> bool:
    return git("merge-tree", "--write-tree", base_sha, head_sha, check=False).returncode == 0


def merge_base(left_sha: str, right_sha: str) -> str:
    return git("merge-base", left_sha, right_sha).stdout.strip()
