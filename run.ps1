param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$ErrorActionPreference = "Stop"
$env:PYTHONDONTWRITEBYTECODE = "1"

function Test-Python {
    param([string]$Executable, [string[]]$Arguments = @())
    try {
        & $Executable @Arguments -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" *> $null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Find-Python {
    if ($env:RESEARCH_WORKBENCH_PYTHON) {
        if (Test-Python $env:RESEARCH_WORKBENCH_PYTHON) {
            return $env:RESEARCH_WORKBENCH_PYTHON
        }
        throw "RESEARCH_WORKBENCH_PYTHON is not a compatible Python executable: $env:RESEARCH_WORKBENCH_PYTHON"
    }

    $venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    if ((Test-Path -LiteralPath $venvPython) -and (Test-Python $venvPython)) {
        return $venvPython
    }

    foreach ($name in @("python.exe", "python3.exe")) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($command -and (Test-Python $command.Source)) {
            return $command.Source
        }
    }

    $pyLauncher = Get-Command "py.exe" -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        try {
            $resolved = & $pyLauncher.Source -3 -c "import sys; print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0 -and $resolved -and (Test-Python $resolved.Trim())) {
                return $resolved.Trim()
            }
        } catch {
            # Fall through to the installation error below.
        }
    }

    throw "Python 3.10 or newer was not found. Install it from https://www.python.org/downloads/ and enable 'Add Python to PATH'."
}

$python = Find-Python
& $python (Join-Path $PSScriptRoot "sync_zotero.py") @Args
exit $LASTEXITCODE
