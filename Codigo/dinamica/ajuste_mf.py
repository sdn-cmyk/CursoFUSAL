"""
Ajuste de la Magic Formula lateral a datos de neumatico.
Curso de Ingenieria FUSAL - capitulo 9.

Que hace
--------
1. Lee un fichero de datos con las columnas SA (angulo de deriva, grados),
   FY (fuerza lateral, N) y FZ (carga vertical, N).
2. Agrupa los puntos por carga vertical nominal.
3. Ajusta, para cada carga, la Magic Formula de cinco parametros.
4. Ajusta la dependencia con la carga y escribe los coeficientes.
5. Dibuja ajuste y residuos.

Si no se le pasa fichero, genera datos sinteticos con ruido para poder
probar el flujo completo sin datos reales. ESOS DATOS NO SIRVEN PARA
DISENAR: son solo para comprobar que el script funciona.

Uso
---
    python ajuste_mf.py                      # datos sinteticos de prueba
    python ajuste_mf.py datos_ttc.csv        # datos reales

Requiere numpy, scipy y matplotlib.
"""

import sys

import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

# Cargas verticales nominales del ensayo, en N. Ajustar a las del fichero.
CARGAS_NOMINALES = np.array([500.0, 1000.0, 1500.0, 2000.0])
# Media anchura de la ventana de agrupacion, en N.
TOLERANCIA_FZ = 120.0
# Carga de referencia del modelo, en N.
FZ0 = 1000.0


# ---------------------------------------------------------------------
#  Modelo
# ---------------------------------------------------------------------
def magic_formula(x, B, C, D, E, Sh=0.0, Sv=0.0):
    """Magic Formula de Pacejka, forma basica.

    y(x) = D sin( C arctan( B x' - E (B x' - arctan(B x')) ) ) + Sv
    con x' = x + Sh.

    Sh recoge la deriva residual (conicidad y ply steer) y Sv el empuje
    residual: son los que hacen que la curva medida no pase por el origen.
    """
    xp = x + Sh
    Bx = B * xp
    return D * np.sin(C * np.arctan(Bx - E * (Bx - np.arctan(Bx)))) + Sv


def rigidez_deriva(B, C, D):
    """Rigidez de deriva, N/grado. Es la pendiente en el origen: BCD."""
    return B * C * D


# ---------------------------------------------------------------------
#  Datos
# ---------------------------------------------------------------------
def datos_sinteticos(semilla=0):
    """Genera un barrido de deriva con ruido para probar el script."""
    rng = np.random.default_rng(semilla)
    # Parametros "verdaderos": mu baja con la carga (sensibilidad a la carga)
    B_ref = {500: 0.3448, 1000: 0.3226, 1500: 0.3030, 2000: 0.2857}
    filas = []
    for fz in CARGAS_NOMINALES:
        mu = 1.90 - 2.8e-4 * fz
        D = mu * fz
        B = B_ref[int(fz)]
        sa = np.arange(-12.0, 12.01, 0.5)
        fy = magic_formula(sa, B, 1.5, D, 0.3, Sh=0.12, Sv=18.0)
        fy = fy + rng.normal(0.0, 0.012 * D, sa.size)      # ruido de medida
        fz_medida = fz + rng.normal(0.0, 15.0, sa.size)    # la carga oscila
        filas.append(np.column_stack([sa, fy, fz_medida]))
    return np.vstack(filas)


def leer_datos(ruta):
    """Lee un CSV con cabecera SA,FY,FZ. Comprueba el convenio de signos."""
    datos = np.genfromtxt(ruta, delimiter=",", names=True)
    tabla = np.column_stack([datos["SA"], datos["FY"], datos["FZ"]])
    # Comprobacion de signos: con el convenio SAE, Fy y alpha crecen juntos.
    correlacion = np.corrcoef(tabla[:, 0], tabla[:, 1])[0, 1]
    if correlacion < 0:
        print("AVISO: Fy y alpha tienen signos opuestos. Revisa el convenio "
              "antes de seguir; probablemente haya que cambiar el signo de FY.")
    return tabla


def agrupar_por_carga(tabla):
    """Devuelve {carga_nominal: (sa, fy)} con los puntos de cada escalon."""
    grupos = {}
    for fz in CARGAS_NOMINALES:
        mascara = np.abs(tabla[:, 2] - fz) < TOLERANCIA_FZ
        if mascara.sum() < 10:
            print(f"AVISO: solo {mascara.sum()} puntos para Fz = {fz:.0f} N. "
                  "No se ajusta.")
            continue
        grupos[fz] = (tabla[mascara, 0], tabla[mascara, 1])
    return grupos


