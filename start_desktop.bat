@echo off
cd /d "%~dp0"
set "UV_EXE="
if exist "%USERPROFILE%\.local\bin\uv.exe" (
    set "UV_EXE=%USERPROFILE%\.local\bin\uv.exe"
) else if exist "%LOCALAPPDATA%\Programs\uv\uv.exe" (
    set "UV_EXE=%LOCALAPPDATA%\Programs\uv\uv.exe"
) else (
    for /f "delims=" %%I in ('where uv.exe 2^>nul') do if not defined UV_EXE set "UV_EXE=%%I"
)

if defined UV_EXE (
    start "" "%UV_EXE%" run pythonw -m voice_by_sumanonline.main --ui
) else if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" -m voice_by_sumanonline.main --ui
) else (
    start "" pythonw -m voice_by_sumanonline.main --ui
)
exit
