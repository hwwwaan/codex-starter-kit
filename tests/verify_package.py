#!/usr/bin/env python3
"""배포본의 버전·마켓플레이스·스킬·훅·설치 경로를 한 번에 검사한다."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True


KIT_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = KIT_ROOT / "plugins" / "smart-work-agent"
EXPECTED_SKILLS = {
    "data-insight",
    "decision-support",
    "evidence-research",
    "field-interview-to-evidence",
    "meeting-to-action",
    "professional-deliverable",
    "quality-audit",
    "team-context-manager",
    "work-orchestrator",
}
EXPECTED_HOOKS = {
    "SessionStart": "session-start",
    "UserPromptSubmit": "prompt-guard",
    "PreToolUse": "tool-guard",
    "Stop": "quality-stop",
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def assert_skill(skill_dir: Path) -> None:
    skill_name = skill_dir.name
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = text.split("---", 2)[1]
    assert re.search(rf"(?m)^name:\s*['\"]?{re.escape(skill_name)}['\"]?\s*$", frontmatter)

    yaml_text = (skill_dir / "agents" / "openai.yaml").read_text(encoding="utf-8")
    assert f"${skill_name}" in yaml_text
    assert re.search(r"(?m)^\s*allow_implicit_invocation:\s*true\s*$", yaml_text)
    short_description = re.search(
        r'(?m)^\s*short_description:\s*["\'](.+)["\']\s*$', yaml_text
    )
    assert short_description, f"short_description 없음: {skill_name}"
    assert 25 <= len(short_description.group(1)) <= 64, f"short_description 길이 오류: {skill_name}"


def main() -> int:
    manifest = read_json(PLUGIN_ROOT / ".codex-plugin" / "plugin.json")
    version_line = (KIT_ROOT / "VERSION.txt").read_text(encoding="utf-8").splitlines()[0]
    assert manifest["name"] == "smart-work-agent"
    assert version_line.endswith(manifest["version"])

    current_marketplace = read_json(KIT_ROOT / ".agents" / "plugins" / "marketplace.json")
    compatibility_marketplace = read_json(KIT_ROOT / "marketplace.json")
    assert current_marketplace == compatibility_marketplace
    assert current_marketplace["name"] == "codex-starter-kit"
    assert current_marketplace["plugins"][0]["name"] == manifest["name"]
    assert current_marketplace["plugins"][0]["source"]["path"] == "./plugins/smart-work-agent"

    skills_root = PLUGIN_ROOT / "skills"
    skill_dirs = {path.name for path in skills_root.iterdir() if path.is_dir()}
    assert skill_dirs == EXPECTED_SKILLS
    for skill_name in sorted(EXPECTED_SKILLS):
        assert_skill(skills_root / skill_name)

    field_skill = skills_root / "field-interview-to-evidence"
    for relative in (
        "references/interview-protocol.md",
        "references/evidence-conversion.md",
        "assets/interview-record-template.md",
    ):
        assert (field_skill / relative).is_file(), f"현장 인터뷰 스킬 자료 없음: {relative}"

    hooks = read_json(PLUGIN_ROOT / "hooks" / "hooks.json")["hooks"]
    assert set(hooks) == set(EXPECTED_HOOKS)
    for event_name, stem in EXPECTED_HOOKS.items():
        hook = hooks[event_name][0]["hooks"][0]
        assert f"hooks/{stem}.py" in hook["command"]
        assert f"hooks\\{stem}.ps1" in hook["commandWindows"]
        assert (PLUGIN_ROOT / "hooks" / f"{stem}.py").is_file()
        assert (PLUGIN_ROOT / "hooks" / f"{stem}.ps1").is_file()

    windows_installer = (KIT_ROOT / "설치하기.ps1").read_text(encoding="utf-8-sig")
    assert "[switch]$ReplaceExisting" in windows_installer
    assert "if (-not $ReplaceExisting)" in windows_installer
    assert ".agents\\plugins\\marketplace.json" in windows_installer
    assert '%*' in (KIT_ROOT / "설치하기.cmd").read_text(encoding="utf-8-sig")
    assert '"$@"' in (KIT_ROOT / "설치하기.sh").read_text(encoding="utf-8")

    windows_checker = (KIT_ROOT / "설치확인.ps1").read_text(encoding="utf-8-sig")
    assert "$env:CODEX_HOME" in windows_checker
    assert all(key in windows_checker for key in ("pre_tool_use", "session_start", "user_prompt_submit", "stop"))

    python_prompt_guard = (PLUGIN_ROOT / "hooks" / "prompt-guard.py").read_text(encoding="utf-8")
    windows_prompt_guard = (PLUGIN_ROOT / "hooks" / "prompt-guard.ps1").read_text(encoding="utf-8-sig")
    for python_name, windows_name in (
        ("RESIDENT_NUMBER_PATTERN", "$residentNumberPattern"),
        ("TIMESTAMP_WITH_EPOCH_MS", "$timestampWithEpochMs"),
    ):
        pattern = re.search(rf'(?m)^{python_name} = r"(.+)"$', python_prompt_guard)
        assert pattern, f"Python 훅 정규식 없음: {python_name}"
        assert f"{windows_name} = '{pattern.group(1)}'" in windows_prompt_guard, f"Windows 훅 정규식이 다름: {python_name}"

    windows_tool_guard = (PLUGIN_ROOT / "hooks" / "tool-guard.ps1").read_text(encoding="utf-8-sig")
    assert "$inputObject.tool_input.cmd" in windows_tool_guard
    assert "@('Bash', 'exec_command')" in windows_tool_guard
    assert (KIT_ROOT / "tests" / "verify_windows.ps1").is_file()

    if os.name != "nt":
        for relative in ("설치하기.sh", "설치확인.sh", "설치하기.py", "설치확인.py"):
            assert os.access(KIT_ROOT / relative, os.X_OK), f"실행 권한 없음: {relative}"

    unwanted = [
        path for path in KIT_ROOT.rglob("*")
        if path.name.startswith("._") or path.name == "__pycache__" or path.suffix == ".pyc"
    ]
    assert not unwanted, f"불필요한 메타데이터: {unwanted}"

    print("PASS: 배포 구조·버전·스킬·훅·설치 경로")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