# ---------------------------------------------------------------------
#  Ajuste
# ---------------------------------------------------------------------
def ajustar_una_carga(sa, fy, fz):
    """Ajusta B, C, D, E, Sh, Sv para un unico escalon de carga.

    Las semillas y los limites importan: sin ellos el optimizador se va a
    soluciones sin sentido fisico (D negativo, C fuera de rango...).
    """
    D0 = np.max(np.abs(fy))
    semilla = [0.30, 1.5, D0, 0.3, 0.0, 0.0]
    limites = (
        [0.05, 1.0, 0.5 * D0, -3.0, -2.0, -0.1 * D0],   # minimos
        [2.00, 2.5, 1.5 * D0, 1.0, 2.0, 0.1 * D0],      # maximos
    )
    coef, _ = curve_fit(magic_formula, sa, fy, p0=semilla,
                        bounds=limites, maxfev=20000)
    residuos = fy - magic_formula(sa, *coef)
    rmse = float(np.sqrt(np.mean(residuos ** 2)))
    return coef, rmse


def comprobaciones(coef, rmse, fz):
    """Avisa de los ajustes que salen numericamente bien y fisicamente mal."""
    B, C, D, E, Sh, Sv = coef
    mu = D / fz
    avisos = []
    if not 1.0 <= mu <= 3.0:
        avisos.append(f"mu = {mu:.2f} fuera de rango razonable")
    if not 1.2 <= C <= 1.9:
        avisos.append(f"C = {C:.2f} atipico para fuerza lateral")
    if rigidez_deriva(B, C, D) > 2000.0:
        avisos.append("rigidez de deriva absurdamente alta")
    if rmse > 0.05 * D:
        avisos.append(f"RMSE = {rmse:.0f} N, mas del 5 % del pico")
    return avisos


# ---------------------------------------------------------------------
#  Programa principal
# ---------------------------------------------------------------------
def main():
    if len(sys.argv) > 1:
        tabla = leer_datos(sys.argv[1])
    else:
        print("Sin fichero de datos: se usan datos SINTETICOS de prueba.\n")
        tabla = datos_sinteticos()

    grupos = agrupar_por_carga(tabla)
    resultados = {}

    print(f"{'Fz [N]':>8} {'B':>8} {'C':>6} {'D [N]':>9} {'E':>7} "
          f"{'Ca [N/deg]':>11} {'RMSE [N]':>9}")
    for fz, (sa, fy) in sorted(grupos.items()):
        coef, rmse = ajustar_una_carga(sa, fy, fz)
        resultados[fz] = coef
        B, C, D, E = coef[:4]
        print(f"{fz:8.0f} {B:8.4f} {C:6.3f} {D:9.1f} {E:7.3f} "
              f"{rigidez_deriva(B, C, D):11.1f} {rmse:9.1f}")
        for aviso in comprobaciones(coef, rmse, fz):
            print(f"         --> REVISAR: {aviso}")

    # Dependencia con la carga: mu(Fz) lineal es suficiente en el rango de FS.
    cargas = np.array(sorted(resultados))
    mus = np.array([resultados[f][2] / f for f in cargas])
    k, mu0 = np.polyfit(cargas, mus, 1)
    print(f"\nSensibilidad a la carga:  mu(Fz) = {mu0:.3f} - "
          f"{-k:.3e} * Fz     [1/N]")
    print("Extrapolar fuera del rango ensayado no vale: el modelo hace "
          "cualquier cosa.")

    graficar(grupos, resultados)


def graficar(grupos, resultados):
    fig, (ax, axr) = plt.subplots(
        2, 1, figsize=(7, 7), height_ratios=[3, 1], sharex=True)
    malla = np.linspace(-13, 13, 400)
    for fz, (sa, fy) in sorted(grupos.items()):
        coef = resultados[fz]
        linea, = ax.plot(malla, magic_formula(malla, *coef),
                         label=f"Fz = {fz:.0f} N")
        ax.plot(sa, fy, ".", ms=3, color=linea.get_color(), alpha=0.5)
        axr.plot(sa, fy - magic_formula(sa, *coef), ".", ms=3,
                 color=linea.get_color())
    ax.set_ylabel("Fy [N]")
    ax.legend()
    ax.grid(alpha=0.3)
    axr.axhline(0.0, color="k", lw=0.8)
    axr.set_xlabel("angulo de deriva [grados]")
    axr.set_ylabel("residuo [N]")
    axr.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig("ajuste_mf.png", dpi=150)
    print("\nFigura escrita en ajuste_mf.png")


if __name__ == "__main__":
    main()
