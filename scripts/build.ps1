param(
    [switch]$Major,
    [switch]$Secondary,
    [switch]$Minor,
    [switch]$NoVersionBump
)

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

$selected = @($Major.IsPresent, $Secondary.IsPresent, $Minor.IsPresent, $NoVersionBump.IsPresent) | Where-Object { $_ }
if ($selected.Count -gt 1) {
    throw 'Choose only one of -Major, -Secondary, -Minor or -NoVersionBump.'
}
if ($env:GITHUB_REF_TYPE -eq 'tag' -and -not $NoVersionBump) {
    throw 'Tagged release builds must use -NoVersionBump.'
}

$iscc = Find-InnoSetup
& (Join-Path $PSScriptRoot 'run.ps1') -SetupOnly

Push-Location $projectRoot
try {
    if ($NoVersionBump) {
        $versionArgs = @('scripts/versioning.py', 'check')
        if ($env:GITHUB_REF_TYPE -eq 'tag') {
            $versionArgs += @('--expected-tag', $env:GITHUB_REF_NAME)
        }
    } else {
        $part = 'minor'
        if ($Major) {
            $part = 'major'
        } elseif ($Secondary) {
            $part = 'secondary'
        }
        $versionArgs = @('scripts/versioning.py', 'bump', '--part', $part)
    }

    & $pythonPath @versionArgs
    if ($LASTEXITCODE -ne 0) {
        throw 'Version validation or increment failed.'
    }

    & (Join-Path $PSScriptRoot 'test.ps1')

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
