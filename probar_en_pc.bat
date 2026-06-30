@echo off
title NOVA AI Android - Probar en PC (modo simulación)
cd /d "%~dp0"
color 0B

echo ============================================================
echo  NOVA AI Android - Modo simulacion en PC
echo ============================================================
echo.
echo Esto abre la app en tu PC para probar la interfaz.
echo Las acciones de Android solo se simularan ([sim] en la pantalla).
echo Para usarla de verdad necesitas compilarla a APK (ver README.md).
echo.
pause

python -c "import kivy" 2>nul
if errorlevel 1 (
    echo Instalando Kivy...
    python -m pip install --upgrade pip
    python -m pip install "kivy[base]==2.3.0"
)

python main.py
if errorlevel 1 pause
