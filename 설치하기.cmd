@echo off
chcp 65001 >nul
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0설치하기.ps1" %*
if errorlevel 1 (
  echo.
  echo 설치 중 오류가 발생했습니다. 위 메시지를 캡처해 전달해 주세요.
  pause
)
