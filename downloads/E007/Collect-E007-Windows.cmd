@echo off
setlocal
where adb.exe >nul 2>&1
if errorlevel 1 (
  echo Put this folder on the platform-tools command path, or run the README commands from platform-tools.
  pause
  exit /b 1
)
adb push "%~dp0check-e007.sh" /data/local/tmp/check-e007.sh
if errorlevel 1 exit /b 1
adb shell sh /data/local/tmp/check-e007.sh > "%~dp0E007-check.txt"
if errorlevel 1 exit /b 1
echo Saved E007-check.txt. Rename it for the profile tested before running again.
pause
