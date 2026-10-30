#!/usr/bin/env python3
"""복구하기 어려운 명령과 외부 변경 도구를 실행 전에 차단한다."""

from __future__ import annotations

import json
import re
import sys


DANGEROUS_PATTERNS = [
    r"\bgit\s+reset\s+--hard\b",
    r"\bgit\s+clean\s+-[^\s]*f",
    r"\bRemove-Item\b[^\r\n]*-Recurse\b",
    r"\brm(?:\.exe)?\s+-[^\s]*r",
    r"\b(?:rmdir|rd)\b[^\r\n]*/s\b",
    r"\bdel\b[^\r\n]*/s\b",
    r"\b(?:Format-Volume|Clear-Disk|Initialize-Disk|diskpart|cipher\s+/w)\b",
    r"\b(?:shutdown|Stop-Computer|Restart-Computer)\b",
]
EXTERNAL_ACTION = re.compile(
    r"^mcp__.*__(send|publish|submit|payment|trade|purchase|share|invite|delete|remove|trash|purge|destroy|wipe|upload|post|create_comment|update_permission)(?:$|_)",
    re.IGNORECASE,
)


def deny(reason: str) -> None:
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        return

    tool_name = str(payload.get("tool_name") or "")
    tool_input = payload.get("tool_input") or {}
    command = ""
    if isinstance(tool_input, dict):
        command = str(tool_input.get("command") or tool_input.get("cmd") or "")

    if tool_name in {"Bash", "exec_command"} and command:
        if any(re.search(pattern, command, re.IGNORECASE) for pattern in DANGEROUS_PATTERNS):
            deny(
                "복구하기 어려운 광범위 삭제 또는 시스템 변경 명령을 차단했습니다. 정확한 대상과 복구 방법을 확인한 뒤 더 좁고 안전한 작업으로 다시 계획하세요."
            )
            return

    if EXTERNAL_ACTION.search(tool_name):
        deny(
            "외부 전송·공개·결제·권한 변경·삭제 도구는 이 스타터 키트에서 실행하지 않습니다. 필요한 내용과 파일을 준비한 뒤 실제 외부 행동은 사용자가 직접 수행하세요."
        )


if __name__ == "__main__":
    main()
