"""
Reparto de frenada y dimensionado del circuito.
Curso de Ingenieria FUSAL - capitulo 22.

Que hace
--------
1. Dibuja la curva de reparto IDEAL de frenada: el reparto que hace que los
   dos ejes bloqueen a la vez, para cada deceleracion. No es una recta,
   porque la transferencia de carga cambia con la deceleracion.
2. Compara esa curva con el reparto REAL instalado, que si es una recta
   porque lo fija la relacion de areas de bomba y de pinza.
3. Recorre la cadena pie -> pedal -> bomba -> presion -> pinza -> pastilla
   -> disco -> par de frenado -> deceleracion, para comprobar que con una
   fuerza de pie razonable se bloquean las cuatro ruedas.

Uso
---
    python frenos.py

Requiere numpy. Parametros GENERICOS de Formula Student salvo donde se dice.
"""

import numpy as np

G = 9.81

# --- Coche --------------------------------------------------------------
MASA = 300.0          # kg con piloto
BATALLA = 1.55        # m
H_CG = 0.30           # m
REPARTO_DEL = 0.48    # fraccion de peso estatico delante
MU = 1.5              # coeficiente de agarre longitudinal
RADIO_RUEDA = 0.230   # m, radio de rodadura

PESO = MASA * G
B_CG = REPARTO_DEL * BATALLA      # CdG -> eje trasero
A_CG = BATALLA - B_CG             # CdG -> eje delantero

# --- Sistema de frenos (GENERICO: sustituir por el nuestro) -------------
RELACION_PEDAL = 4.5              # brazo pie / brazo bomba
DIAM_BOMBA_DEL = 0.0159           # m (5/8")
DIAM_BOMBA_TRA = 0.0159           # m
DIAM_PISTON_PINZA_DEL = 0.0254    # m
DIAM_PISTON_PINZA_TRA = 0.0254    # m
PISTONES_POR_PINZA = 2            # pistones enfrentados que empujan
RADIO_EFICAZ_DEL = 0.085          # m, radio medio de la pastilla
RADIO_EFICAZ_TRA = 0.085          # m
MU_PASTILLA = 0.40
BALANCE_BAR = 0.62                # fraccion del esfuerzo a la bomba delantera
FUERZA_PIE = 800.0                # N, lo que empuja un piloto con ganas


def area(diametro):
    return np.pi * diametro ** 2 / 4.0


def reparto_ideal(decel_g):
    """Fraccion de la fuerza de frenado que debe ir al eje delantero para
    que los dos ejes bloqueen a la vez, a una deceleracion dada."""
    carga_del = PESO * (B_CG / BATALLA) + MASA * decel_g * G * H_CG / BATALLA
    return carga_del / PESO


def par_por_eje(presion, area_piston, radio_eficaz):
    """Par de frenado de UN eje (dos ruedas), en N.m."""
    fuerza_pastilla = presion * area_piston * PISTONES_POR_PINZA
    return 2.0 * fuerza_pastilla * MU_PASTILLA * radio_eficaz


def cadena_completa(fuerza_pie=FUERZA_PIE):
    """Del pie a la deceleracion, paso a paso."""
    fuerza_varilla = fuerza_pie * RELACION_PEDAL
    f_del = fuerza_varilla * BALANCE_BAR
    f_tra = fuerza_varilla * (1.0 - BALANCE_BAR)
    p_del = f_del / area(DIAM_BOMBA_DEL)
    p_tra = f_tra / area(DIAM_BOMBA_TRA)
    par_del = par_por_eje(p_del, area(DIAM_PISTON_PINZA_DEL), RADIO_EFICAZ_DEL)
    par_tra = par_por_eje(p_tra, area(DIAM_PISTON_PINZA_TRA), RADIO_EFICAZ_TRA)
    fuerza_total = (par_del + par_tra) / RADIO_RUEDA
    return {
        "fuerza_varilla": fuerza_varilla,
        "p_del": p_del, "p_tra": p_tra,
        "par_del": par_del, "par_tra": par_tra,
        "fuerza_total": fuerza_total,
        "decel_g": fuerza_total / PESO,
        "reparto_real": par_del / (par_del + par_tra),
    }


def decel_maxima_agarre():
    """Deceleracion maxima que permite el neumatico, sin mas."""
    return MU


def main():
    print("Reparto ideal de frenada")
    print(f"{'decel [g]':>10} {'reparto ideal delante':>23}")
    with open("reparto_frenada.dat", "w", encoding="ascii") as f:
        f.write("decel ideal real\n")
        c = cadena_completa()
        for d in np.arange(0.0, 2.001, 0.05):
            ideal = reparto_ideal(d)
            f.write(f"{d:.3f} {ideal:.5f} {c['reparto_real']:.5f}\n")
            if abs(d * 100 - round(d * 100)) < 1e-6 and round(d * 20) % 5 == 0:
                print(f"{d:10.2f} {ideal:23.3f}")

    print("\nCadena completa, con "
          f"{FUERZA_PIE:.0f} N de fuerza en el pedal")
    c = cadena_completa()
    print(f"  fuerza en la varilla   : {c['fuerza_varilla']:8.0f} N")
    print(f"  presion delantera      : {c['p_del']/1e5:8.1f} bar")
    print(f"  presion trasera        : {c['p_tra']/1e5:8.1f} bar")
    print(f"  par de frenado delante : {c['par_del']:8.0f} N.m")
    print(f"  par de frenado detras  : {c['par_tra']:8.0f} N.m")
    print(f"  fuerza total en suelo  : {c['fuerza_total']:8.0f} N")
    print(f"  deceleracion teorica   : {c['decel_g']:8.2f} g")
    print(f"  reparto real instalado : {c['reparto_real']:8.3f} delante")

    limite = decel_maxima_agarre()
    print(f"\n  El neumatico solo da {limite:.2f} g, asi que el sistema")
    print(f"  bloquea las cuatro ruedas con margen: es lo que se busca.")
    print(f"  Reparto ideal a {limite:.2f} g: {reparto_ideal(limite):.3f} "
          f"(instalado: {c['reparto_real']:.3f})")

    # Energia y calentamiento de un disco en una frenada
    v0 = 100 / 3.6
    energia = 0.5 * MASA * v0 ** 2
    energia_disco_del = energia * c["reparto_real"] / 2.0
    masa_disco, cp_acero = 0.8, 460.0
    print(f"\nFrenada de {v0*3.6:.0f} km/h a cero:")
    print(f"  energia total            : {energia/1000:7.1f} kJ")
    print(f"  a un disco delantero     : {energia_disco_del/1000:7.1f} kJ")
    print(f"  subida de temperatura    : "
          f"{energia_disco_del/(masa_disco*cp_acero):7.0f} K  "
          f"(disco de {masa_disco} kg, sin refrigerar)")

    print("\nEscrito reparto_frenada.dat")


if __name__ == "__main__":
    main()
