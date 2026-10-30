$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$codexCommand = Get-Command codex -ErrorAction SilentlyContinue
if ($null -eq $codexCommand) {
    Write-Host 'FAIL: Codex 명령을 찾지 못했습니다.' -ForegroundColor Red
    exit 1
}

$raw = & $codexCommand.Source plugin list --json 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) {
    Write-Host 'FAIL: 플러그인 상태를 읽지 못했습니다.' -ForegroundColor Red
    Write-Host $raw
    exit 1
}

try {
    $pluginList = $raw | ConvertFrom-Json
} catch {
    Write-Host 'FAIL: 플러그인 목록 형식이 올바르지 않습니다.' -ForegroundColor Red
    exit 1
}

$plugin = @($pluginList.installed | Where-Object {
    $_.name -eq 'smart-work-agent' -and $_.marketplaceName -eq 'codex-starter-kit'
}) | Select-Object -First 1

if ($null -eq $plugin) {
    Write-Host 'FAIL: 스마트 업무 에이전트를 찾지 못했습니다. 설치하기.cmd를 실행하세요.' -ForegroundColor Red
    exit 1
}
if (-not $plugin.enabled) {
    Write-Host 'FAIL: 스마트 업무 에이전트가 설치되어 있지만 비활성 상태입니다.' -ForegroundColor Red
    exit 1
}

$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME '.codex' }
$configPath = Join-Path $codexHome 'config.toml'
if (-not (Test-Path -LiteralPath $configPath)) {
    Write-Host "FAIL: 훅 신뢰 설정을 찾지 못했습니다: $configPath" -ForegroundColor Red
    exit 1
}

$configRaw = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8
$hookStateKeys = @(
    'smart-work-agent@codex-starter-kit:hooks/hooks.json:pre_tool_use:0:0',
    'smart-work-agent@codex-starter-kit:hooks/hooks.json:session_start:0:0',
    'smart-work-agent@codex-starter-kit:hooks/hooks.json:user_prompt_submit:0:0',
    'smart-work-agent@codex-starter-kit:hooks/hooks.json:stop:0:0'
)
$missingHooks = @()
foreach ($key in $hookStateKeys) {
    $pattern = '(?m)^\[hooks\.state\."' + [regex]::Escape($key) + '"\]\s*\r?\ntrusted_hash\s*=\s*"sha256:[0-9a-f]{64}"\s*$'
    if ($configRaw -notmatch $pattern) {
        $missingHooks += $key
    }
}
if ($missingHooks.Count -gt 0) {
    Write-Host 'FAIL: 아직 신뢰하지 않은 플러그인 훅이 있습니다.' -ForegroundColor Red
    $missingHooks | ForEach-Object { Write-Host "- $_" }
    Write-Host 'Codex에서 훅 검토 화면을 열어 코드를 확인한 뒤 신뢰하세요.'
    exit 1
}

Write-Host "PASS: 스마트 업무 에이전트 $($plugin.version)이 활성화되어 있습니다." -ForegroundColor Green
Write-Host 'PASS: 플러그인 훅 4개에 신뢰 기록이 있습니다.' -ForegroundColor Green
Write-Host '새 작업에서 스킬과 훅을 사용할 수 있습니다.'
exit 0
