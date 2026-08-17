@echo off

cd /d "%~dp0"
echo.
echo === Compilando Curso FUSAL ===
echo.
latexmk -pdf main.tex
if errorlevel 1 (
  echo.
  echo *** HA FALLADO. Mira main.log y busca la primera linea que empiece por "!" ***
  echo.
  pause
  exit /b 1
)
echo.
echo === Listo: main.pdf ===
echo.
pause
