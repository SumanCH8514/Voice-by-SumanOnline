@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" -m voice_by_sumanonline.main --ui
) else (
    start "" pythonw -m voice_by_sumanonline.main --ui
)
exit
