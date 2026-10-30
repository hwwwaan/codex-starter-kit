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

$toolName = [string]$inputObject.tool_name
$command = ''
if ($null -ne $inputObject.tool_input -and $null -ne $inputObject.tool_input.command) {
    $command = [string]$inputObject.tool_input.command
} elseif ($null -ne $inputObject.tool_input -and $null -ne $inputObject.tool_input.cmd) {
    $command = [string]$inputObject.tool_input.cmd
}

function Deny-ToolCall([string]$reason) {
    @{
        hookSpecificOutput = @{
            hookEventName = 'PreToolUse'
            permissionDecision = 'deny'
            permissionDecisionReason = $reason
        }
    } | ConvertTo-Json -Depth 6 -Compress
    exit 0
}

if ($toolName -in @('Bash', 'exec_command') -and -not [string]::IsNullOrWhiteSpace($command)) {
    $dangerousPatterns = @(
        '(?i)\bgit\s+reset\s+--hard\b',
        '(?i)\bgit\s+clean\s+-[^\s]*f',
        '(?i)\bRemove-Item\b[^\r\n]*-Recurse\b',
        '(?i)\brm(?:\.exe)?\s+-[^\s]*r',
        '(?i)\b(?:rmdir|rd)\b[^\r\n]*\/s\b',
        '(?i)\bdel\b[^\r\n]*\/s\b',
        '(?i)\b(?:Format-Volume|Clear-Disk|Initialize-Disk|diskpart|cipher\s+\/w)\b',
        '(?i)\b(?:shutdown|Stop-Computer|Restart-Computer)\b'
    )

    foreach ($pattern in $dangerousPatterns) {
        if ($command -match $pattern) {
            Deny-ToolCall '복구하기 어려운 광범위 삭제 또는 시스템 변경 명령을 차단했습니다. 정확한 대상과 복구 방법을 확인한 뒤 더 좁고 안전한 작업으로 다시 계획하세요.'
        }
    }
}

if ($toolName -match '(?i)^mcp__.*__(send|publish|submit|payment|trade|purchase|share|invite|delete|remove|trash|purge|destroy|wipe|upload|post|create_comment|update_permission)') {
    Deny-ToolCall '외부 전송·공개·결제·권한 변경·삭제 도구는 이 스타터 키트에서 실행하지 않습니다. 필요한 내용과 파일을 준비한 뒤 실제 외부 행동은 사용자가 직접 수행하세요.'
}
