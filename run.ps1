param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$env:PYTHONDONTWRITEBYTECODE = "1"

$python = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Bundled Python was not found at: $python"
}

& $python (Join-Path $PSScriptRoot "sync_zotero.py") @Args
exit $LASTEXITCODE
