$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$previousPlatform = [Environment]::GetEnvironmentVariable('QT_QPA_PLATFORM', 'Process')

function Invoke-Check {
    param([string[]]$Arguments)

    & $pythonPath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Check failed: python $($Arguments -join ' ')"
    }
}

& (Join-Path $PSScriptRoot 'run.ps1') -SetupOnly

Push-Location $projectRoot
try {
    $env:QT_QPA_PLATFORM = 'offscreen'
    Invoke-Check -Arguments @('-m', 'pytest', '-q')
    Invoke-Check -Arguments @('-m', 'compileall', '-q', 'src')
    Invoke-Check -Arguments @('-m', 'ruff', 'check', '.')
    Invoke-Check -Arguments @('-m', 'pyright')
} finally {
    [Environment]::SetEnvironmentVariable('QT_QPA_PLATFORM', $previousPlatform, 'Process')
    Pop-Location
}
