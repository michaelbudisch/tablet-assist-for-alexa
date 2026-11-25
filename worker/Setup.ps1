# Deprecated compatible entrypoint. Existing .env is never overwritten.
& (Join-Path $PSScriptRoot "Worker-Windows.ps1") -Action Prepare
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
