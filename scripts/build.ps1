$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
python -m pip install -e '.[dev]'
python -m pytest -q
python -m PyInstaller --noconfirm --clean --windowed --onedir --name 'SABL PDF' --paths src src/sabl_pdf/main.py
if (Test-Path 'installer/tessdata/eng.traineddata') {
    Copy-Item -Recurse -Force installer/tessdata 'dist/SABL PDF/tessdata'
}
$iscc = Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'
if (-not (Test-Path $iscc)) {
    throw 'Install Inno Setup 6 to create the installer.'
}
& $iscc installer/SABL-PDF.iss
