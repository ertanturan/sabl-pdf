import os
from pathlib import Path
import subprocess


UPDATE_SCRIPT = r"""
param(
    [Parameter(Mandatory=$true)][string]$Installer,
    [Parameter(Mandatory=$true)][string]$AppPath,
    [Parameter(Mandatory=$true)][int]$ParentId
)
$ErrorActionPreference = 'Stop'
try {
    Wait-Process -Id $ParentId -ErrorAction SilentlyContinue
    $setup = Start-Process -FilePath $Installer -ArgumentList @(
        '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART',
        '/CLOSEAPPLICATIONS', '/NORESTARTAPPLICATIONS'
    ) -Wait -PassThru
    if ($setup.ExitCode -ne 0) {
        throw "Installer failed with exit code $($setup.ExitCode)"
    }
    Start-Process -FilePath $AppPath
} catch {
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show(
        $_.Exception.Message, 'Simple PDF update failed'
    ) | Out-Null
} finally {
    Remove-Item -LiteralPath $Installer -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $PSCommandPath -Force -ErrorAction SilentlyContinue
}
"""


def launch_verified_installer(installer: Path, app_path: Path, parent_pid: int) -> None:
    if not installer.is_file() or not app_path.is_file():
        raise FileNotFoundError("The verified installer or installed application is missing")
    script = installer.parent / "install-update.ps1"
    script.write_text(UPDATE_SCRIPT, encoding="utf-8")
    powershell = Path(os.environ.get("SystemRoot", r"C:\Windows")) / (
        "System32/WindowsPowerShell/v1.0/powershell.exe"
    )
    try:
        subprocess.Popen(
            [
                str(powershell), "-NoProfile", "-NonInteractive",
                "-ExecutionPolicy", "Bypass", "-File", str(script),
                "-Installer", str(installer), "-AppPath", str(app_path),
                "-ParentId", str(parent_pid),
            ],
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except OSError:
        script.unlink(missing_ok=True)
        raise
