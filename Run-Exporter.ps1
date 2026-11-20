$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Add-Type -AssemblyName System.Windows.Forms
try {
    Write-Host 'Doppel Echo Voice Model Converter' -ForegroundColor Cyan
    $python = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
    $ready = $false
    if (Test-Path -LiteralPath $python) {
        Write-Host 'Checking the converter environment. Please wait; no input is needed.' -ForegroundColor Cyan
        $ErrorActionPreference = 'Continue'
        & $python -I -X utf8 (Join-Path $PSScriptRoot 'check_runtime.py') 2>&1 | ForEach-Object { Write-Host $_ }
        $ready = ($LASTEXITCODE -eq 0)
        $ErrorActionPreference = 'Stop'
    }
    if (!$ready) {
        $answer = [System.Windows.Forms.MessageBox]::Show('Set up the CPU converter in this folder? Python 3.10-3.12 (64-bit) and an internet connection are required. Packages will be downloaded from PyPI and PyTorch. Your game environment will not be changed.', 'Doppel Echo - First-time setup', 'YesNo', 'Question')
        if ($answer -ne 'Yes') { exit 0 }
        Write-Host 'Starting first-time setup. Downloads and installation may take several minutes.' -ForegroundColor Cyan
        Write-Host 'Please keep this window open. No Enter key is needed while setup is running.'
        & (Join-Path $PSScriptRoot 'Setup-Exporter.ps1')
        if ($LASTEXITCODE -ne 0) { throw 'Setup failed. See logs/setup-*.log.' }
    }
    Write-Host 'READY. Next: select your RVC .pth model, then choose where to save the .onnx file.' -ForegroundColor Green
    Read-Host 'Press Enter to open the model selection window' | Out-Null
    $open = New-Object System.Windows.Forms.OpenFileDialog
    $open.Title = 'Select RVC voice model (.pth)'
    $open.Filter = 'RVC voice model (*.pth)|*.pth'
    if ($open.ShowDialog() -ne 'OK') { exit 0 }
    $inputPath = $open.FileName
    $open.Dispose()
    $save = New-Object System.Windows.Forms.SaveFileDialog
    $save.Title = 'Save validated ONNX model'
    $save.Filter = 'ONNX model (*.onnx)|*.onnx'
    $save.FileName = [IO.Path]::GetFileNameWithoutExtension($inputPath) + '.onnx'
    $save.InitialDirectory = [IO.Path]::GetDirectoryName($inputPath)
    $save.OverwritePrompt = $true
    Write-Host 'Model selected. Choose the output filename in the save window.' -ForegroundColor Cyan
    if ($save.ShowDialog() -ne 'OK') { exit 0 }
    $outputPath = $save.FileName
    $save.Dispose()
    $logs = Join-Path $PSScriptRoot 'logs'
    [IO.Directory]::CreateDirectory($logs) | Out-Null
    $log = Join-Path $logs ('export-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.log')
    Write-Host 'Converting on CPU. Please keep this window open.'
    # Native warnings are ordinary log output in Windows PowerShell 5.1.
    $ErrorActionPreference = 'Continue'
    & $python -I -X utf8 -u (Join-Path $PSScriptRoot 'export_rvc.py') $inputPath $outputPath --overwrite 2>&1 | Tee-Object -FilePath $log
    $code = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($code -ne 0) { throw "Export failed. Original files were preserved. Log: $log" }
    Write-Host "DONE. Saved model: $outputPath" -ForegroundColor Green
    Write-Host "Log: $log"
    [System.Windows.Forms.MessageBox]::Show("Export and validation succeeded.`n$outputPath", 'ONNX Export', 'OK', 'Information') | Out-Null
    Read-Host 'Press Enter to close this window' | Out-Null
} catch {
    Write-Host $_ -ForegroundColor Red
    [System.Windows.Forms.MessageBox]::Show($_.ToString(), 'ONNX Export failed', 'OK', 'Error') | Out-Null
    exit 1
}
