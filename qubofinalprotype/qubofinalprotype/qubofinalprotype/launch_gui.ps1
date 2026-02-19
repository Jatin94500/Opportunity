$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$rootDir = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
$appPy = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$rootPy = Join-Path $rootDir ".venv\Scripts\python.exe"

function Test-PyQt5([string]$pythonPath) {
    if (-not (Test-Path $pythonPath)) { return $false }
    & $pythonPath -c "import PyQt5" *> $null
    return $LASTEXITCODE -eq 0
}

if (Test-PyQt5 $appPy) {
    $python = $appPy
} elseif (Test-PyQt5 $rootPy) {
    $python = $rootPy
} else {
    $python = "python"
}

& $python "run_gui.py" @args
