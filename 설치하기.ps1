param(
    [switch]$ReplaceExisting
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

Write-Host ''
Write-Host '스마트 업무 에이전트 설치를 시작합니다.' -ForegroundColor Cyan
Write-Host ''

$kitRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$marketplaceFile = Join-Path $kitRoot '.agents\plugins\marketplace.json'
$pluginManifest = Join-Path $kitRoot 'plugins\smart-work-agent\.codex-plugin\plugin.json'

if (-not (Test-Path -LiteralPath $marketplaceFile)) {
    throw "설치 파일을 찾지 못했습니다: $marketplaceFile"
}
if (-not (Test-Path -LiteralPath $pluginManifest)) {
    throw "플러그인 파일을 찾지 못했습니다: $pluginManifest"
}

$codexCommand = Get-Command codex -ErrorAction SilentlyContinue
if ($null -eq $codexCommand) {
    throw 'Codex 명령을 찾지 못했습니다. Codex 앱을 최신 버전으로 설치한 뒤 다시 실행해 주세요.'
}

Write-Host '1/4 설치 파일을 확인했습니다.' -ForegroundColor Green

$marketplaceOutput = & $codexCommand.Source plugin marketplace list --json 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) {
    throw "Codex 마켓플레이스 목록을 확인하지 못했습니다.`n$marketplaceOutput"
}

try {
    $marketplaceList = $marketplaceOutput | ConvertFrom-Json
} catch {
    throw "Codex 마켓플레이스 목록 형식을 읽지 못했습니다.`n$marketplaceOutput"
}

$existingMarketplace = @($marketplaceList.marketplaces | Where-Object { $_.name -eq 'codex-starter-kit' }) | Select-Object -First 1

$pluginListRaw = & $codexCommand.Source plugin list --json 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) {
    throw "설치된 플러그인을 확인하지 못했습니다.`n$pluginListRaw"
}

$alreadyInstalled = $false
try {
    $pluginList = $pluginListRaw | ConvertFrom-Json
    $alreadyInstalled = @($pluginList.installed | Where-Object {
        $_.name -eq 'smart-work-agent' -and $_.marketplaceName -eq 'codex-starter-kit'
    }).Count -gt 0
} catch {
    $alreadyInstalled = $pluginListRaw -match '(?i)smart-work-agent'
}

if ($alreadyInstalled -and $ReplaceExisting) {
    $removeOutput = & $codexCommand.Source plugin remove 'smart-work-agent@codex-starter-kit' --json 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        throw "기존 에이전트 버전을 제거하지 못했습니다.`n$removeOutput"
    }
    Write-Host '2/4 사용자가 교체를 요청해 기존 에이전트 캐시를 정리했습니다.' -ForegroundColor Green
} elseif ($alreadyInstalled) {
    Write-Host '2/4 같은 에이전트가 이미 설치되어 있어 기존 상태를 유지합니다.' -ForegroundColor Green
} else {
    Write-Host '2/4 기존 설치가 없어 새로 설치합니다.' -ForegroundColor Green
}

$normalizedKitRoot = [System.IO.Path]::GetFullPath($kitRoot).TrimEnd('\')
if ($null -ne $existingMarketplace) {
    $normalizedExistingRoot = [System.IO.Path]::GetFullPath([string]$existingMarketplace.root).TrimEnd('\')
    if (-not $normalizedExistingRoot.Equals($normalizedKitRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        if (-not $ReplaceExisting) {
            throw '같은 이름의 마켓플레이스가 다른 경로에 있습니다. 기존 상태를 보존했습니다. 경로를 확인한 뒤 교체하려면 -ReplaceExisting을 명시하세요.'
        }
        $removeMarketplaceOutput = & $codexCommand.Source plugin marketplace remove 'codex-starter-kit' --json 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0) {
            throw "이전 팀 마켓플레이스 경로를 정리하지 못했습니다.`n$removeMarketplaceOutput"
        }
        $existingMarketplace = $null
    }
}

if ($null -eq $existingMarketplace) {
    $addOutput = & $codexCommand.Source plugin marketplace add $kitRoot --json 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        throw "팀 마켓플레이스를 추가하지 못했습니다.`n$addOutput"
    }
    Write-Host '3/4 현재 ZIP 위치의 팀 마켓플레이스를 등록했습니다.' -ForegroundColor Green
} else {
    Write-Host '3/4 팀 마켓플레이스 경로가 현재 위치와 일치합니다.' -ForegroundColor Green
}

if ($alreadyInstalled -and -not $ReplaceExisting) {
    Write-Host '4/4 기존 스마트 업무 에이전트를 그대로 사용합니다.' -ForegroundColor Green
} else {
    $installOutput = & $codexCommand.Source plugin add 'smart-work-agent@codex-starter-kit' --json 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        throw "에이전트 플러그인을 설치하지 못했습니다.`n$installOutput"
    }
    Write-Host '4/4 스마트 업무 에이전트 최신본을 설치했습니다.' -ForegroundColor Green
}

Write-Host ''
Write-Host '설치가 끝났습니다.' -ForegroundColor Cyan
Write-Host 'Codex 앱을 완전히 종료했다가 다시 열고, 이 스타터 키트 폴더에서 새 작업을 시작하세요.'
Write-Host '훅 검토 알림이 나오면 smart-work-agent의 내용을 확인한 뒤 신뢰해 주세요.'
Write-Host ''
Read-Host 'Enter 키를 누르면 창을 닫습니다'
