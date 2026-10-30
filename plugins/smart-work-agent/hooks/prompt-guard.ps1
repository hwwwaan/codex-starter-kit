$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }

try {
    $inputObject = $raw | ConvertFrom-Json
} catch {
    exit 0
}

$prompt = [string]$inputObject.prompt
if ([string]::IsNullOrWhiteSpace($prompt)) { exit 0 }

$secretPatterns = @(
    '(?i)\bsk-[a-z0-9_-]{16,}\b',
    '(?i)\bgh[pousr]_[a-z0-9]{20,}\b',
    '(?i)\bAKIA[0-9A-Z]{16}\b',
    '(?i)\bAIza[0-9A-Za-z_-]{35}\b',
    '(?i)\bxox[baprs]-[0-9A-Za-z-]{10,}\b',
    '(?i)\beyJ[0-9A-Za-z_-]{10,}\.[0-9A-Za-z_-]{10,}\.[0-9A-Za-z_-]{10,}\b',
    '(?i)-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    '(?i)\bBearer\s+[0-9A-Za-z._~-]{20,}\b',
    '(?i)(api[_ -]?key|access[_ -]?token|secret[_ -]?key|client[_ -]?secret|password|비밀번호|인증키)\s*[:=]\s*[^\s]{8,}'
)

# 주민등록번호는 앞 6자리가 생년월일(월 01~12, 일 01~31)이고 뒷자리가 성별 숫자 1~4로 시작한다.
# 2020년 10월 이후 번호는 끝자리 검증식이 맞지 않으므로 검증식으로 거르지 않는다.
$residentNumberPattern = '(?<!\d)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\s*[- ]?\s*[1-4]\d{6}(?!\d)'

# Codex 자동화는 프롬프트 머리에 `Last run: 2026-10-16T21:03:52.334Z (1792184632334)`를 붙인다.
# 괄호 속 13자리가 바로 앞 UTC 시각의 밀리초 값과 정확히 같을 때만 시각 표기로 보고 주민등록번호 검사에서 뺀다.
$timestampWithEpochMs = '((\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,9}))?Z)\s*\((\d{13})\)'

$dropEpochMs = [System.Text.RegularExpressions.MatchEvaluator]{
    param($found)
    try {
        $millisecond = [int](($found.Groups[8].Value + '000').Substring(0, 3))
        $moment = [DateTimeOffset]::new(
            [int]$found.Groups[2].Value, [int]$found.Groups[3].Value, [int]$found.Groups[4].Value,
            [int]$found.Groups[5].Value, [int]$found.Groups[6].Value, [int]$found.Groups[7].Value,
            $millisecond, [TimeSpan]::Zero)
        if ($moment.ToUnixTimeMilliseconds() -eq [int64]$found.Groups[9].Value) {
            return $found.Groups[1].Value
        }
    } catch {
    }
    return $found.Value
}

$secretFound = [regex]::Replace($prompt, $timestampWithEpochMs, $dropEpochMs) -match $residentNumberPattern
foreach ($pattern in $secretPatterns) {
    if ($prompt -match $pattern) { $secretFound = $true }
}

if ($secretFound) {
    @{
        decision = 'block'
        reason = '민감정보 또는 인증정보로 보이는 값이 포함되어 전송을 차단했습니다. 해당 값을 삭제하거나 가린 뒤 다시 요청해 주세요. 원문 값을 채팅에 다시 붙이지 마세요.'
    } | ConvertTo-Json -Depth 4 -Compress
    exit 0
}

$sensitiveRecordRequest = (
    $prompt -match '(첨부|파일|문서|엑셀|PDF).{0,40}(상담기록|사례관리기록|진료기록|건강정보|주민등록번호|민감정보)' -or
    $prompt -match '(상담기록|사례관리기록|진료기록|건강정보|주민등록번호|민감정보).{0,40}(첨부|파일|문서|엑셀|PDF)'
) -and $prompt -match '(분석|읽|정리|검토|요약|가공|작성)'

if ($sensitiveRecordRequest) {
    @{
        decision = 'block'
        reason = '민감한 상담·사례·건강·개인식별 기록이 포함된 파일 요청을 차단했습니다. 이름, 연락처, 주민등록번호와 상세 식별정보를 제거한 비식별 사본을 만든 뒤 다시 요청해 주세요.'
    } | ConvertTo-Json -Depth 4 -Compress
    exit 0
}

$contextParts = [System.Collections.Generic.List[string]]::new()

if ($prompt -match '(최신|현재|오늘|요즘|현행|최근|지금|가격|일정|법령|정책|지침|통계)') {
    $contextParts.Add('이 요청에는 최신성이 달라질 수 있는 정보가 포함되어 있다. 기억이나 기존 요약으로 단정하지 말고 현재 공식 원출처를 확인하며, 확인 날짜와 출처를 결과 가까이에 표시한다.')
}

if ($prompt -match '(법률|법적|의료|진단|치료|투자|대출|세금|재무|개인정보|사례관리|상담기록)') {
    $contextParts.Add('고위험 또는 민감 영역이다. 일반 검토와 정보 제공의 범위를 명시하고, 민감정보를 최소화하며, 중요한 결론은 공식자료와 전문가 확인 필요성을 분리한다.')
}

if ($contextParts.Count -gt 0) {
    @{
        hookSpecificOutput = @{
            hookEventName = 'UserPromptSubmit'
            additionalContext = ($contextParts -join ' ')
        }
    } | ConvertTo-Json -Depth 5 -Compress
}
