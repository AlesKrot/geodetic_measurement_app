# Geodetic Measurement App

Desktop Python application for geodetic measurement analysis, error estimation, and correction reporting.

## Features planned in this scaffold

- PySide6 window with tabs:
	- Obliczenie kolimacji
	- Obliczenie inklinacji
	- Obliczenie Ng0
	- Obliczenie poprawki atmosferycznej
	- Wczytanie pliku tekstowego
	- Obliczenie różnicy łuk-cięciwa
	- Connection
	- Export
- Bluetooth-ready connection service with a mock transport first implementation
- Calculation engine using pandas for tabular results
- CSV, JSON, and PDF export
- Test structure for unit and integration checks

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Run

```bash
./run_app.sh
```

Or:

```bash
./scripts/run_app.sh
```

## Test

```bash
./run_tests.sh
```

Or:

```bash
./scripts/run_tests.sh
```

## Windows .exe build from a remote host (RDP)

This project can be packaged into a Windows executable on a remote Windows machine accessed via RDP.

### What is needed on a clean Windows machine

1. Windows 10/11 x64 with RDP access
2. Git installed
3. Python 3.11 (x64) installed and available in PATH
4. Internet access to download Python dependencies
5. Optional but recommended: Microsoft Visual C++ Redistributable (2015-2022)

### One-time setup on the remote host

Clone the repository:

```powershell
git clone <YOUR_REPO_URL>
cd <REPO_FOLDER>
```

### Build executable

Run the provided script:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\build_exe.ps1
```

Or with CMD:

```bat
scripts\windows\build_exe.bat
```

By default, the script:

1. Creates a clean virtual environment in `.venv-win`
2. Installs dependencies from `requirements.txt`
3. Installs the local package in editable mode
4. Installs PyInstaller
5. Runs tests
6. Builds `dist\\geodetic-app.exe`

To skip tests during build:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\build_exe.ps1 -SkipTests
```

### Output

The executable is created at:

`dist\\geodetic-app.exe`

### Notes

1. Build on Windows for Windows to avoid cross-platform packaging issues.
2. If antivirus flags one-file executables, consider a custom PyInstaller configuration later (`--onedir`).
