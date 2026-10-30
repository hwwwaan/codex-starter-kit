# Codex Starter Kit

A ready-made Codex workspace for teams of non-developers. It started as a kit for a small project team whose members were new to Codex, so that they could hand it complex work without learning a terminal first. The working language of the kit is Korean.

## What is inside

- **A Codex plugin, `smart-work-agent`, with 9 skills:** work orchestration, evidence research, field interviews, meeting notes to action items, data checks, decision support, document writing, quality audit and team context.
- **4 hooks:** one sets shared work standards at session start, one blocks credentials and sensitive records in prompts, one stops hard-to-reverse commands and outside changes, and one asks for an independent quality check before work is reported as done.
- **A simple folder flow:** put files in `01_자료`, ask Codex in plain language, and read the result in `03_완성본`.
- **Installers and checks** for macOS and Windows, plus tests for the package structure, hooks and installers.

## Install

1. Unzip or clone this folder. You need the Codex CLI and Python 3.
2. On macOS, run `./설치하기.sh`. On Windows, double-click `설치하기.cmd`.
3. Quit Codex completely and open it again.
4. Open this folder in Codex.
5. When Codex asks you to review the hooks, read them and trust them.

Then start with [00_처음_읽기.md](00_처음_읽기.md) and the examples in [예제](예제).

## What has been tested

The four test scripts pass on macOS, and version 1.1.3 was installed with `codex plugin add` on a real Mac. The Windows scripts have not been run on a real Windows machine, so please treat them as untested there. Details are in [검증_기록.md](검증_기록.md).

The hooks catch common mistakes. They do not replace your own review of what goes into or out of Codex.

## 한국어 안내

Codex를 처음 쓰는 비개발자 팀이 복합 업무를 맡길 수 있도록 미리 구성한 작업공간입니다. 스킬 9개, 민감정보와 위험한 명령을 막고 완료 전에 검수하는 훅 4개, 맥·윈도우 설치기가 들어 있습니다. 설치와 사용법은 [00_처음_읽기.md](00_처음_읽기.md)를 보세요.

맥에서는 실제 설치까지 확인했고, 윈도우 스크립트는 실제 윈도우 기기에서 돌려 보지 못했습니다.

## License

MIT
