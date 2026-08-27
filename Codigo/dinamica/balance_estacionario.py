"""
Transferencia de carga y balance en regimen estacionario.
Curso de Ingenieria FUSAL - capitulo 10.

Que hace
--------
1. Descompone la transferencia de carga lateral de cada eje en sus tres
   terminos (elastica, geometrica y masa no suspendida) y COMPRUEBA que la
   suma de los seis da exactamente m*ay*h/t. Si no cuadra, hay un error.
2. Calcula, para cada reparto de transferencia (LLTD), la aceleracion
   lateral que puede sostener cada eje. El eje que se queda corto es el que
   limita, y ahi esta el balance del coche.
3. Escribe los .dat que dibuja el libro.

Uso
---
    python balance_estacionario.py

Requiere numpy. Los parametros son GENERICOS de Formula Student salvo las
alturas de centro de balanceo, que son las de nuestro coche.
"""

import numpy as np

G = 9.81

# --- Coche -------------------------------------------------------------
MASA = 300.0          # kg, con piloto
MASA_SUSP = 260.0     # kg, masa suspendida
MASA_NS_DEL = 20.0    # kg, masa no suspendida delantera
MASA_NS_TRA = 20.0    # kg, masa no suspendida trasera
BATALLA = 1.55        # m
VIA = 1.20            # m
H_CG = 0.30           # m, centro de gravedad del coche completo
Z_NS = 0.23           # m, altura del CdG no suspendido (centro de rueda)
REPARTO_DEL = 0.48    # fraccion de peso sobre el eje delantero

# Alturas de centro de balanceo: estas SI son las nuestras.
Z_RC_DEL = 0.030      # m
Z_RC_TRA = 0.080      # m

# Rigideces a balanceo en N.m/grado. GENERICAS: falta medir las nuestras.
K_ROLL_DEL = 320.0
K_ROLL_TRA = 270.0

PESO = MASA * G
CARGA_DEL = REPARTO_DEL * PESO
CARGA_TRA = PESO - CARGA_DEL
B_CG = REPARTO_DEL * BATALLA          # CdG -> eje trasero
A_CG = BATALLA - B_CG                 # CdG -> eje delantero

# Altura del CdG suspendido, deducida para que sea coherente con H_CG.
# No se elige a ojo: si no cuadra, la descomposicion no suma.
H_SUSP = (MASA * H_CG - (MASA_NS_DEL + MASA_NS_TRA) * Z_NS) / MASA_SUSP

# Altura del eje de balanceo bajo el CdG, interpolando entre los dos RC.
Z_EJE_BALANCEO = Z_RC_DEL + (Z_RC_TRA - Z_RC_DEL) * (A_CG / BATALLA)
BRAZO_SUSP = H_SUSP - Z_EJE_BALANCEO  # brazo de la masa suspendida

# --- Neumatico (el mismo del capitulo 8) -------------------------------
MU0, K_MU = 1.90, 2.8e-4


def mu(fz):
    return np.maximum(MU0 - K_MU * np.maximum(fz, 0.0), 0.2)


def pico_eje(carga_eje, delta_fz):
    """Fuerza lateral maxima de un eje con una transferencia dada."""
    fz_ext = np.maximum(carga_eje / 2.0 + delta_fz, 0.0)
    fz_int = np.maximum(carga_eje / 2.0 - delta_fz, 0.0)
    return mu(fz_ext) * fz_ext + mu(fz_int) * fz_int


# --- 1. Descomposicion de la transferencia lateral ---------------------
def descomposicion(ay_g):
    """Los tres terminos de cada eje, en N, para una Ay dada en g."""
    ay = ay_g * G
    reparto_susp_del = REPARTO_DEL            # se supone igual que el total
    elastica_total = MASA_SUSP * ay * BRAZO_SUSP / VIA
    reparto_rigidez = K_ROLL_DEL / (K_ROLL_DEL + K_ROLL_TRA)
    return {
        "del": {
            "elastica": elastica_total * reparto_rigidez,
            "geometrica": MASA_SUSP * ay * reparto_susp_del * Z_RC_DEL / VIA,
            "no_susp": MASA_NS_DEL * ay * Z_NS / VIA,
        },
        "tra": {
            "elastica": elastica_total * (1.0 - reparto_rigidez),
            "geometrica": (MASA_SUSP * ay * (1.0 - reparto_susp_del)
                           * Z_RC_TRA / VIA),
            "no_susp": MASA_NS_TRA * ay * Z_NS / VIA,
        },
    }


