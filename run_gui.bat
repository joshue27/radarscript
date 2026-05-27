@echo off
REM Lanzador de RadarScript GUI con el Python del entorno virtual
cd /d "%~dp0"
.venv\Scripts\python gui.py
pause
