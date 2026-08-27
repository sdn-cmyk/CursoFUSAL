"""
Diagrama de momento de guinada (YMD / Milliken Moment Method).
Curso de Ingenieria FUSAL - capitulo 11.

Que hace
--------
Barre angulo de deriva del vehiculo (beta) y angulo de direccion (delta) con
la guinada bloqueada (r = 0), y para cada combinacion calcula:
    Ay  aceleracion lateral, en g
    N   momento de guinada, en N.m
Con eso escribe los ficheros .dat que dibuja el libro y, de paso, calcula
como cambian la Ay maxima equilibrada y la derivada de estabilidad al mover
el reparto de transferencia de carga lateral (LLTD).

Con r = 0 y sin carga aerodinamica el diagrama NO depende de la velocidad:
los angulos de deriva de cada eje son alfa_del = beta - delta y
alfa_tra = beta, sin terminos en V. En cuanto haya aero habra que rehacerlo
para cada velocidad.

Uso
---
    python ymd.py            # escribe los .dat junto a este fichero

Requiere numpy. Los parametros del coche son GENERICOS de Formula Student:
sustituyelos por los nuestros en cuanto existan.
"""

import numpy as np

G = 9.81

# --- Coche (GENERICO - sustituir por el nuestro) ----------------------
MASA = 300.0        # kg, con piloto
BATALLA = 1.55      # m
VIA = 1.20          # m, igual delante y detras para simplificar
H_CG = 0.30         # m
REPARTO_DEL = 0.48  # fraccion de peso sobre el eje delantero
LLTD = 0.50         # fraccion de la transferencia lateral que va al delantero

# Distancias del centro de gravedad a cada eje.
# Ojo al convenio: el peso delantero lo fija la distancia al eje TRASERO.
B_CG = REPARTO_DEL * BATALLA          # CdG -> eje trasero
A_CG = BATALLA - B_CG                 # CdG -> eje delantero

PESO = MASA * G
CARGA_DEL = REPARTO_DEL * PESO
CARGA_TRA = PESO - CARGA_DEL

# --- Neumatico (Magic Formula, misma del capitulo 8) ------------------
MU0, K_MU = 1.90, 2.8e-4      # mu(Fz) = MU0 - K_MU * Fz
MF_C, MF_E = 1.5, 0.3
U_PICO = 2.0                  # B*alfa en el pico, para C=1.5 y E=0.3


def alfa_pico(fz):
    """Angulo de deriva del pico, en grados. Crece un poco con la carga."""
    return 5.8 + 1.2 * (fz - 500.0) / 1500.0


def fuerza_lateral(alfa_deg, fz):
    """Magic Formula lateral. fz en N, alfa en grados. Devuelve N."""
    fz = np.maximum(fz, 0.0)
    mu = np.maximum(MU0 - K_MU * fz, 0.2)
    d = mu * fz
    b = U_PICO / alfa_pico(fz)
    bx = b * alfa_deg
    interior = (1 - MF_E) * bx + MF_E * np.arctan(bx)
    return d * np.sin(MF_C * np.arctan(interior))


def eje(alfa_deg, carga_eje, delta_fz):
    """Fuerza lateral de un eje, en convenio SAE: un angulo de deriva
    POSITIVO da una fuerza NEGATIVA. Es el mismo neumatico del capitulo 8,
    cuyas curvas estan dibujadas en el primer cuadrante (|Fy| frente a
    |alfa|); aqui hace falta el signo de verdad.

    delta_fz es la transferencia de carga del eje, con signo. Como las dos
    ruedas entran sumadas, su signo solo intercambia cual es la interior.
    """
    carga_rueda = carga_eje / 2.0
    fz_a = np.maximum(carga_rueda + delta_fz, 0.0)
    fz_b = np.maximum(carga_rueda - delta_fz, 0.0)
    return -(fuerza_lateral(alfa_deg, fz_a) + fuerza_lateral(alfa_deg, fz_b))


def punto(beta_deg, delta_deg, lltd=LLTD, iteraciones=80):
    """Un punto del diagrama: (Ay en g, N en N.m).

    Guinada bloqueada (r = 0), asi que alfa_del = beta - delta y
    alfa_tra = beta. La transferencia de carga depende de Ay y Ay depende de
    la transferencia, de modo que se itera; con relajacion, porque cerca del
    limite el punto fijo oscila si se aplica entero.
    """
    alfa_del = beta_deg - delta_deg
    alfa_tra = beta_deg
    ay = 0.0
    for _ in range(iteraciones):
        transferencia = MASA * ay * G * H_CG / VIA
        fy_del = eje(alfa_del, CARGA_DEL, lltd * transferencia)
        fy_tra = eje(alfa_tra, CARGA_TRA, (1.0 - lltd) * transferencia)
        ay = ay + 0.4 * ((fy_del + fy_tra) / PESO - ay)
    transferencia = MASA * ay * G * H_CG / VIA
    fy_del = eje(alfa_del, CARGA_DEL, lltd * transferencia)
    fy_tra = eje(alfa_tra, CARGA_TRA, (1.0 - lltd) * transferencia)
    return ay, A_CG * fy_del - B_CG * fy_tra


def malla(betas, deltas, lltd=LLTD):
    ay = np.zeros((betas.size, deltas.size))
    n = np.zeros_like(ay)
    for i, b in enumerate(betas):
        for j, d in enumerate(deltas):
            ay[i, j], n[i, j] = punto(b, d, lltd)
    return ay, n


