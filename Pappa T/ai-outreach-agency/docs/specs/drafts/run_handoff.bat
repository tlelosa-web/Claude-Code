@echo off
REM run_handoff.bat
REM Triggers Claude Code headless mode for one lead's asset_gen/email_draft handoff.
REM Usage: run_handoff.bat <lead_id>

if "%~1"=="" (
    echo Usage: run_handoff.bat ^<lead_id>
    exit /b 1
)

set LEAD_ID=%~1
set HANDOFF_DIR=handoff
set INPUT_FILE=%HANDOFF_DIR%\lead_%LEAD_ID%.md
set OUTPUT_FILE=%HANDOFF_DIR%\output_%LEAD_ID%.md
set RESULT_FILE=%HANDOFF_DIR%\result_%LEAD_ID%.json

if not exist "%INPUT_FILE%" (
    echo ERROR: %INPUT_FILE% not found.
    exit /b 1
)

echo Running headless handoff for lead %LEAD_ID%...

claude -p "Read %INPUT_FILE% and follow its instructions exactly. Write the completed asset and email draft to %OUTPUT_FILE%." --allowedTools "Read,Write" --output-format json > "%RESULT_FILE%"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: claude -p exited with code %ERRORLEVEL%. See %RESULT_FILE% for details.
    exit /b %ERRORLEVEL%
)

echo Done. Output: %OUTPUT_FILE%
echo Result log: %RESULT_FILE%
