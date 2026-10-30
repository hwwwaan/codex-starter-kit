$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$kitRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$hookRoot = Join-Path $kitRoot 'plugins\smart-work-agent\hooks'

$parseTargets = @(
    (Join-Path $kitRoot '설치하기.ps1'),
    (Join-Path $kitRoot '설치확인.ps1')
) + @(Get-ChildItem -LiteralPath $hookRoot -Filter '*.ps1' | Select-Object -ExpandProperty FullName)

foreach ($path in $parseTargets) {
    $tokens = $null
    $errors = $null
    $null = [System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$tokens, [ref]$errors)
    if ($errors.Count -gt 0) {
        $messages = ($errors | ForEach-Object { $_.Message }) -join '; '
        throw "PowerShell 구문 오류: $path - $messages"
    }
}

function Invoke-Hook([string]$scriptName, [hashtable]$payload) {
    $scriptPath = Join-Path $hookRoot $scriptName
    $json = $payload | ConvertTo-Json -Depth 8 -Compress
    return $json | & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $scriptPath | Out-String
}

$promptResult = Invoke-Hook 'prompt-guard.ps1' @{
    prompt = '검사용 키 api_key=sk-test_12345678901234567890'
} | ConvertFrom-Json
if ($promptResult.decision -ne 'block') {
    throw '인증정보 차단 시나리오가 실패했습니다.'
}

function Test-PromptBlocked([string]$prompt) {
    $raw = Invoke-Hook 'prompt-guard.ps1' @{ prompt = $prompt }
    if ([string]::IsNullOrWhiteSpace($raw)) { return $false }
    return (($raw | ConvertFrom-Json).decision -eq 'block')
}

foreach ($prompt in @(
    '이 번호 900101-1234567 맞는지 봐 줘',
    '9001011234567 으로 조회해 줘',
    'Last run: 2026-10-16T21:03:52.334Z (9001011234567)'
)) {
    if (-not (Test-PromptBlocked $prompt)) {
        throw "주민등록번호 차단 시나리오가 실패했습니다: $prompt"
    }
}

$automationHeader = "Automation: 일일 리서치`nAutomation ID: drive`nLast run: {0}`n`n회차를 이어서 진행해 줘"
foreach ($lastRun in @('2026-10-16T21:03:52.334Z (1792184632334)', '2027-01-27T00:53:54.567Z (1801011234567)')) {
    if (Test-PromptBlocked ($automationHeader -f $lastRun)) {
        throw "자동화 머리말 통과 시나리오가 실패했습니다: $lastRun"
    }
}

$toolResult = Invoke-Hook 'tool-guard.ps1' @{
    tool_name = 'exec_command'
    tool_input = @{ cmd = 'git reset --hard' }
} | ConvertFrom-Json
if ($toolResult.hookSpecificOutput.permissionDecision -ne 'deny') {
    throw 'exec_command 위험 명령 차단 시나리오가 실패했습니다.'
}

$qualityResult = Invoke-Hook 'quality-stop.ps1' @{
    stop_hook_active = $false
    last_assistant_message = ('보고서 파일을 작성했습니다. ' * 12)
} | ConvertFrom-Json
if ($qualityResult.decision -ne 'block') {
    throw '최종 품질감사 시나리오가 실패했습니다.'
}

$sessionResult = Invoke-Hook 'session-start.ps1' @{} | ConvertFrom-Json
if ($sessionResult.hookSpecificOutput.hookEventName -ne 'SessionStart') {
    throw '세션 시작 맥락 주입 시나리오가 실패했습니다.'
}

Write-Host 'PASS: Windows PowerShell 구문과 핵심 훅 9개 시나리오' -ForegroundColor Green
