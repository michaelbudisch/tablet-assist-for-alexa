param(
    [Parameter(Mandatory = $true)][string]$KeystorePath,
    [Parameter(Mandatory = $true)][string]$Alias,
    [string]$Output = 'dist/HA-Jarvis-Echo-Relay-0.9.0.apk'
)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$version = (Get-Content VERSION -Raw).Trim()
if ($version -ne '0.9.0') { throw "Expected version 0.9.0; found $version" }
$unsigned = Join-Path $PSScriptRoot 'app/build/outputs/apk/release/app-release-unsigned.apk'
$reference = Join-Path $PSScriptRoot 'downloads/HA-Jarvis-Echo-Relay-0.7.1.apk'
if (-not (Test-Path $unsigned)) { throw "Build the release first: .\build.ps1 -Configuration Release -Check" }
if (-not (Test-Path $reference)) { throw 'Original signed 0.7.1 APK is missing' }
if (-not (Test-Path $KeystorePath)) { throw 'Original signing keystore not found' }
if (-not $env:ANDROID_HOME) { $env:ANDROID_HOME = Join-Path $env:LOCALAPPDATA 'Android\Sdk' }
$sdk = Join-Path $env:ANDROID_HOME 'build-tools\34.0.0'
$zipalign = Join-Path $sdk 'zipalign.exe'
$apksigner = Join-Path $sdk 'apksigner.bat'
if (-not (Test-Path $zipalign) -or -not (Test-Path $apksigner)) { throw 'Android Build Tools 34.0.0 are required' }
$dest = Join-Path $PSScriptRoot $Output
New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null
$aligned = Join-Path $env:TEMP ('jarvis-aligned-' + [guid]::NewGuid() + '.apk')
try {
    & $zipalign -f -p 4 $unsigned $aligned
    if ($LASTEXITCODE -ne 0) { throw 'zipalign failed' }
    # Passwords are requested by apksigner interactively; never pass them on the command line.
    & $apksigner sign --ks $KeystorePath --ks-key-alias $Alias --out $dest $aligned
    if ($LASTEXITCODE -ne 0) { throw 'Signing failed' }
    & $apksigner verify --verbose --print-certs $dest
    if ($LASTEXITCODE -ne 0) { throw 'APK signature verification failed' }
    $oldLines = & $apksigner verify --print-certs $reference
    $newLines = & $apksigner verify --print-certs $dest
    if ($LASTEXITCODE -ne 0) { throw 'Unable to read APK signing certificate' }
    $oldMatch = $oldLines | Select-String 'Signer #1 certificate SHA-256 digest:'
    $newMatch = $newLines | Select-String 'Signer #1 certificate SHA-256 digest:'
    if (-not $oldMatch -or -not $newMatch) { throw 'Signing fingerprint unavailable' }
    $oldCert = ($oldMatch.ToString() -split 'digest:\s*')[-1].Trim().ToLowerInvariant()
    $newCert = ($newMatch.ToString() -split 'digest:\s*')[-1].Trim().ToLowerInvariant()
    if ($oldCert -ne $newCert) {
        Remove-Item $dest -Force
        throw 'This is NOT the signing key from version 0.7.1. Refusing incompatible update.'
    }
    $hash = (Get-FileHash $dest -Algorithm SHA256).Hash.ToLowerInvariant()
    $checksum = Join-Path (Split-Path $dest) 'SHA256SUMS'
    Set-Content -Path $checksum -Value "$hash  $(Split-Path $dest -Leaf)"
    Write-Host "Update-compatible signed APK: $dest"
} finally {
    Remove-Item $aligned -Force -ErrorAction SilentlyContinue
}
