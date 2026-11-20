@echo off
powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File "%~dp0Setup-Exporter.ps1" -WaitForExit
