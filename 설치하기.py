#!/usr/bin/env python3
"""로컬 마켓플레이스와 플러그인을 현재 Codex에 설치한다."""

from __future__ import annotations

import json
import argparse
import shutil
import subprocess
import sys
from pathlib import Path


MARKETPLACE_NAME = "codex-starter-kit"
PLUGIN_NAME = "smart-work-agent"
PLUGIN_ID = f"{PLUGIN_NAME}@{MARKETPLACE_NAME}"


def run(codex: str, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [codex, "plugin", *args],
        check=False,
        text=True,
        capture_output=True,
    )
    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(message or f"명령 실행 실패: codex plugin {' '.join(args)}")
    return result


def read_json(result: subprocess.CompletedProcess[str], label: str) -> dict:
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{label} 결과를 읽지 못했습니다: {exc}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="스마트 업무 에이전트를 설치합니다.")
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="같은 이름의 기존 플러그인 또는 다른 경로의 마켓플레이스를 확인 후 교체합니다.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    kit_root = Path(__file__).resolve().parent
    marketplace_file = kit_root / ".agents" / "plugins" / "marketplace.json"
    plugin_manifest = kit_root / "plugins" / PLUGIN_NAME / ".codex-plugin" / "plugin.json"

    for required in (marketplace_file, plugin_manifest):
        if not required.is_file():
            raise RuntimeError(f"설치 파일을 찾지 못했습니다: {required}")

    try:
        plugin_version = json.loads(plugin_manifest.read_text(encoding="utf-8"))["version"]
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"플러그인 버전을 읽지 못했습니다: {exc}") from exc

    codex = shutil.which("codex")
    if not codex:
        raise RuntimeError("Codex 명령을 찾지 못했습니다. Codex 앱을 최신 버전으로 설치해 주세요.")

    print("스마트 업무 에이전트 설치를 시작합니다.")
    print("1/4 설치 파일과 Codex CLI를 확인했습니다.")

    marketplaces = read_json(run(codex, "marketplace", "list", "--json"), "마켓플레이스 목록")
    existing_marketplace = next(
        (item for item in marketplaces.get("marketplaces", []) if item.get("name") == MARKETPLACE_NAME),
        None,
    )

    plugins = read_json(run(codex, "list", "--json"), "플러그인 목록")
    installed = any(
        item.get("name") == PLUGIN_NAME and item.get("marketplaceName") == MARKETPLACE_NAME
        for item in plugins.get("installed", [])
    )
    if installed and args.replace_existing:
        run(codex, "remove", PLUGIN_ID, "--json")
        print("2/4 사용자가 교체를 요청해 기존 플러그인 캐시를 정리했습니다.")
    elif installed:
        print("2/4 같은 플러그인이 이미 설치되어 있어 기존 상태를 유지합니다.")
    else:
        print("2/4 기존 설치가 없어 새로 설치합니다.")

    expected_root = kit_root.resolve()
    if existing_marketplace:
        current_root = Path(str(existing_marketplace.get("root", ""))).expanduser().resolve()
        if current_root != expected_root:
            if not args.replace_existing:
                raise RuntimeError(
                    "같은 이름의 마켓플레이스가 다른 경로에 있습니다. 기존 상태를 보존했습니다. "
                    "경로를 확인한 뒤 교체하려면 --replace-existing을 명시하세요."
                )
            run(codex, "marketplace", "remove", MARKETPLACE_NAME, "--json")
            existing_marketplace = None

    if existing_marketplace is None:
        run(codex, "marketplace", "add", str(kit_root), "--json")
        print("3/4 현재 폴더를 로컬 마켓플레이스로 등록했습니다.")
    else:
        print("3/4 로컬 마켓플레이스 경로가 현재 폴더와 일치합니다.")

    if installed and not args.replace_existing:
        print("4/4 기존 스마트 업무 에이전트를 그대로 사용합니다.")
    else:
        run(codex, "add", PLUGIN_ID, "--json")
        print(f"4/4 스마트 업무 에이전트 {plugin_version}을 설치했습니다.")
    print("Codex 앱을 완전히 종료했다가 다시 열고 새 작업을 시작하세요.")
    print("훅 검토 알림이 나오면 내용을 확인한 뒤 신뢰해 주세요.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"설치 실패: {exc}", file=sys.stderr)
        raise SystemExit(1)
