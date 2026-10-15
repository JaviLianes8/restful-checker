# Local quality gate. Run before every commit. No CI runs in the cloud.
# $ErrorActionPreference does NOT stop on a native command's non-zero exit, so each tool's
# exit code is checked explicitly: a red gate must fail, never pass silently.
$ErrorActionPreference = "Stop"

function Invoke-Step($label, [scriptblock]$cmd) {
    Write-Host "== $label =="
    & $cmd
    if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: $label (exit $LASTEXITCODE)"; exit $LASTEXITCODE }
}

Invoke-Step "ruff format" { ruff format --check . }
Invoke-Step "ruff lint"   { ruff check . }
Invoke-Step "mypy"        { mypy --strict restful_checker tests }
Invoke-Step "pytest"      { pytest }
Write-Host "gate green"
