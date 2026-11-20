param([string]$PythonPath = '', [switch]$WaitForExit)
$ErrorActionPreference = 'Stop'
$setupLock = $null
$transcribing = $false
try {
    $setupLock = [IO.File]::Open((Join-Path $PSScriptRoot '.setup.lock'), 'OpenOrCreate', 'ReadWrite', 'None')
    $logs = Join-Path $PSScriptRoot 'logs'
    [IO.Directory]::CreateDirectory($logs) | Out-Null
    Start-Transcript -Path (Join-Path $logs ('setup-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.log')) | Out-Null
    $transcribing = $true
    Write-Host '[1/5] Finding a supported Python installation. Please wait.' -ForegroundColor Cyan
    $probe = 'import sys, struct; assert (3,10) <= sys.version_info[:2] <= (3,12) and struct.calcsize(chr(80)) == 8; print(sys.executable)'
    if (!$PythonPath) {
        $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
        if ($launcher) {
            foreach ($tag in @('-3.12', '-3.11', '-3.10')) {
                try {
                    $candidate = & $launcher.Source $tag -I -c $probe 2>$null
                    if ($LASTEXITCODE -eq 0 -and $candidate) { $PythonPath = [string]($candidate | Select-Object -Last 1); break }
                } catch { }
            }
        }
        if (!$PythonPath) {
            $command = Get-Command python.exe -ErrorAction SilentlyContinue
            if ($command) {
                try {
                    $candidate = & $command.Source -I -c $probe 2>$null
                    if ($LASTEXITCODE -eq 0 -and $candidate) { $PythonPath = [string]($candidate | Select-Object -Last 1) }
                } catch { }
            }
        }
        if (!$PythonPath) {
            Add-Type -AssemblyName System.Windows.Forms
            [System.Windows.Forms.MessageBox]::Show('Install Python 3.10, 3.11 or 3.12 (Windows 64-bit) from python.org, then run again. If already installed, select its python.exe in the next dialog. See GUIDE.en.md or GUIDE.ko.md.', 'Python required', 'OK', 'Information') | Out-Null
            $dialog = New-Object System.Windows.Forms.OpenFileDialog
            $dialog.Title = 'Select Python 3.10-3.12 (64-bit) python.exe'
            $dialog.Filter = 'Python executable (python.exe)|python.exe'
            if ($dialog.ShowDialog() -ne 'OK') { throw 'Setup cancelled. Python was not selected.' }
            $PythonPath = $dialog.FileName
            $dialog.Dispose()
        }
    }
    & $PythonPath -I -c $probe
    if ($LASTEXITCODE -ne 0) { throw 'Use Python 3.10-3.12, Windows x64, with venv and pip support.' }
    $venv = Join-Path $PSScriptRoot '.venv'
    $python = Join-Path $venv 'Scripts/python.exe'
    Write-Host '[2/5] Preparing the local .venv environment. Please wait; no input is needed.' -ForegroundColor Cyan
    if (!(Test-Path -LiteralPath $python)) {
        & $PythonPath -I -m venv $venv
        if ($LASTEXITCODE -ne 0) { throw 'Could not create the local Python environment. Use a full Python installation, not an embedded runtime.' }
    }
    Write-Host '[3/5] Downloading/installing CPU PyTorch. This may take several minutes.' -ForegroundColor Cyan
    & $python -I -m pip --isolated install --disable-pip-version-check --index-url https://download.pytorch.org/whl/cpu 'torch==2.6.0+cpu'
    if ($LASTEXITCODE -ne 0) { throw 'PyTorch installation failed. Check the internet connection and setup log.' }
    Write-Host '[4/5] Downloading/installing ONNX dependencies. Please wait.' -ForegroundColor Cyan
    & $python -I -m pip --isolated install --disable-pip-version-check --index-url https://pypi.org/simple -r (Join-Path $PSScriptRoot 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'ONNX dependency installation failed. Check the setup log.' }
    Write-Host '[5/5] Checking installed packages. First-time imports may take a moment.' -ForegroundColor Cyan
    & $python -I (Join-Path $PSScriptRoot 'check_runtime.py')
    if ($LASTEXITCODE -ne 0) { throw 'Runtime check failed. See the setup log.' }
    Write-Host 'Setup complete. Start ONNX Export.bat to convert a model.' -ForegroundColor Green
} catch {
    Write-Host $_ -ForegroundColor Red
    exit 1
} finally {
    if ($transcribing) { Stop-Transcript | Out-Null }
    if ($setupLock) { $setupLock.Dispose() }
    if ($WaitForExit) { Read-Host 'Press Enter to close this window' | Out-Null }
}
