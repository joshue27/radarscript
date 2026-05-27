@echo off
REM ============================================================
REM  Asociar .obj de RadarScript en Windows
REM ============================================================
REM  Ejecutar UNA SOLA VEZ como Administrador para que
REM  los archivos .obj se abran automaticamente con
REM  RadarScript.exe (editor + VM) al hacer doble clic.
REM ============================================================

title Asociar .obj — RadarScript
cd /d "%~dp0"

echo.
echo  ========================================
echo    RadarScript — Asociar .obj
echo  ========================================
echo.
echo  Esto asocia los archivos .obj con
echo  RadarScript.exe.
echo.
echo  - .obj  → abre el dashboard de la MV
echo  - .rdr  → abre el editor (doble clic o
echo             arrastrar sobre el .exe)
echo.

REM --- Verificar que RadarScript.exe existe ---
if not exist "dist\RadarScript.exe" (
    echo  [ERROR] No se encuentra dist\RadarScript.exe
    echo  Ejecuta primero:  py -m PyInstaller RadarScript.spec
    pause
    exit /b 1
)

set "EXE=%~dp0dist\RadarScript.exe"
echo  [OK] Ejecutable: %EXE%
echo.

REM --- Registrar asociacion ---
echo  Asociando .obj con RadarScript.ObjFile ...
assoc .obj=RadarScript.ObjFile >nul 2>nul
if %errorlevel% neq 0 (
    echo  [ADVERTENCIA] No se pudo ejecutar ASSOC.
    echo  Ejecuta este batch COMO ADMINISTRADOR.
    pause
    exit /b 1
)

ftype RadarScript.ObjFile="%EXE%" "%%1" >nul 2>nul
if %errorlevel% neq 0 (
    echo  [ADVERTENCIA] No se pudo ejecutar FTYPE.
    pause
    exit /b 1
)

echo.
echo  ========================================
echo    Asociacion completada
echo  ========================================
echo.
echo  Ya podes hacer doble clic en cualquier
echo  archivo .obj de RadarScript para ver
echo  el resultado en el dashboard.
echo.
echo  Para deshacer:
echo     assoc .obj=
echo     ftype RadarScript.ObjFile=
echo.

pause
