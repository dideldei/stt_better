# install.ps1 - Idempotente Installation für STT-Diktat-Agent
# Windows 11, Python venv, requirements.lock.txt

param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# Schritt 1/5: Python-Version prüfen
Write-Host "[1/5] Prüfe Python-Version..." -ForegroundColor Cyan

try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "FEHLER: Python ist nicht installiert oder nicht im PATH." -ForegroundColor Red
        Write-Host "Bitte installieren Sie Python 3.11 oder höher manuell." -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "  Gefunden: $pythonVersion" -ForegroundColor Gray
    
    # Version parsen: "Python 3.11.x" oder höher
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        
        if ($major -ne 3) {
            Write-Host "FEHLER: Python 3.x erforderlich, gefunden: $pythonVersion" -ForegroundColor Red
            exit 1
        }
        
        if ($minor -lt 11) {
            Write-Host "FEHLER: Python >= 3.11 erforderlich, gefunden: $pythonVersion" -ForegroundColor Red
            exit 1
        }
        
        Write-Host "  OK: Python $major.$minor ist kompatibel" -ForegroundColor Green
    } else {
        Write-Host "FEHLER: Konnte Python-Version nicht parsen: $pythonVersion" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "FEHLER: Python-Version konnte nicht ermittelt werden: $_" -ForegroundColor Red
    exit 1
}

# Schritt 2/5: Projektkontext prüfen
Write-Host "[2/5] Prüfe Projektkontext..." -ForegroundColor Cyan

$scriptPath = $PSScriptRoot
$projectRoot = Split-Path -Parent $scriptPath

if (-not (Test-Path $projectRoot)) {
    Write-Host "FEHLER: Projektroot nicht gefunden: $projectRoot" -ForegroundColor Red
    exit 1
}

$requirementsLock = Join-Path $projectRoot "requirements.lock.txt"
if (-not (Test-Path $requirementsLock)) {
    Write-Host "FEHLER: requirements.lock.txt nicht gefunden: $requirementsLock" -ForegroundColor Red
    exit 1
}

Write-Host "  Projektroot: $projectRoot" -ForegroundColor Gray
Write-Host "  requirements.lock.txt: gefunden" -ForegroundColor Green

# Schritt 3/5: Virtual Environment verwalten
Write-Host "[3/5] Verwalte Virtual Environment..." -ForegroundColor Cyan

$venvPath = Join-Path $projectRoot ".venv"

if (Test-Path $venvPath) {
    if ($Force) {
        Write-Host "  -Force gesetzt: Lösche vorhandenes .venv..." -ForegroundColor Yellow
        Remove-Item -Path $venvPath -Recurse -Force
        Write-Host "  .venv gelöscht" -ForegroundColor Gray
    } else {
        Write-Host "  .venv existiert bereits, verwende vorhandenes" -ForegroundColor Gray
    }
}

if (-not (Test-Path $venvPath)) {
    Write-Host "  Erstelle .venv..." -ForegroundColor Gray
    python -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host "FEHLER: venv konnte nicht erstellt werden" -ForegroundColor Red
        exit 1
    }
    Write-Host "  .venv erstellt" -ForegroundColor Green
} else {
    Write-Host "  .venv vorhanden" -ForegroundColor Green
}

# Python-Pfad aus venv bestimmen (Windows)
$venvPython = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "FEHLER: venv-Python nicht gefunden: $venvPython" -ForegroundColor Red
    exit 1
}

# Schritt 4/5: pip installieren
Write-Host "[4/5] Installiere Abhängigkeiten..." -ForegroundColor Cyan

Write-Host "  Upgrade pip..." -ForegroundColor Gray
& $venvPython -m pip install --upgrade pip --quiet
# pip-Upgrade-Fehler ignorieren (nicht kritisch)
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Warnung: pip-Upgrade fehlgeschlagen, fahre fort..." -ForegroundColor Yellow
}

Write-Host "  Installiere aus requirements.lock.txt..." -ForegroundColor Gray
Write-Host "  (inkl. faster-whisper CPU-only, sounddevice, numpy)" -ForegroundColor Gray
& $venvPython -m pip install -r $requirementsLock
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: Installation aus requirements.lock.txt fehlgeschlagen" -ForegroundColor Red
    exit 1
}

Write-Host "  Abhängigkeiten installiert" -ForegroundColor Green

# Schritt 5/5: Verifikation
Write-Host "[5/5] Verifiziere Installation..." -ForegroundColor Cyan

$verificationScript = @"
import sys
errors = []
try:
    import sounddevice
    print('OK: sounddevice')
except ImportError as e:
    errors.append(f'sounddevice: {e}')

try:
    import numpy
    print('OK: numpy')
except ImportError as e:
    errors.append(f'numpy: {e}')

try:
    import faster_whisper
    print('OK: faster_whisper')
except ImportError as e:
    errors.append(f'faster_whisper: {e}')

if errors:
    print('FEHLER:', file=sys.stderr)
    for err in errors:
        print(f'  {err}', file=sys.stderr)
    sys.exit(1)
"@

$tempScript = [System.IO.Path]::GetTempFileName() + ".py"
$verificationScript | Out-File -FilePath $tempScript -Encoding UTF8

try {
    # Ausgabe erfassen, ohne dass PowerShell bei stderr einen Fehler wirft
    $oldErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    
    $processInfo = New-Object System.Diagnostics.ProcessStartInfo
    $processInfo.FileName = $venvPython
    $processInfo.Arguments = "`"$tempScript`""
    $processInfo.RedirectStandardOutput = $true
    $processInfo.RedirectStandardError = $true
    $processInfo.UseShellExecute = $false
    $processInfo.CreateNoWindow = $true
    
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $processInfo
    $process.Start() | Out-Null
    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()
    $exitCode = $process.ExitCode
    
    $ErrorActionPreference = $oldErrorAction
    
    if ($exitCode -eq 0) {
        # Erfolgreiche Ausgabe anzeigen
        if ($stdout) {
            $stdout -split "`n" | Where-Object { $_.Trim() -match '^OK:' } | ForEach-Object {
                Write-Host $_.Trim() -ForegroundColor Green
            }
        }
        Write-Host "  Verifikation erfolgreich" -ForegroundColor Green
    } else {
        # Fehlerausgabe anzeigen
        if ($stderr) {
            $stderr -split "`n" | Where-Object { $_.Trim() } | ForEach-Object {
                Write-Host $_.Trim() -ForegroundColor Red
            }
        }
        if ($stdout) {
            $stdout -split "`n" | Where-Object { $_.Trim() } | ForEach-Object {
                Write-Host $_.Trim() -ForegroundColor Red
            }
        }
        Write-Host "FEHLER: Verifikation fehlgeschlagen" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "FEHLER: Verifikation konnte nicht ausgeführt werden: $_" -ForegroundColor Red
    exit 1
} finally {
    Remove-Item -Path $tempScript -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "Installation abgeschlossen." -ForegroundColor Green
Write-Host "Virtual Environment: $venvPath" -ForegroundColor Gray
Write-Host ""
Write-Host "Aktivierung (PowerShell):" -ForegroundColor Cyan
Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor Gray
