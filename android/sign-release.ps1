param(
    [Parameter(Mandatory = $true)][string]$KeystorePath,
    [Parameter(Mandatory = $true)][string]$Alias,
    [string]$Output = ''
)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$version = (Get-Content VERSION -Raw).Trim()
if ($version -notmatch '^\d+\.\d+\.\d+$') { throw "Invalid version: $version" }
if (-not $Output) { $Output = "dist/TAFA-Device-Bridge-$version.apk" }
$unsigned = Join-Path $PSScriptRoot 'app/build/outputs/apk/release/app-release-unsigned.apk'
$expectedCertificate = '3f3949b442ccda37ca1b779a14c1161b5a0f6139f35f3808780e607862b58281'
if (-not (Test-Path $unsigned)) { throw "Build the release first: .\build.ps1 -Configuration Release -Check" }
if (-not (Test-Path $KeystorePath)) { throw 'Original signing keystore not found' }
if (-not $env:ANDROID_HOME) { $env:ANDROID_HOME = Join-Path $env:LOCALAPPDATA 'Android\Sdk' }
$sdk = Join-Path $env:ANDROID_HOME 'build-tools\36.0.0'
$zipalign = Join-Path $sdk 'zipalign.exe'
$apksigner = Join-Path $sdk 'apksigner.bat'
if (-not (Test-Path $zipalign) -or -not (Test-Path $apksigner)) { throw 'Android Build Tools 36.0.0 are required' }
$dest = Join-Path $PSScriptRoot $Output
New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null
$aligned = Join-Path $env:TEMP ('tafa-aligned-' + [guid]::NewGuid() + '.apk')
try {
    & $zipalign -P 16 -f 4 $unsigned $aligned
    if ($LASTEXITCODE -ne 0) { throw 'zipalign failed' }
    # Passwords are requested by apksigner interactively; never pass them on the command line.
    & $apksigner sign --ks $KeystorePath --ks-key-alias $Alias --v4-signing-enabled false --out $dest $aligned
    if ($LASTEXITCODE -ne 0) { throw 'Signing failed' }
    & $apksigner verify --verbose --print-certs $dest
    if ($LASTEXITCODE -ne 0) { throw 'APK signature verification failed' }
    $newLines = & $apksigner verify --print-certs $dest
    if ($LASTEXITCODE -ne 0) { throw 'Unable to read APK signing certificate' }
    $newMatch = $newLines | Select-String 'Signer #1 certificate SHA-256 digest:'
    if (-not $newMatch) { throw 'Signing fingerprint unavailable' }
    $oldCert = $expectedCertificate
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
