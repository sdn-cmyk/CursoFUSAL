# Curso de Ingeniería FUSAL — proyecto LaTeX

Libro/memoria de formación del departamento de mecánica. 8 partes, 60 capítulos
más anexos, en clase `book`.

## Compilar

```bash
latexmk -pdf main.tex
```

O doble clic en `compilar.bat`. Para limpiar auxiliares: `limpiar.bat`
(o `latexmk -c`; `latexmk -C` borra también el PDF).

Requiere MiKTeX o TeX Live con `latexmk` y `biber`. Motor: **pdfLaTeX**
(no xelatex ni lualatex: el preámbulo usa `inputenc` + `newtx`).

## Sacar un extracto para revisión

Para mandar a los compañeros solo lo que está escrito:

```bash
exportar_revision.bat
```

Produce `CursoFUSAL_Bloque0_revision.pdf` con la parte I, una portada que dice
que es un extracto, un capítulo inicial de instrucciones para el revisor y, al
final, la lista de todo lo que ya sabemos que falta.

Las referencias cruzadas a capítulos no escritos (cap. 53, 26, 13…) siguen
saliendo con su número correcto: el maestro `CursoFUSAL_Bloque0_revision.tex`
lee las etiquetas de esos capítulos con `\includeref` sin imprimirlos. Por eso el
`.bat` compila el libro completo antes y después del extracto; no te saltes pasos.

Cuando se escriba otra parte, se añaden sus `\include` en el extracto (y se
quitan de la lista de `\includeref`), o se hace un maestro nuevo copiando ese.

## Escribir solo un capítulo

Compilar el libro entero tarda. Mientras trabajas en un capítulo, descomenta en
`main.tex`:

```latex
\includeonly{Capitulos/06_Refrigeracion/42_superficies_compactas}
```

Compila en segundos y mantiene la numeración y las referencias cruzadas del
resto (siempre que hayas compilado el libro completo al menos una vez).

## Estructura

```
main.tex                 fichero maestro: portada, partes y \include de capítulos
latexmkrc                configuración de compilación
bibliografia.bib         TODAS las referencias, con clave autor_tema_año
Estilo/
  preambulo.tex          paquetes y configuración  <- los \usepackage van AQUÍ
  entornos.tex           los seis recuadros (caso, regla, ojo, entregable...)
  macros.tex             símbolos: \Cl, \Kus, \NTU...  <- úsalos siempre
  portada.tex            portada y créditos
Capitulos/
  00_Frontal/            prólogo, cómo usar el libro, nomenclatura
  01_Tronco/  … 08_Transversal/    un .tex por capítulo
  99_Anexos/             plantillas, checklists, planos, código
Imagenes/<parte>/        figuras (PDF vectorial mejor que PNG)
Codigo/<subsistema>/     fuentes que se insertan con \lstinputlisting
Planos/                  planos en PDF, se insertan con \includepdf
```

## Reglas de escritura

1. **Los `\usepackage` van en `Estilo/preambulo.tex`**, nunca en un capítulo.
2. **Símbolos con macro**, nunca a mano: `$\Cl$`, no `$C_L$`. Si cambia el
   convenio, se cambia en un sitio.
3. **Unidades con `siunitx`**: `\SI{85}{\celsius}`, `\SI{1200}{\newton\per\milli\meter}`.
   Nunca `85 ºC` a pelo. Decimal con coma (ya configurado).
4. **Todo símbolo nuevo va a la nomenclatura** (`Capitulos/00_Frontal/nomenclatura.tex`)
   y a `Estilo/macros.tex`.
5. **Referencias cruzadas con `cleveref`**: `\cref{ch:neumatico}` produce
   "capítulo 8" solo. Etiquetas: `ch:` capítulos, `sec:` apartados, `fig:`,
   `tab:`, `eq:`.
6. **Nada de código copiado a mano**: `\lstinputlisting{...}` desde `Codigo/`.
7. **Lo que falta se marca**, no se recuerda: `\pendiente{...}` y `\falta{...}`.

## Los recuadros

| Entorno | Para qué |
|---|---|
| `objetivos` | Qué debe saber el lector al terminar. Abre el capítulo. |
| `clave` | La idea que hay que retener aunque se olvide el resto. |
| `caso[título]` | Lo que hicimos nosotros: decisión, datos, resultado, qué cambiaríamos. |
| `regla[artículo]` | Requisito del reglamento que condiciona el diseño. |
| `ojo` | Errores que se repiten cada temporada. |
| `entregable` | Qué produce el lector al terminar el capítulo. |
| `juez` | Preguntas tipo del design event. |

`caso` y `regla` admiten un argumento opcional que se añade al título:
`\begin{caso}[Radiador AXM2]`.

También `\fichasesion{duración}{requisitos}{material}` para impartir el capítulo
como clase.

## Modo borrador

En `main.tex`:

- `\borradortrue` → se ven los `\pendiente` y `\falta` resaltados. Para trabajar.
- `\borradorfalse` → versión limpia. Para repartir.

## Personalizar

- **Color del equipo**: `fusalPrim` en `Estilo/preambulo.tex`.
- **Logo**: sustituye el rectángulo de `Estilo/portada.tex` por
  `\includegraphics[width=6cm]{Imagenes/logo_fusal.pdf}`.
- **Temporada y versión**: `\temporada` y `\version` en `main.tex`.
- **Doble cara para imprimir**: cambia `oneside,openany` por `twoside,openright`
  en `\documentclass`.
- **Tipografía**: sustituye las líneas `newtxtext`/`newtxmath` (ver comentario
  en el preámbulo).

## Control de versiones

Hay `.gitignore` preparado. Si el libro lo van a mantener varias personas a lo
largo de los años, ponlo en git (o al menos en un repositorio compartido del
equipo) desde el primer día: es literalmente el objetivo del documento.

```bash
git init && git add . && git commit -m "Esqueleto del curso FUSAL"
```
