#!/usr/bin/env python3
"""세션 시작 시 공통 업무 기준을 주입한다."""

from __future__ import annotations

import json
import sys


def main() -> None:
    sys.stdin.read()
    context = (
        "스마트 업무 기준을 적용한다. 실질적인 요청은 자료 목록화, 결론에 영향을 주는 "
        "원문 전체 확인, 사실·해석·가설·제안 분리, 반증 탐색, 실행, 결과 검증 순서로 처리한다. "
        "사용자가 기술을 몰라도 가능한 작업은 직접 수행한다. 최신 사실은 공식 원출처를 확인한다. "
        "원본을 덮어쓰지 않고, 외부 발송·제출·게시·결제·가입·권한 변경은 사용자가 실행한다. "
        "완성이라고 말하기 전에 범위, 근거, 수치, 충돌, 개인정보, 파일 존재와 형식을 다시 확인한다."
    )
    json.dump(
        {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}},
        sys.stdout,
        ensure_ascii=False,
        separators=(",", ":"),
    )


if __name__ == "__main__":
    main()
