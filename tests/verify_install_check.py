#!/usr/bin/env python3
"""설치 확인기가 플러그인과 훅 신뢰 상태를 함께 판정하는지 검사한다."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True


KIT_ROOT = Path(__file__).resolve().parents[1]
CHECKER = KIT_ROOT / "설치확인.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("install_check", CHECKER)
    if not spec or not spec.loader:
        raise AssertionError("설치 확인기 모듈을 불러오지 못했습니다.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_case(*, enabled: bool = True, trusted_hooks: int = 4, valid_json: bool = True):
    module = load_checker()
    payload = {
        "installed": [
            {
                "name": "smart-work-agent",
                "marketplaceName": "codex-starter-kit",
                "version": "1.1.3",
                "enabled": enabled,
            }
        ]
    }
    stdout = json.dumps(payload) if valid_json else "not-json"
    completed = subprocess.CompletedProcess(["codex"], 0, stdout, "")

    with tempfile.TemporaryDirectory(prefix="install-check-") as temp_dir:
        codex_home = Path(temp_dir)
        states = []
        for key in module.HOOK_STATE_KEYS[:trusted_hooks]:
            states.append(f'[hooks.state."{key}"]\ntrusted_hash = "sha256:{"a" * 64}"\n')
        (codex_home / "config.toml").write_text("\n".join(states), encoding="utf-8")

        output = io.StringIO()
        with (
            mock.patch.object(module.shutil, "which", return_value="/mock/codex"),
            mock.patch.object(module.subprocess, "run", return_value=completed),
            mock.patch.dict(os.environ, {"CODEX_HOME": str(codex_home)}),
            contextlib.redirect_stdout(output),
        ):
            result = module.main()
        return result, output.getvalue()


def main() -> int:
    result, output = run_case()
    assert result == 0
    assert "훅 4개에 신뢰 기록" in output

    result, output = run_case(trusted_hooks=3)
    assert result == 1
    assert "신뢰하지 않은 플러그인 훅" in output

    result, output = run_case(enabled=False)
    assert result == 1
    assert "비활성 상태" in output

    result, output = run_case(valid_json=False)
    assert result == 1
    assert "목록 형식" in output

    print("PASS: 설치 확인기 4개 상태 시나리오")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