def escribe(ruta, curvas, cabecera="Ay N"):
    """Escribe curvas separadas por linea en blanco (pgfplots: empty line=jump)."""
    with open(ruta, "w", encoding="ascii") as f:
        f.write(cabecera + "\n")
        for curva in curvas:
            for ay, n in curva:
                f.write(f"{ay:.5f} {n:.2f}\n")
            f.write("\n")


def equilibrio_limite(lltd, betas, deltas):
    """Punto de equilibrio (N = 0) con la Ay mas alta que alcanza el coche.

    Es el numero que de verdad importa: el coche solo puede sostener una
    curva donde el momento de guinada se anula. Devuelve (Ay, beta, delta).
    """
    ay, n = malla(betas, deltas, lltd)
    mejor = (0.0, 0.0, 0.0)
    for j in range(deltas.size):
        # para cada delta, buscar donde N cruza cero al variar beta
        col_n, col_ay = n[:, j], ay[:, j]
        for i in np.nonzero(np.diff(np.sign(col_n)))[0]:
            t = col_n[i] / (col_n[i] - col_n[i + 1])
            ay_eq = col_ay[i] + t * (col_ay[i + 1] - col_ay[i])
            if abs(ay_eq) > abs(mejor[0]):
                mejor = (ay_eq, betas[i] + t * (betas[i + 1] - betas[i]),
                         deltas[j])
    return mejor


def ay_maxima_equilibrada(lltd, betas, deltas):
    return abs(equilibrio_limite(lltd, betas, deltas)[0])


def margen_en_maxima_ay(lltd, betas, deltas):
    """Momento de guinada que queda en el punto de MAXIMA Ay del diagrama.

    Ese punto es el techo de agarre del coche, pero solo se puede sostener
    si N = 0. Lo que sobra o falta mide el desequilibrio en el limite:
      N < 0  el coche no genera bastante momento para girar tanto: SUBVIRA
      N > 0  le sobra momento y se pasa de vueltas: SOBREVIRA
    Se normaliza por m*g*L para que sea comparable entre coches.
    """
    ay, n = malla(betas, deltas, lltd)
    i, j = np.unravel_index(np.argmax(np.abs(ay)), ay.shape)
    signo = np.sign(ay[i, j]) or 1.0
    return abs(ay[i, j]), signo * n[i, j] / (PESO * BATALLA)


def pendiente_estabilidad(lltd, delta=0.0, beta=0.0, paso=0.5):
    """Pendiente dN/dAy de una linea de delta constante, en N.m por g.

    Es lo que se LEE en el diagrama, y por eso se calcula asi y no como
    dN/dbeta: no depende del convenio de signos de beta. Negativa = estable
    (si el coche desliza mas, aparece un momento que lo endereza).
    """
    ay_mas, n_mas = punto(beta + paso, delta, lltd)
    ay_menos, n_menos = punto(beta - paso, delta, lltd)
    return (n_mas - n_menos) / (ay_mas - ay_menos)


def main():
    betas = np.arange(-10.0, 10.01, 0.25)
    deltas = np.arange(-12.0, 12.01, 0.25)

    # Curvas de delta constante (se recorre beta)
    curvas_delta = []
    for d in np.arange(-12.0, 12.01, 2.0):
        curvas_delta.append([punto(b, d) for b in betas])
    escribe("ymd_delta.dat", curvas_delta)

    # Curvas de beta constante (se recorre delta)
    curvas_beta = []
    for b in np.arange(-10.0, 10.01, 2.5):
        curvas_beta.append([punto(b, d) for d in deltas])
    escribe("ymd_beta.dat", curvas_beta)

    # Barrido de LLTD: lo que de verdad se usa para decidir
    betas_g = np.arange(-10.0, 10.01, 0.5)
    deltas_g = np.arange(-12.0, 12.01, 1.0)
    with open("ymd_lltd.dat", "w", encoding="ascii") as f:
        f.write("LLTD AyEquilibrada AyTope margen\n")
        print(f"{'LLTD':>6} {'Ay equil [g]':>13} {'Ay tope [g]':>12} "
              f"{'margen N/(mgL)':>15}")
        # Por encima de ~0.63 la rueda trasera interior despega y el modelo
        # deja de significar lo mismo, asi que el barrido se corta antes.
        for lltd in np.arange(0.38, 0.621, 0.02):
            ay_eq = ay_maxima_equilibrada(lltd, betas_g, deltas_g)
            ay_tope, margen = margen_en_maxima_ay(lltd, betas_g, deltas_g)
            f.write(f"{lltd:.3f} {ay_eq:.4f} {ay_tope:.4f} {margen:.5f}\n")
            print(f"{lltd:6.2f} {ay_eq:13.3f} {ay_tope:12.3f} {margen:15.4f}")

    ay_eq, beta_eq, delta_eq = equilibrio_limite(LLTD, betas_g, deltas_g)
    print("\nEscritos ymd_delta.dat, ymd_beta.dat y ymd_lltd.dat")
    print(f"Con LLTD = {LLTD:.2f}: Ay maxima equilibrada {abs(ay_eq):.3f} g "
          f"(beta = {beta_eq:.1f} deg, delta = {delta_eq:.1f} deg)")


if __name__ == "__main__":
    main()
