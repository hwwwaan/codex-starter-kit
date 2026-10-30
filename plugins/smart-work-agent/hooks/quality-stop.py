#!/usr/bin/env python3
"""파일 인도나 완료 보고 전에 독립 품질감사를 한 번 요구한다."""

from __future__ import annotations

import json
import re
import sys


def emit(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, separators=(",", ":"))


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        emit({"continue": True})
        return

    if payload.get("stop_hook_active") is True:
        emit({"continue": True})
        return

    message = str(payload.get("last_assistant_message") or "")
    claims_file = re.search(
        r"\.(docx|pptx|xlsx|pdf|md|hwp|hwpx|csv|zip)|파일[^\r\n]{0,40}(작성|생성|수정|저장|완료)",
        message,
        re.IGNORECASE,
    )
    claims_completion = re.search(
        r"완료했습니다|완성했습니다|작성했습니다|생성했습니다|수정했습니다|저장했습니다|검증했습니다|인도합니다",
        message,
    )
    clearly_waiting = re.search(r"승인해|알려\s*주시면|선택해|확인이 필요합니다\s*$|질문드립니다\s*$", message)
    should_audit = bool(claims_file or (claims_completion and len(message) >= 120))

    if should_audit and not clearly_waiting:
        emit(
            {
                "decision": "block",
                "reason": "최종 인도 전 독립 감사 1회를 수행하세요. 사용자 요청의 전체 범위, 실제 원문 확인 범위, 주장·수치·출처, 기존 자료와의 충돌, 반증과 예외, 개인정보·내부 흔적, 생성 파일의 존재·열림·형식을 확인하십시오. 발견한 결함은 직접 고친 뒤 검증 근거와 남은 불확실성만 간결하게 보고하세요.",
            }
        )
        return

    emit({"continue": True})


if __name__ == "__main__":
    main()
