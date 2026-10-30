#!/usr/bin/env python3
"""플러그인의 설치·활성·버전을 확인한다."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib


HOOK_STATE_KEYS = (
    "smart-work-agent@codex-starter-kit:hooks/hooks.json:pre_tool_use:0:0",
    "smart-work-agent@codex-starter-kit:hooks/hooks.json:session_start:0:0",
    "smart-work-agent@codex-starter-kit:hooks/hooks.json:user_prompt_submit:0:0",
    "smart-work-agent@codex-starter-kit:hooks/hooks.json:stop:0:0",
)


def main() -> int:
    codex = shutil.which("codex")
    if not codex:
        print("FAIL: Codex 명령을 찾지 못했습니다.")
        return 1

    result = subprocess.run(
        [codex, "plugin", "list", "--json"],
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        print("FAIL: 플러그인 상태를 읽지 못했습니다.")
        print(result.stderr.strip() or result.stdout.strip())
        return 1

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        print(f"FAIL: 플러그인 목록 형식이 올바르지 않습니다: {exc}")
        return 1

    plugin = next(
        (
            item
            for item in payload.get("installed", [])
            if item.get("name") == "smart-work-agent"
            and item.get("marketplaceName") == "codex-starter-kit"
        ),
        None,
    )
    if not plugin:
        print("FAIL: 스마트 업무 에이전트를 찾지 못했습니다.")
        return 1
    if not plugin.get("enabled"):
        print("FAIL: 스마트 업무 에이전트가 설치되어 있지만 비활성 상태입니다.")
        return 1

    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    config_path = codex_home / "config.toml"
    try:
        with config_path.open("rb") as config_file:
            config = tomllib.load(config_file)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        print(f"FAIL: 훅 신뢰 설정을 읽지 못했습니다: {exc}")
        return 1

    hook_state = config.get("hooks", {}).get("state", {})
    missing_hooks = [
        key for key in HOOK_STATE_KEYS if not hook_state.get(key, {}).get("trusted_hash")
    ]
    if missing_hooks:
        print("FAIL: 아직 신뢰하지 않은 플러그인 훅이 있습니다.")
        for key in missing_hooks:
            print(f"- {key.rsplit(':', 3)[0]}")
        print("Codex에서 훅 검토 화면을 열어 코드를 확인한 뒤 신뢰하세요.")
        return 1

    print(f"PASS: 스마트 업무 에이전트 {plugin.get('version', '버전 미확인')}이 활성화되어 있습니다.")
    print("PASS: 플러그인 훅 4개에 신뢰 기록이 있습니다.")
    print("새 작업에서 스킬과 훅을 사용할 수 있습니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
