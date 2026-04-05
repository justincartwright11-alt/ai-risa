@echo off
REM run_upcoming_schedule_cadence.bat
REM Windows-safe launcher for upcoming schedule cadence runner

REM Set working directory to repo root
cd /d %~dp0

REM Call locked Python interpreter with cadence runner
set PYTHON_EXE=C:\Users\jusin\AppData\Local\Python\pythoncore-3.14-64\python.exe
set CADENCE_RUNNER=build_upcoming_schedule_cadence_runner.py

%PYTHON_EXE% %CADENCE_RUNNER%
set EXITCODE=%ERRORLEVEL%

REM Emit scheduler-launch artifact
set ARTIFACT_JSON=ops\events\upcoming_schedule_scheduler_launch.json
set ARTIFACT_MD=ops\events\upcoming_schedule_scheduler_launch.md

REM Write JSON artifact
> %ARTIFACT_JSON% echo {^
  "timestamp": "%date% %time%",^
  "launcher": "run_upcoming_schedule_cadence.bat",^
  "working_dir": "%CD%",^
  "python": "%PYTHON_EXE%",^
  "runner": "%CADENCE_RUNNER%",^
  "exit_code": %EXITCODE%^
}

REM Write Markdown artifact
> %ARTIFACT_MD% echo # Upcoming Schedule Scheduler Launcher
>> %ARTIFACT_MD% echo.
>> %ARTIFACT_MD% echo Run at: %date% %time%
>> %ARTIFACT_MD% echo Working directory: %CD%
>> %ARTIFACT_MD% echo Python: %PYTHON_EXE%
>> %ARTIFACT_MD% echo Runner: %CADENCE_RUNNER%
>> %ARTIFACT_MD% echo Exit code: %EXITCODE%

exit /b %EXITCODE%
