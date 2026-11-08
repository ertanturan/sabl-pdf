param([switch]$SetupOnly)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$venvPath = Join-Path $projectRoot '.venv'
$pythonPath = Join-Path $venvPath 'Scripts\python.exe'

function Initialize-Python {
    if (Test-Path -LiteralPath $pythonPath) {
        return
    }

    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv $venvPath
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv $venvPath
    } else {
        throw 'Python 3.12 or newer is required. Install Python and try again.'
    }

    if ($LASTEXITCODE -ne 0) {
        throw 'Could not create the Python virtual environment.'
    }
}

function Invoke-Python {
    param([string[]]$Arguments)

    & $pythonPath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed: $($Arguments -join ' ')"
    }
}

Initialize-Python
Invoke-Python -Arguments @('-c', 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)')

Push-Location $projectRoot
try {
    Invoke-Python -Arguments @('-m', 'pip', 'install', '-e', '.[dev]')
} finally {
    Pop-Location
}

if (-not $SetupOnly) {
    Invoke-Python -Arguments @('-m', 'sabl_pdf.main')
}
