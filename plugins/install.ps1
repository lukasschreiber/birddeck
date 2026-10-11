param([switch]$Force)
$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'de.birdtagging.names.sdPlugin'
if (!(Test-Path -LiteralPath (Join-Path $source 'node_modules\@napi-rs\canvas'))) {
    npm ci --omit=dev --prefix $source
    if ($LASTEXITCODE -ne 0) { throw 'Could not install the Stream Deck runtime dependencies.' }
}
$plugins = Join-Path $env:APPDATA 'Elgato\StreamDeck\Plugins'
$destination = Join-Path $plugins 'de.birdtagging.names.sdPlugin'
if ((Test-Path -LiteralPath $destination) -and !$Force) {
    throw 'Bird names is already installed. Use -Force to update it after closing Stream Deck.'
}
New-Item -ItemType Directory -Path $destination -Force | Out-Null
foreach ($sourceFile in Get-ChildItem -LiteralPath $source -Recurse -File) {
    $relativeName = $sourceFile.FullName.Substring($source.Length).TrimStart('\')
    $targetFile = Join-Path $destination $relativeName
    # Native renderer binaries are memory-mapped while the plugin is running.
    # Leave identical files in place rather than attempting to overwrite them.
    if ((Test-Path -LiteralPath $targetFile) -and
        ((Get-FileHash -LiteralPath $sourceFile.FullName).Hash -eq (Get-FileHash -LiteralPath $targetFile).Hash)) {
        continue
    }
    New-Item -ItemType Directory -Path ([System.IO.Path]::GetDirectoryName($targetFile)) -Force | Out-Null
    Copy-Item -LiteralPath $sourceFile.FullName -Destination $targetFile -Force
}
if (Get-Process -Name StreamDeck -ErrorAction SilentlyContinue) {
    Start-Process 'streamdeck://plugins/restart/de.birdtagging.names' -WindowStyle Hidden
    Write-Output "Installed Bird names in $destination and requested Stream Deck to load it."
} else {
    Write-Output "Installed Bird names in $destination. Open Stream Deck to load it."
}
