# The Creed (1999) - Unofficial Patch v1.2 - by Andromeda Kiwi + Claude
# OPTIONAL: copies the files the game reads from its two CDs into the game folder
# (cd1\Data and cd2\Data), so the CDs are no longer needed to play.
# Without this step the game still works - it just asks for the CD like the original.

param([switch]$NoPrompt)
$ErrorActionPreference = 'Stop'

$Discs = @(
    @{ N = 1; Name = 'Main'; Label = 'CREED_MAIN'; Files = @{ 'data.v00' = 65467080 } },
    @{ N = 2; Name = 'Data'; Label = 'CREED_DATA'; Files = @{ 'Data.v01' = 20455848; 'Data.v02' = 16928016; 'Data.v03' = 18413052 } }
)

function Say([string]$msg, [string]$color = 'Gray') { Write-Host $msg -ForegroundColor $color }
function Clear-RO([string]$path) {
    if (Test-Path -LiteralPath $path) { $i = Get-Item -LiteralPath $path -Force; if ($i.IsReadOnly) { $i.IsReadOnly = $false } }
}

if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'Creed.exe')) { $GameDir = $PSScriptRoot } else { $GameDir = Split-Path -Parent $PSScriptRoot }
if (-not (Test-Path -LiteralPath (Join-Path $GameDir 'Creed.exe'))) { throw "Creed.exe not found next to the Extras folder ($GameDir)." }

function Disc-Dir($disc) { Join-Path (Join-Path $GameDir ('cd' + $disc.N)) 'Data' }
function Disc-Complete($disc) {
    foreach ($f in $disc.Files.Keys) {
        $p = Join-Path (Disc-Dir $disc) $f
        if (-not (Test-Path -LiteralPath $p)) { return $false }
        if ((Get-Item -LiteralPath $p).Length -ne $disc.Files[$f]) { return $false }
    }
    return $true
}
function Find-DiscDrive([string]$label) {
    try {
        $d = Get-CimInstance -ClassName Win32_LogicalDisk -Filter 'DriveType=5' -ErrorAction Stop |
             Where-Object { $_.VolumeName -eq $label } | Select-Object -First 1
        if ($d) { return $d.DeviceID + '\' }
    } catch { }
    return $null
}

Say 'The Creed - copy CD files (No-CD)' 'Cyan'
Say "Game folder: $GameDir"
$allOk = $true
foreach ($disc in $Discs) {
    if (Disc-Complete $disc) { Say "CD $($disc.N) files already copied (cd$($disc.N)\Data)." 'Green'; continue }
    $done = $false
    while (-not $done) {
        $drive = Find-DiscDrive $disc.Label
        if ($drive) {
            $dst = Disc-Dir $disc
            New-Item -ItemType Directory -Path $dst -Force | Out-Null
            foreach ($f in $disc.Files.Keys) {
                $src = Join-Path (Join-Path $drive 'Data') $f
                if (-not (Test-Path -LiteralPath $src)) { throw "CD $($disc.N) in $drive does not contain Data\$f." }
                Say "  copying Data\$f from CD $($disc.N) ($drive)..."
                $out = Join-Path $dst $f
                Clear-RO $out
                Copy-Item -LiteralPath $src -Destination $out -Force
                Clear-RO $out
            }
            if (-not (Disc-Complete $disc)) { throw "Copy from CD $($disc.N) is incomplete - check the disc and try again." }
            Say "CD $($disc.N) ($($disc.Name) Disc) copied." 'Green'
            $done = $true
        } elseif ($NoPrompt) {
            $allOk = $false; break
        } else {
            Say ''
            Say "Insert The Creed CD $($disc.N) ('$($disc.Name) Disc')." 'Yellow'
            $ans = Read-Host 'Press Enter when ready (or type S + Enter to stop)'
            if ($ans -match '^[sS]') { $allOk = $false; break }
        }
    }
    if (-not $allOk) { break }
}
Say ''
if ($allOk) { Say 'Done - you can play without the CDs now.' 'Cyan' }
else { Say 'Stopped. The game still works, it will just ask for the CD. Run CopyCDs.bat again any time.' 'Yellow' }
