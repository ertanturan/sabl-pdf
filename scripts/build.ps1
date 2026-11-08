$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'

function Find-InnoSetup {
    $command = Get-Command 'ISCC.exe' -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $folders = @(
        [Environment]::GetFolderPath('ProgramFilesX86')
        [Environment]::GetFolderPath('ProgramFiles')
    )

    foreach ($folder in $folders) {
        if (-not $folder) {
            continue
        }
        $candidate = Join-Path $folder 'Inno Setup 6\ISCC.exe'
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    throw 'Inno Setup 6 is required for builds: https://jrsoftware.org/isinfo.php'
}

$iscc = Find-InnoSetup
& (Join-Path $PSScriptRoot 'test.ps1')

Push-Location $projectRoot
try {
    & $pythonPath -m PyInstaller --noconfirm --clean --windowed --onedir --name 'SABL PDF' --paths src src/sabl_pdf/main.py
    if ($LASTEXITCODE -ne 0) {
        throw 'PyInstaller failed.'
    }

    if (Test-Path 'installer/tessdata/eng.traineddata') {
        Copy-Item -Recurse -Force 'installer/tessdata' 'dist/SABL PDF/tessdata'
    }

    & $iscc 'installer/SABL-PDF.iss'
    if ($LASTEXITCODE -ne 0) {
        throw 'Inno Setup failed.'
    }
} finally {
    Pop-Location
}
