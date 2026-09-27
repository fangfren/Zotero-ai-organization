$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$source = Join-Path $root "zotero-plugin"
$release = Join-Path $root "release"

# Entries are written in this order; every path uses forward slashes because
# Gecko resolves add-on resources through JAR URIs and does not understand
# backslash-separated ZIP entry names.
$requiredFiles = @(
    "manifest.json",
    "bootstrap.js",
    "prefs.js",
    "content/workbench.js",
    "content/workbench.css",
    "content/preferences.xhtml",
    "content/preferences.js",
    "content/icons/workbench-16.svg",
    "content/icons/workbench-20.svg",
    "content/icons/workbench-48.svg",
    "content/icons/workbench-96.svg",
    "locale/en-US/research-workbench.ftl",
    "locale/zh-CN/research-workbench.ftl"
)

if (-not (Test-Path -LiteralPath $source -PathType Container)) {
    throw "Plugin source directory not found: $source"
}

foreach ($relativePath in $requiredFiles) {
    $path = Join-Path $source $relativePath
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required plugin file not found: $relativePath"
    }
}

$manifest = Get-Content -LiteralPath (Join-Path $source "manifest.json") -Raw | ConvertFrom-Json
$version = [string]$manifest.version
if (-not $version) {
    throw "manifest.json does not declare a version"
}
$destination = Join-Path $release "zotero-research-workbench-$version.xpi"

New-Item -ItemType Directory -Force -Path $release | Out-Null
if (Test-Path -LiteralPath $destination) {
    Remove-Item -LiteralPath $destination -Force
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.IO.Compression

# Build the archive entry by entry instead of using CreateFromDirectory, which
# on .NET Framework writes Windows-style backslashes into the entry names.
$archiveStream = [System.IO.File]::Create($destination)
$archive = New-Object System.IO.Compression.ZipArchive(
    $archiveStream,
    [System.IO.Compression.ZipArchiveMode]::Create,
    $true
)
try {
    foreach ($relativePath in $requiredFiles) {
        $filePath = Join-Path $source ($relativePath -replace "/", "\")
        $entry = $archive.CreateEntry(
            $relativePath,
            [System.IO.Compression.CompressionLevel]::Optimal
        )
        $entry.LastWriteTime = (Get-Item -LiteralPath $filePath).LastWriteTime
        $entryStream = $entry.Open()
        $fileStream = [System.IO.File]::OpenRead($filePath)
        try {
            $fileStream.CopyTo($entryStream)
        }
        finally {
            $fileStream.Dispose()
            $entryStream.Dispose()
        }
    }
}
finally {
    $archive.Dispose()
    $archiveStream.Dispose()
}

$archive = [System.IO.Compression.ZipFile]::OpenRead($destination)
try {
    $entries = @($archive.Entries | ForEach-Object { $_.FullName })

    $badEntries = @($entries | Where-Object { $_ -like "*\*" })
    if ($badEntries.Count -gt 0) {
        throw "Built XPI contains backslash-separated entries: $($badEntries -join ', ')"
    }

    foreach ($relativePath in $requiredFiles) {
        if ($entries -notcontains $relativePath) {
            throw "Built XPI is missing $relativePath"
        }
    }

    if ($entries | Where-Object { $_ -like "zotero-plugin/*" }) {
        throw "Built XPI contains an unexpected zotero-plugin/ prefix"
    }
}
finally {
    $archive.Dispose()
}

Write-Host "Built $destination ($((Get-Item -LiteralPath $destination).Length) bytes)"
