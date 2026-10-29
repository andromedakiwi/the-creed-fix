# The Creed - Unofficial Patch v2.0 (Andromeda Kiwi + Claude)
# Optional: makes Windows save a minidump in <game folder>\CrashDumps whenever Creed.exe crashes.
# Needs administrator rights (Windows Error Reporting settings live in HKLM).
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'Creed.exe')) { $gameDir = $PSScriptRoot } else { $gameDir = Split-Path -Parent $PSScriptRoot }
$dumpDir = Join-Path $gameDir 'CrashDumps'
New-Item -ItemType Directory -Path $dumpDir -Force | Out-Null
$key = 'HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\Creed.exe'
New-Item -Path $key -Force | Out-Null
New-ItemProperty -Path $key -Name DumpFolder -Value $dumpDir -PropertyType ExpandString -Force | Out-Null
New-ItemProperty -Path $key -Name DumpType  -Value 1 -PropertyType DWord -Force | Out-Null
New-ItemProperty -Path $key -Name DumpCount -Value 10 -PropertyType DWord -Force | Out-Null
Write-Host "Crash dumps enabled. They will be saved in: $dumpDir" -ForegroundColor Green
