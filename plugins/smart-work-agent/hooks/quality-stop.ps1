$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) {
    @{ continue = $true } | ConvertTo-Json -Compress
    exit 0
}

try {
    $inputObject = $raw | ConvertFrom-Json
} catch {
    @{ continue = $true } | ConvertTo-Json -Compress
    exit 0
}

if ($inputObject.stop_hook_active -eq $true) {
    @{ continue = $true } | ConvertTo-Json -Compress
    exit 0
}

$message = [string]$inputObject.last_assistant_message
$claimsFileDelivery = $message -match '(?i)(\.(docx|pptx|xlsx|pdf|md|hwp|hwpx|csv|zip)|파일[^\r\n]{0,40}(작성|생성|수정|저장|완료))'
$claimsCompletion = $message -match '(완료했습니다|완성했습니다|작성했습니다|생성했습니다|수정했습니다|저장했습니다|검증했습니다|인도합니다)'
$isClearlyWaiting = $message -match '(승인해|알려\s*주시면|선택해|확인이 필요합니다\s*$|질문드립니다\s*$)'
$shouldAudit = $claimsFileDelivery -or ($claimsCompletion -and $message.Length -ge 120)

if ($shouldAudit -and -not $isClearlyWaiting) {
    @{
        decision = 'block'
        reason = '최종 인도 전 독립 감사 1회를 수행하세요. 사용자 요청의 전체 범위, 실제 원문 확인 범위, 주장·수치·출처, 기존 자료와의 충돌, 반증과 예외, 개인정보·내부 흔적, 생성 파일의 존재·열림·형식을 확인하십시오. 발견한 결함은 직접 고친 뒤 검증 근거와 남은 불확실성만 간결하게 보고하세요.'
    } | ConvertTo-Json -Depth 4 -Compress
    exit 0
}

@{ continue = $true } | ConvertTo-Json -Compress
