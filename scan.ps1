# scan.ps1 — run BiometriScan analysis in Docker
#
# Usage:
#   .\scan.ps1 C:\path\to\top_view.jpg
#   .\scan.ps1 C:\path\to\top_view.jpg C:\path\to\side_view.jpg
#   .\scan.ps1 C:\path\to\top_view.jpg --confidence 0.1
#   .\scan.ps1 C:\path\to\top_view.jpg --rebuild

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$TopView,
    [Parameter(Position=1)]
    [string]$SideView = "",
    [float]$Confidence = 0.3,
    [string]$Board = "7x9_30mm",
    [switch]$Flip,
    [switch]$Rebuild
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot   # biometric-grip-toolkit/ only
$ImageTag = "biometric-grip"

# Resolve photo to absolute path
$TopViewAbs = Resolve-Path $TopView | Select-Object -ExpandProperty Path
$PhotoDir = Split-Path $TopViewAbs -Parent
$TopViewName = Split-Path $TopViewAbs -Leaf

# Build image if not present or --Rebuild
$exists = docker image inspect $ImageTag 2>$null
if ($Rebuild -or -not $exists) {
    Write-Host "Building Docker image..."
    docker build -t $ImageTag $ProjectRoot
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

# Mount: repo → /repo (code), photo dir → /photos (input/output)
$RunArgs = @(
    "run", "--rm",
    "-v", "${ProjectRoot}:/repo",
    "-v", "${PhotoDir}:/photos",
    "-w", "/repo",
    "--entrypoint", "python",
    $ImageTag,
    "1_biometriscan/analyze_photo.py",
    "/photos/$TopViewName",
    "--board", $Board,
    "--confidence", $Confidence
)

if ($Flip) {
    $RunArgs += "--flip"
}

if ($SideView) {
    $SideAbs = Resolve-Path $SideView | Select-Object -ExpandProperty Path
    $SideName = Split-Path $SideAbs -Leaf
    $RunArgs += "/photos/$SideName"
}

Write-Host ""
Write-Host "docker $($RunArgs -join ' ')"
Write-Host ""
docker @RunArgs
