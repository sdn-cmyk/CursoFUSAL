@echo off
REM ====================================================================
REM  Borra los ficheros auxiliares (aux, log, toc, bbl...) y deja el PDF.
REM  Usalo cuando la compilacion se atasque con errores raros.
REM  Para borrar tambien el PDF:  latexmk -C
REM ====================================================================
cd /d "%~dp0"
latexmk -c
echo.
echo === Auxiliares borrados (main.pdf se conserva) ===
echo.
pause
