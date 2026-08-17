# =====================================================================
#  Configuración de latexmk — Curso FUSAL
#  Uso:  latexmk -pdf main.tex     (o simplemente: latexmk)
# =====================================================================

# pdflatex (no xelatex/lualatex: el preámbulo usa inputenc + newtx)
$pdf_mode = 1;
$pdflatex = 'pdflatex -synctex=1 -interaction=nonstopmode -file-line-error %O %S';

# Bibliografía con biber (biblatex)
$bibtex_use = 2;

# Índice alfabético
$makeindex = 'makeindex %O -o %D %S';

# Fichero principal por defecto
@default_files = ('main.tex');

# Extensiones extra que borra "latexmk -c"
$clean_ext = 'bbl run.xml synctex.gz idx ind ilg tdo fls fdb_latexmk out';
