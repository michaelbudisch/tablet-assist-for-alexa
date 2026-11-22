param([ValidateSet('Debug', 'Release')][string]$Configuration = 'Debug', [switch]$Check)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not $env:JAVA_HOME) {
    $cachedJdk = Get-ChildItem (Join-Path $PSScriptRoot '.build-cache\tools') -Directory -Filter 'jdk-17*' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($cachedJdk) { $env:JAVA_HOME = $cachedJdk.FullName }
}
if (-not $env:JAVA_HOME -or -not (Test-Path (Join-Path $env:JAVA_HOME 'bin\java.exe'))) {
    throw 'Install JDK 17 and set JAVA_HOME. Android lint in this project requires JDK 17.'
}
$javaRelease = Join-Path $env:JAVA_HOME 'release'
if (-not (Test-Path $javaRelease) -or -not (Select-String -LiteralPath $javaRelease -Pattern '^JAVA_VERSION="17\.' -Quiet)) {
    throw 'Set JAVA_HOME to JDK 17 before building (including Android lint).'
}
if (-not $env:ANDROID_HOME) { $env:ANDROID_HOME = Join-Path $env:LOCALAPPDATA 'Android\Sdk' }
if (-not (Test-Path (Join-Path $env:ANDROID_HOME 'platforms\android-35\android.jar'))) {
    throw 'Install Android SDK Platform 35 with Android Studio SDK Manager.'
}
$tasks = @(':app:assemble' + $Configuration)
if ($Check) { $tasks += @(':app:testDebugUnitTest', ':app:lintDebug', ':app:assembleDebugAndroidTest') }
& (Join-Path $PSScriptRoot 'gradlew.bat') @tasks --console=plain --no-problems-report
if ($LASTEXITCODE -ne 0) { throw 'Android build failed.' }
if ($Configuration -eq 'Release') {
    Write-Host 'Unsigned release APK: app/build/outputs/apk/release/app-release-unsigned.apk. Sign privately before installation.'
} else { Write-Host 'Debug APK: app/build/outputs/apk/debug/app-debug.apk' }
