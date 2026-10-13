#Requires -Version 5.1
[CmdletBinding()]
param(
    [string]$RepoUrl,
    [string]$CloneDir = (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'Codex\codex-research-skills'),
    [string]$Destination = (Join-Path ([Environment]::GetFolderPath('UserProfile')) '.agents\skills'),
    [switch]$Offline
)
$ErrorActionPreference = 'Stop'
if ($RepoUrl) {
    if (-not (Test-Path -LiteralPath $CloneDir)) {
        & git clone -c core.longpaths=true -- $RepoUrl $CloneDir
        if ($LASTEXITCODE -ne 0) { throw 'Git clone failed; authenticate GitHub first.' }
    }
    & (Join-Path $CloneDir 'sync-windows.ps1') -Destination $Destination -Offline:$Offline -RemoteUrl $RepoUrl
} else {
    & (Join-Path $PSScriptRoot 'sync-windows.ps1') -Destination $Destination -Offline:$Offline
}
