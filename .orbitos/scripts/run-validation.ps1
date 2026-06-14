param(
  [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

$ErrorActionPreference = "Stop"

$python = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $python) {
  $python = Get-Command py -ErrorAction SilentlyContinue
}

if ($null -eq $python) {
  throw "Python is required for OrbitOS validation. Fallback manually with: node .orbitos/scripts/run-validation.mjs"
}

& $python.Source (Join-Path $PSScriptRoot "run-validation.py") $Root
exit $LASTEXITCODE
