from pathlib import Path


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/update-winget.yml"


def test_winget_update_follows_successful_release_workflow() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_run:" in workflow
    assert "Publish Windows installer" in workflow
    assert "github.event.workflow_run.conclusion == 'success'" in workflow


def test_winget_update_requires_explicit_activation_and_secret() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "vars.WINGET_ENABLED == 'true'" in workflow
    assert "secrets.WINGET_PAT" in workflow
    assert "if (-not $env:WINGET_PAT)" in workflow


def test_winget_update_uses_published_versioned_installer() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "gh release view" in workflow
    assert "$release.isDraft -or $release.isPrerelease" in workflow
    assert 'Simple-PDF-Setup-$tag-x64.exe' in workflow
    assert "SABL.SimplePDF --version $env:VERSION --urls $env:INSTALLER_URL" in workflow
    assert "--submit --token $env:WINGET_PAT" in workflow


def test_winget_update_has_manual_retry_path() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow
    assert "REQUESTED_TAG:" in workflow
    assert "cancel-in-progress: false" in workflow
