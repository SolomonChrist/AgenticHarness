@echo off
setlocal
if "%~1"=="" goto config
if "%~2"=="" goto usage
py "%~dp0folder_mirror.py" --left "%~1" --right "%~2"
goto end
:config
if exist "%~dp0mirror_config.local.json" (
  py "%~dp0folder_mirror.py" --config "%~dp0mirror_config.local.json"
  goto end
)
echo No mirror_config.local.json found. Run setup first:
echo py "%~dp0setup_folder_mirror.py"
goto end
:usage
echo Usage: start_folder_mirror.bat "C:\path\to\AgenticHarness" "G:\My Drive\AgenticHarness_Mirror"
echo Or run without arguments after setup_folder_mirror.py creates mirror_config.local.json.
:end
