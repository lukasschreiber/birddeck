param([switch]$Force)
$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'de.birdtagging.names.sdPlugin'
$plugins = Join-Path $env:APPDATA 'Elgato\StreamDeck\Plugins'
$destination = Join-Path $plugins 'de.birdtagging.names.sdPlugin'
if ((Test-Path -LiteralPath $destination) -and !$Force) {
    throw 'Bird names is already installed. Use -Force to update it after closing Stream Deck.'
}
New-Item -ItemType Directory -Path $destination -Force | Out-Null
Copy-Item -Path (Join-Path $source '*') -Destination $destination -Recurse -Force
if (Get-Process -Name StreamDeck -ErrorAction SilentlyContinue) {
    Start-Process 'streamdeck://plugins/restart/de.birdtagging.names' -WindowStyle Hidden
    Write-Output "Installed Bird names in $destination and requested Stream Deck to load it."
} else {
    Write-Output "Installed Bird names in $destination. Open Stream Deck to load it."
}