# --- 2. Balance: que eje se queda corto --------------------------------
def ay_limite_eje(carga_eje, fraccion_transferencia, reparto_peso):
    """Ay (en g) a la que un eje agota su agarre.

    Lo que el eje TIENE que dar crece con Ay; lo que PUEDE dar baja, porque
    la transferencia de carga le quita agarre. Se cruzan en un punto.
    """
    rejilla = np.arange(0.0, 3.0, 0.001)
    necesita = rejilla * reparto_peso * PESO
    transferencia = fraccion_transferencia * MASA * rejilla * G * H_CG / VIA
    puede = pico_eje(carga_eje, transferencia)
    cruce = np.nonzero(np.diff(np.sign(puede - necesita)))[0]
    return rejilla[cruce[0]] if cruce.size else np.nan


def main():
    # --- Descomposicion, con la comprobacion que importa ---
    ay_g = 1.4
    d = descomposicion(ay_g)
    total_del = sum(d["del"].values())
    total_tra = sum(d["tra"].values())
    invariante = MASA * ay_g * G * H_CG / VIA

    print(f"Transferencia de carga lateral a {ay_g} g")
    print(f"  h del CdG suspendido : {H_SUSP:.4f} m  (deducida, no elegida)")
    print(f"  eje de balanceo      : {Z_EJE_BALANCEO:.4f} m")
    print(f"  brazo de la m. susp. : {BRAZO_SUSP:.4f} m\n")
    print(f"{'':14}{'elastica':>10}{'geometrica':>12}{'no susp.':>10}{'total':>10}")
    for eje, etiqueta in (("del", "delantero"), ("tra", "trasero")):
        v = d[eje]
        print(f"  {etiqueta:12}{v['elastica']:10.1f}{v['geometrica']:12.1f}"
              f"{v['no_susp']:10.1f}{sum(v.values()):10.1f}")
    print(f"\n  suma de los seis terminos : {total_del + total_tra:8.1f} N")
    print(f"  invariante  m*ay*h/t      : {invariante:8.1f} N")
    error = abs(total_del + total_tra - invariante)
    print(f"  diferencia                : {error:8.4f} N  "
          f"{'OK' if error < 1e-6 else '<-- REVISAR'}")
    print(f"\n  LLTD = {100 * total_del / invariante:.1f} % al eje delantero")

    with open("transferencia_terminos.dat", "w", encoding="ascii") as f:
        f.write("eje elastica geometrica nosusp\n")
        f.write(f"1 {d['del']['elastica']:.1f} {d['del']['geometrica']:.1f} "
                f"{d['del']['no_susp']:.1f}\n")
        f.write(f"2 {d['tra']['elastica']:.1f} {d['tra']['geometrica']:.1f} "
                f"{d['tra']['no_susp']:.1f}\n")

    # --- Balance frente al LLTD ---
    print(f"\n{'LLTD':>6} {'Ay del [g]':>11} {'Ay tra [g]':>11} {'limita':>9}")
    with open("balance_lltd.dat", "w", encoding="ascii") as f:
        f.write("LLTD AyDel AyTra\n")
        for lltd in np.arange(0.35, 0.6501, 0.01):
            ay_del = ay_limite_eje(CARGA_DEL, lltd, REPARTO_DEL)
            ay_tra = ay_limite_eje(CARGA_TRA, 1.0 - lltd, 1.0 - REPARTO_DEL)
            f.write(f"{lltd:.3f} {ay_del:.4f} {ay_tra:.4f}\n")
            if abs(lltd * 100 - round(lltd * 100)) < 1e-6 and \
                    round(lltd * 100) % 5 == 0:
                quien = "delantero" if ay_del < ay_tra else "trasero"
                print(f"{lltd:6.2f} {ay_del:11.3f} {ay_tra:11.3f} {quien:>9}")

    print("\nEscritos transferencia_terminos.dat y balance_lltd.dat")


if __name__ == "__main__":
    main()
