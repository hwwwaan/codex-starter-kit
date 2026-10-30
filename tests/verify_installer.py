#!/usr/bin/env python3
"""사용자 설정을 건드리지 않고 설치기의 상태별 동작을 검사한다."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True


KIT_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = KIT_ROOT / "설치하기.py"


def load_installer():
    spec = importlib.util.spec_from_file_location("installer", INSTALLER)
    if not spec or not spec.loader:
        raise AssertionError("설치기 모듈을 불러오지 못했습니다.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def completed(payload: dict) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["codex"], 0, json.dumps(payload), "")


def exercise(*, marketplace_root: Path | None, installed: bool, replace: bool = False):
    module = load_installer()
    calls: list[tuple[str, ...]] = []

    def fake_run(_codex: str, *args: str, check: bool = True):
        del check
        calls.append(args)
        if args == ("marketplace", "list", "--json"):
            items = [] if marketplace_root is None else [{"name": module.MARKETPLACE_NAME, "root": str(marketplace_root)}]
            return completed({"marketplaces": items})
        if args == ("list", "--json"):
            items = []
            if installed:
                items.append({"name": module.PLUGIN_NAME, "marketplaceName": module.MARKETPLACE_NAME})
            return completed({"installed": items})
        return completed({"ok": True})

    argv = [str(INSTALLER)] + (["--replace-existing"] if replace else [])
    with (
        mock.patch.object(module.shutil, "which", return_value="/mock/codex"),
        mock.patch.object(module, "run", side_effect=fake_run),
        mock.patch.object(sys, "argv", argv),
        contextlib.redirect_stdout(io.StringIO()),
    ):
        module.main()
    return calls


def main() -> int:
    fresh = exercise(marketplace_root=None, installed=False)
    assert ("marketplace", "add", str(KIT_ROOT), "--json") in fresh
    assert ("add", "smart-work-agent@codex-starter-kit", "--json") in fresh
    assert not any("remove" in call for call in fresh)

    existing = exercise(marketplace_root=KIT_ROOT, installed=True)
    assert not any("remove" in call for call in existing)
    assert not any(call and call[0] == "add" for call in existing)

    module = load_installer()
    try:
        exercise(marketplace_root=Path("/private/tmp/old-marketplace"), installed=False)
    except RuntimeError as exc:
        assert "기존 상태를 보존했습니다" in str(exc)
    else:
        raise AssertionError("다른 경로의 기존 마켓플레이스를 기본 설치가 보존하지 않았습니다.")

    replaced = exercise(
        marketplace_root=Path("/private/tmp/old-marketplace"),
        installed=True,
        replace=True,
    )
    assert ("remove", "smart-work-agent@codex-starter-kit", "--json") in replaced
    assert ("marketplace", "remove", "codex-starter-kit", "--json") in replaced

    print("PASS: 설치기 4개 상태 시나리오")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
