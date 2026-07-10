param(
    [Parameter(Mandatory = $true)]
    [string]$TargetFile,

    [int]$Keep = 5
)

$resolved = Resolve-Path -LiteralPath $TargetFile -ErrorAction Stop
$targetPath = $resolved.Path

if (-not (Test-Path -LiteralPath $targetPath -PathType Leaf)) {
    throw "Target file not found: $TargetFile"
}

if ($Keep -lt 1) {
    throw "Keep must be at least 1."
}

$fileItem = Get-Item -LiteralPath $targetPath
$parentDir = $fileItem.DirectoryName
$fileName = $fileItem.Name
$backupDir = Join-Path $parentDir "_backups"
$fileBackupDir = Join-Path $backupDir $fileName

New-Item -ItemType Directory -Force -Path $fileBackupDir | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupName = "{0}-{1}.bak" -f $timestamp, $fileName
$backupPath = Join-Path $fileBackupDir $backupName

Copy-Item -LiteralPath $targetPath -Destination $backupPath -Force

$backups = Get-ChildItem -LiteralPath $fileBackupDir -File |
    Sort-Object LastWriteTime -Descending

if ($backups.Count -gt $Keep) {
    $toRemove = $backups | Select-Object -Skip $Keep
    foreach ($item in $toRemove) {
        Remove-Item -LiteralPath $item.FullName -Force
    }
}

Write-Output ("Backup created: {0}" -f $backupPath)
Write-Output ("Restore points kept: {0}" -f $Keep)
