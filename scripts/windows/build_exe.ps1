param(
    [string]$RepoPath = "",
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Get-RepoRoot {
    param([string]$ProvidedRepoPath)

    if ($ProvidedRepoPath -and (Test-Path -LiteralPath $ProvidedRepoPath)) {
        return (Resolve-Path -LiteralPath $ProvidedRepoPath).Path
    }

    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $root = Resolve-Path -LiteralPath (Join-Path $scriptDir "..\..")
    return $root.Path
}

function Resolve-PythonCommand {
    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) {
        try {
            & py -3.11 --version | Out-Null
            return @("py", "-3.11")
        }
        catch {
            throw "Python 3.11 is not available via the py launcher. Install Python 3.11 and rerun."
        }
    }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        return @("python", "")
    }

    throw "Python is not installed or not available in PATH. Install Python 3.11 first."
}

$repo = Get-RepoRoot -ProvidedRepoPath $RepoPath
Write-Host "Repository root: $repo"

$venvPath = Join-Path $repo ".venv-win"
$distExe = Join-Path $repo "dist\geodetic-app.exe"
$entrypoint = Join-Path $repo "src\geodetic_app\__main__.py"

if (-not (Test-Path -LiteralPath $entrypoint)) {
    throw "Entrypoint not found: $entrypoint"
}

$pyCommand = Resolve-PythonCommand

Write-Host "Creating virtual environment in $venvPath"
if (Test-Path -LiteralPath $venvPath) {
    Remove-Item -LiteralPath $venvPath -Recurse -Force
}

if ([string]::IsNullOrWhiteSpace($pyCommand[1])) {
    & $pyCommand[0] -m venv $venvPath
}
else {
    & $pyCommand[0] $pyCommand[1] -m venv $venvPath
}

$venvPython = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "Virtual environment Python executable not found: $venvPython"
}

Write-Host "Installing dependencies"
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $repo "requirements.txt")
& $venvPython -m pip install -e $repo
& $venvPython -m pip install pyinstaller

if (-not $SkipTests) {
    Write-Host "Running test suite"
    & $venvPython -m pytest
}

Write-Host "Building Windows executable via PyInstaller"
Push-Location $repo
try {
    & $venvPython -m PyInstaller --noconfirm --clean --windowed --name geodetic-app --paths "$repo\src" "$entrypoint"
}
finally {
    Pop-Location
}

if (-not (Test-Path -LiteralPath $distExe)) {
    throw "Build did not produce expected executable: $distExe"
}

Write-Host "Build complete"
Write-Host "Executable: $distExe"