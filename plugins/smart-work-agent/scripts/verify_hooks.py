#!/usr/bin/env python3
"""Python 훅의 허용·차단·맥락 주입 동작을 재현해 검사한다."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


HOOK_ROOT = Path(__file__).resolve().parents[1] / "hooks"


def invoke(name: str, payload: dict) -> dict | None:
    result = subprocess.run(
        [sys.executable, str(HOOK_ROOT / name)],
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(f"{name} 실행 실패: {result.stderr.strip()}")
    if not result.stdout.strip():
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"{name}이 올바르지 않은 JSON을 출력했습니다: {result.stdout}") from exc


def assert_blocked(payload: dict | None, label: str) -> None:
    if not payload:
        raise AssertionError(f"{label}: 차단 결과가 없습니다.")
    if payload.get("decision") == "block":
        return
    permission = payload.get("hookSpecificOutput", {}).get("permissionDecision")
    if permission != "deny":
        raise AssertionError(f"{label}: 차단되지 않았습니다: {payload}")


def assert_passed(payload: dict | None, label: str) -> None:
    if not payload:
        return
    if payload.get("decision") == "block" or payload.get("hookSpecificOutput", {}).get("permissionDecision") == "deny":
        raise AssertionError(f"{label}: 막지 않아야 할 요청을 막았습니다: {payload}")


def main() -> int:
    session = invoke("session-start.py", {"source": "startup"})
    assert session and session["hookSpecificOutput"]["hookEventName"] == "SessionStart"

    assert invoke("prompt-guard.py", {"prompt": "회의록을 요약해 줘"}) is None
    assert_blocked(
        invoke("prompt-guard.py", {"prompt": "api_key=sk-abcdefghijklmnopqrstuv"}),
        "인증정보",
    )
    assert_blocked(
        invoke("prompt-guard.py", {"prompt": "첨부한 사례관리기록 파일을 분석해 줘"}),
        "민감기록",
    )
    current = invoke("prompt-guard.py", {"prompt": "현재 지역 복지 정책을 확인해 줘"})
    assert current and current["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"

    for label, prompt in (
        ("주민등록번호", "이 번호 900101-1234567 맞는지 봐 줘"),
        ("붙여 쓴 주민등록번호", "9001011234567 으로 조회해 줘"),
        ("띄어 쓴 주민등록번호", "040229 - 3123456"),
        ("시각과 맞지 않는 괄호 속 번호", "Last run: 2026-10-16T21:03:52.334Z (9001011234567)"),
    ):
        assert_blocked(invoke("prompt-guard.py", {"prompt": prompt}), label)
    automation_header = (
        "Automation: 일일 리서치\nAutomation ID: drive\n"
        "Automation memory: $CODEX_HOME/automations/drive/memory.md\n"
        "Last run: {}\n\n회차를 이어서 진행해 줘"
    )
    for label, last_run in (
        ("자동화 머리말", "2026-10-16T21:03:52.334Z (1792184632334)"),
        ("생년월일처럼 보이는 자동화 머리말", "2027-01-27T00:53:54.567Z (1801011234567)"),
    ):
        assert_passed(invoke("prompt-guard.py", {"prompt": automation_header.format(last_run)}), label)
    assert_blocked(
        invoke(
            "prompt-guard.py",
            {"prompt": automation_header.format("2026-10-16T21:03:52.334Z (1792184632334)") + " 900101-1234567"},
        ),
        "자동화 머리말 뒤 주민등록번호",
    )
    assert_passed(invoke("prompt-guard.py", {"prompt": "주문번호 901301-1234567 배송 조회"}), "월이 13인 번호")

    assert invoke("tool-guard.py", {"tool_name": "exec_command", "tool_input": {"cmd": "ls"}}) is None
    assert_blocked(
        invoke("tool-guard.py", {"tool_name": "exec_command", "tool_input": {"cmd": "git reset --hard"}}),
        "위험 명령",
    )
    assert_blocked(
        invoke("tool-guard.py", {"tool_name": "mcp__mail__send_message", "tool_input": {}}),
        "외부 전송",
    )

    neutral = invoke("quality-stop.py", {"last_assistant_message": "설명을 마쳤습니다."})
    assert neutral == {"continue": True}
    assert_blocked(
        invoke("quality-stop.py", {"last_assistant_message": "보고서.md 파일을 작성했습니다."}),
        "완료 전 감사",
    )
    reentry = invoke(
        "quality-stop.py",
        {"last_assistant_message": "보고서.md 파일을 작성했습니다.", "stop_hook_active": True},
    )
    assert reentry == {"continue": True}

    print("PASS: Python 훅 19개 시나리오")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
