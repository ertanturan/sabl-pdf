import os
from pathlib import Path
import subprocess

from sabl_pdf.services.updates import parse_version


UPDATE_SCRIPT = r"""
param(
    [Parameter(Mandatory=$true)][string]$Installer,
    [Parameter(Mandatory=$true)][string]$AppPath,
    [Parameter(Mandatory=$true)][int]$ParentId,
    [Parameter(Mandatory=$true)][string]$ExpectedVersion
)
$ErrorActionPreference = 'Stop'
$log = Join-Path (Split-Path -Parent $Installer) 'install-update.log'
$completed = $false

function Test-AppRunning {
    $running = @(Get-Process -Name 'Simple PDF' -ErrorAction SilentlyContinue |
        Where-Object { $_.Path -ieq $AppPath })
    return $running.Count -gt 0
}

try {
    Wait-Process -Id $ParentId -ErrorAction SilentlyContinue
    $deadline = (Get-Date).AddSeconds(30)
    while (Test-AppRunning) {
        if ((Get-Date) -ge $deadline) {
            throw 'Close all Simple PDF windows before installing the update.'
        }
        Start-Sleep -Milliseconds 500
    }
    $directory = Split-Path -Parent $AppPath
    $setup = Start-Process -FilePath $Installer -ArgumentList @(
        '/SILENT', '/SP-', '/NORESTART', '/NOCLOSEAPPLICATIONS',
        '/NORESTARTAPPLICATIONS', ('/DIR="' + $directory + '"'),
        ('/LOG="' + $log + '"')
    ) -Wait -PassThru
    if ($setup.ExitCode -ne 0) {
        throw "Installer did not complete (exit code $($setup.ExitCode))."
    }
    if (-not (Test-Path -LiteralPath $AppPath -PathType Leaf)) {
        throw 'The installed Simple PDF executable is missing.'
    }
    $key = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{B0B635E2-0CB9-4FA1-BF4C-7BF92A2F1D94}_is1'
    $installed = Get-ItemProperty -LiteralPath $key -ErrorAction SilentlyContinue
    if ([string]$installed.DisplayVersion -ne $ExpectedVersion) {
        throw "Installer exited successfully, but Simple PDF v$ExpectedVersion was not installed."
    }
    Start-Process -FilePath $AppPath
    $completed = $true
} catch {
    $message = $_.Exception.Message
    if ((Test-Path -LiteralPath $AppPath -PathType Leaf) -and -not (Test-AppRunning)) {
        try {
            Start-Process -FilePath $AppPath
        } catch {
            $message += " Could not reopen Simple PDF: $($_.Exception.Message)"
        }
    }
    $details = @(
        $message, '', 'The update was not confirmed. Your installer is retained for retry.',
        "Installer: $Installer", "Installation log: $log"
    ) -join [Environment]::NewLine
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show(
        $details, 'Simple PDF update failed'
    ) | Out-Null
} finally {
    if ($completed) {
        Remove-Item -LiteralPath $Installer -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $log -Force -ErrorAction SilentlyContinue
    }
    Remove-Item -LiteralPath $PSCommandPath -Force -ErrorAction SilentlyContinue
}
"""


def launch_verified_installer(
    installer: Path, app_path: Path, parent_pid: int, expected_version: str
) -> None:
    parse_version(f"v{expected_version}")
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
                "-ParentId", str(parent_pid), "-ExpectedVersion", expected_version,
            ],
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except OSError:
        script.unlink(missing_ok=True)
        raise
