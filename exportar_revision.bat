@echo off
REM ====================================================================
REM  Genera CursoFUSAL_Bloque0_revision.pdf: solo la parte I, para mandar
REM  a revisar. Son tres pasos y los tres hacen falta:
REM
REM  1) El libro completo, que es de donde salen las etiquetas de los
REM     capitulos 8 a 60. Sin este paso, las referencias del extracto
REM     saldrian como "??".
REM  2) El extracto.
REM  3) El libro completo otra vez, porque el paso 2 reescribe los
REM     auxiliares de los capitulos de la parte I con su paginacion.
REM ====================================================================
cd /d "%~dp0"

echo.
echo === 1/3  Libro completo ===
latexmk -pdf main.tex
if errorlevel 1 goto :fallo

echo.
echo === 2/3  Extracto para revision ===
latexmk -pdf CursoFUSAL_Bloque0_revision.tex
if errorlevel 1 goto :fallo

echo.
echo === 3/3  Libro completo otra vez ===
latexmk -pdf main.tex
if errorlevel 1 goto :fallo

echo.
echo LISTO: CursoFUSAL_Bloque0_revision.pdf
echo.
pause
exit /b 0

:fallo
echo.
echo *** HA FALLADO. Mira el .log y busca la primera linea que empiece por "!" ***
echo.
pause
exit /b 1
