#Requires -Version 5.1
[CmdletBinding()]
param(
    [string]$Destination = (Join-Path ([Environment]::GetFolderPath('UserProfile')) '.agents\skills'),
    [switch]$Offline,
    [switch]$Push,
    [string]$RemoteUrl
)
$ErrorActionPreference = 'Stop'
$PythonCommand = $null
$PythonPrefix = @()
if ($env:RESEARCH_SKILLS_PYTHON) {
    $PythonCommand = $env:RESEARCH_SKILLS_PYTHON
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCommand = 'py'; $PythonPrefix = @('-3')
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCommand = 'python'
} else { throw 'Install Python 3.9+ (3.11+ recommended), then rerun; WSL is not required.' }
$CommandArgs = @((Join-Path $PSScriptRoot 'scripts\manage.py'), 'sync', '--repo', $PSScriptRoot, '--dest', $Destination)
if ($Offline) { $CommandArgs += '--offline' }
if ($Push) { $CommandArgs += '--push' }
if ($RemoteUrl) { $CommandArgs += @('--remote-url', $RemoteUrl) }
& $PythonCommand @PythonPrefix @CommandArgs
if ($LASTEXITCODE -ne 0) { throw "Skills sync stopped (exit $LASTEXITCODE). Local changes were preserved." }
