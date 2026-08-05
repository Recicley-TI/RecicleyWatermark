@echo off
cd /d "%~dp0"
echo ============================================
echo   Diagnostico Recicley Watermark
echo ============================================
echo.
echo Ejecutando GUI_Watermark.py con Python...
echo (esto puede tardar unos segundos)
echo.

"L:\Python\python.exe" GUI_Watermark.py > diagnostico_log.txt 2>&1
echo Codigo de salida: %errorlevel% >> diagnostico_log.txt

echo.
echo ============================================
echo   RESULTADO (tambien guardado en diagnostico_log.txt)
echo ============================================
echo.
type diagnostico_log.txt
echo.
echo ============================================
echo Copia TODO lo de arriba y envialo, o adjunta
echo el archivo diagnostico_log.txt que quedo en
echo esta misma carpeta.
echo ============================================
echo.
pause
