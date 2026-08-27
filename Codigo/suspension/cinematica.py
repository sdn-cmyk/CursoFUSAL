"""
Cinematica de un cuadrilatero deformable (doble trapecio), vista frontal.
Curso de Ingenieria FUSAL - capitulo 16.

Que hace
--------
Para un recorrido de suspension dado calcula, en cada posicion:
    - angulo de caida y ganancia de caida
    - variacion de via (scrub)
    - centro instantaneo y altura del centro de balanceo
    - bump steer aproximado, a partir del error de longitud del tirante
y escribe los .dat que dibuja el libro.

Como funciona
-------------
El trapecio inferior gira alrededor de su pivote interior. Conocida la
posicion de la rotula inferior, la superior es la interseccion de dos
circunferencias: una centrada en el pivote superior interior (radio = brazo
superior) y otra centrada en la rotula inferior (radio = distancia entre
rotulas, que es rigida porque las dos van en la mangueta).

Con las dos rotulas queda definida la mangueta como solido rigido, y todo lo
demas -- huella de contacto, centro de rueda, punto exterior del tirante --
se obtiene aplicandole la misma transformacion.

Limitaciones, que hay que tener presentes
-----------------------------------------
Es un modelo 2D en el plano frontal. No ve el avance, ni el angulo de salida
en vista lateral, ni el efecto de la direccion. El bump steer que calcula es
una ESTIMACION: mide cuanto cambia la longitud que deberia tener el tirante
y lo convierte en convergencia dividiendo por la longitud del brazo de
direccion, que se pasa como dato porque en 2D no se ve. Sirve para entender
la tendencia y para elegir donde poner el tirante; el numero final sale del
modelo 3D del CAD.

Uso
---
    python cinematica.py

Requiere numpy. Coordenadas en mm, en el plano frontal:
    y hacia la derecha del coche (0 = plano de simetria)
    z hacia arriba (0 = suelo)
"""

import numpy as np

# =====================================================================
#  Geometria de EJEMPLO del eje delantero.
#  NO son nuestros puntos duros: es una geometria plausible ajustada para
#  dar los 30 mm de centro de balanceo que buscamos. Sustituir por los
#  nuestros en cuanto esten congelados.
# =====================================================================
PIVOTE_INF_INT = np.array([185.0, 122.0])   # chasis, trapecio inferior
PIVOTE_SUP_INT = np.array([215.0, 280.0])   # chasis, trapecio superior
ROTULA_INF = np.array([555.0, 120.0])       # mangueta, rotula inferior
ROTULA_SUP = np.array([540.0, 300.0])       # mangueta, rotula superior
HUELLA = np.array([600.0, 0.0])             # huella de contacto
CENTRO_RUEDA = np.array([600.0, 230.0])     # radio de rodadura 230 mm

# Tirante de direccion. El interior es el que se elige; el exterior va en la
# mangueta. Se dan dos alturas del punto interior para comparar.
TIRANTE_EXT = np.array([530.0, 165.0])
TIRANTE_INT_BUENO = np.array([195.0, 161.2])   # alineado con el centro instantaneo
TIRANTE_INT_MALO = np.array([195.0, 130.0])    # 31 mm mas bajo

BRAZO_DIRECCION = 75.0      # mm, longitud real del brazo de direccion (dato 3D)
RECORRIDO = 30.0            # mm de recorrido a cada lado


def interseccion_circulos(c1, r1, c2, r2, referencia):
    """Interseccion de dos circunferencias; devuelve la solucion mas cercana
    a 'referencia', que es la rama fisica del mecanismo."""
    d_vec = c2 - c1
    d = np.hypot(*d_vec)
    if d > r1 + r2 or d < abs(r1 - r2) or d == 0:
        raise ValueError("el mecanismo no cierra: revisa longitudes")
    a = (r1 ** 2 - r2 ** 2 + d ** 2) / (2 * d)
    h = np.sqrt(max(r1 ** 2 - a ** 2, 0.0))
    base = c1 + a * d_vec / d
    normal = np.array([-d_vec[1], d_vec[0]]) / d
    opciones = (base + h * normal, base - h * normal)
    return min(opciones, key=lambda p: np.hypot(*(p - referencia)))


def interseccion_rectas(p1, d1, p2, d2):
    """Interseccion de dos rectas dadas por punto y direccion."""
    matriz = np.array([[d1[0], -d2[0]], [d1[1], -d2[1]]])
    if abs(np.linalg.det(matriz)) < 1e-9:
        return None                      # brazos paralelos: CI en el infinito
    t = np.linalg.solve(matriz, p2 - p1)
    return p1 + t[0] * d1


class Suspension:
    def __init__(self):
        self.brazo_inf = np.hypot(*(ROTULA_INF - PIVOTE_INF_INT))
        self.brazo_sup = np.hypot(*(ROTULA_SUP - PIVOTE_SUP_INT))
        self.mangueta = np.hypot(*(ROTULA_SUP - ROTULA_INF))
        self.ang_inf_0 = np.arctan2(*(ROTULA_INF - PIVOTE_INF_INT)[::-1])
        # Puntos solidarios a la mangueta, en el sistema local de la mangueta
        eje = (ROTULA_SUP - ROTULA_INF) / self.mangueta
        self.base_local = np.array([[eje[0], -eje[1]], [eje[1], eje[0]]])
        self.solidarios = {
            nombre: np.linalg.solve(self.base_local, punto - ROTULA_INF)
            for nombre, punto in (("huella", HUELLA),
                                  ("centro_rueda", CENTRO_RUEDA),
                                  ("tirante", TIRANTE_EXT))
        }

    def postura(self, angulo_inf):
        """Resuelve el mecanismo para un angulo del trapecio inferior."""
        rot_inf = PIVOTE_INF_INT + self.brazo_inf * np.array(
            [np.cos(angulo_inf), np.sin(angulo_inf)])
        rot_sup = interseccion_circulos(
            PIVOTE_SUP_INT, self.brazo_sup, rot_inf, self.mangueta, ROTULA_SUP)
        eje = (rot_sup - rot_inf) / self.mangueta
        base = np.array([[eje[0], -eje[1]], [eje[1], eje[0]]])
        puntos = {n: rot_inf + base @ local
                  for n, local in self.solidarios.items()}
        puntos["rotula_inf"], puntos["rotula_sup"] = rot_inf, rot_sup
        return puntos

    def angulo_para_altura(self, subida, tolerancia=1e-9):
        """Busca por biseccion el angulo que sube la huella lo pedido."""
        objetivo = HUELLA[1] + subida
        lo, hi = self.ang_inf_0 - 0.35, self.ang_inf_0 + 0.35
        # la huella sube al girar el trapecio: funcion monotona en el rango util
        for _ in range(200):
            medio = 0.5 * (lo + hi)
            if self.postura(medio)["huella"][1] < objetivo:
                lo = medio
            else:
                hi = medio
            if hi - lo < tolerancia:
                break
        return 0.5 * (lo + hi)

    def estado(self, subida):
        """Todo lo que interesa de una posicion, dado el recorrido en mm.

        Convenio: recorrido positivo = compresion (la rueda sube respecto al
        chasis, que es lo mismo que bajar el chasis sobre la rueda). Caida
        negativa = parte alta de la rueda hacia dentro.
        """
        p = self.postura(self.angulo_para_altura(subida))
        eje_mangueta = p["rotula_sup"] - p["rotula_inf"]
        eje_0 = ROTULA_SUP - ROTULA_INF
        giro = (np.arctan2(eje_mangueta[1], eje_mangueta[0])
                - np.arctan2(eje_0[1], eje_0[0]))
        # El brazo superior es mas corto, asi que en compresion la rotula
        # superior entra mas que la inferior y la rueda se tumba hacia dentro.
        # Eso es caida NEGATIVA, de ahi el signo.
        caida = -np.degrees(giro)

        centro_inst = interseccion_rectas(
            PIVOTE_INF_INT, p["rotula_inf"] - PIVOTE_INF_INT,
            PIVOTE_SUP_INT, p["rotula_sup"] - PIVOTE_SUP_INT)
        if centro_inst is None:
            altura_cb = 0.0
        else:
            direccion = p["huella"] - centro_inst
            if abs(direccion[0]) < 1e-9:
                altura_cb = 0.0
            else:
                pendiente = direccion[1] / direccion[0]
                altura_cb = p["huella"][1] + pendiente * (0.0 - p["huella"][0])

        via = 2.0 * p["huella"][0]
        bump_steer = {}
        for nombre, interior in (("bueno", TIRANTE_INT_BUENO),
                                 ("malo", TIRANTE_INT_MALO)):
            largo_0 = np.hypot(*(TIRANTE_EXT - interior))
            largo = np.hypot(*(p["tirante"] - interior))
            bump_steer[nombre] = np.degrees((largo - largo_0) / BRAZO_DIRECCION)
        return {
            "recorrido": subida, "caida": caida, "via": via,
            "centro_inst": centro_inst, "altura_cb": altura_cb,
            "bump_bueno": bump_steer["bueno"], "bump_malo": bump_steer["malo"],
            "huella": p["huella"],
        }


def main():
    s = Suspension()
    base = s.estado(0.0)
    print("Geometria de partida")
    print(f"  brazo inferior      : {s.brazo_inf:7.1f} mm")
    print(f"  brazo superior      : {s.brazo_sup:7.1f} mm")
    print(f"  distancia rotulas   : {s.mangueta:7.1f} mm")
    print(f"  via                 : {base['via']:7.1f} mm")
    print(f"  centro instantaneo  : ({base['centro_inst'][0]:8.1f},"
          f" {base['centro_inst'][1]:7.1f}) mm")
    brazo_virtual = base["centro_inst"][0] - HUELLA[0]
    print(f"  brazo oscilante     : {abs(brazo_virtual):7.1f} mm")
    print(f"  centro de balanceo  : {base['altura_cb']:7.1f} mm\n")

    recorridos = np.linspace(-RECORRIDO, RECORRIDO, 61)
    estados = [s.estado(r) for r in recorridos]

    with open("cinematica_barrido.dat", "w", encoding="ascii") as f:
        f.write("recorrido caida via altura_cb bump_bueno bump_malo\n")
        for e in estados:
            f.write(f"{e['recorrido']:.3f} {e['caida']:.5f} {e['via']:.3f} "
                    f"{e['altura_cb']:.4f} {e['bump_bueno']:.5f} "
                    f"{e['bump_malo']:.5f}\n")

    print(f"{'recorrido':>10} {'caida':>9} {'via':>9} {'centro bal.':>12} "
          f"{'bump ok':>9} {'bump mal':>9}")
    for e in estados[::10]:
        print(f"{e['recorrido']:10.1f} {e['caida']:9.3f} {e['via']:9.1f} "
              f"{e['altura_cb']:12.1f} {e['bump_bueno']:9.3f} "
              f"{e['bump_malo']:9.3f}")

    # Ganancia de caida y variacion de via, por derivada central en el centro
    i = len(estados) // 2
    paso = estados[i + 1]["recorrido"] - estados[i - 1]["recorrido"]
    ganancia = (estados[i + 1]["caida"] - estados[i - 1]["caida"]) / paso
    scrub = (estados[i + 1]["via"] - estados[i - 1]["via"]) / (2 * paso)
    print(f"\nEn posicion de reposo:")
    print(f"  ganancia de caida  : {ganancia:.4f} deg/mm "
          f"({25 * ganancia:.2f} deg por 25 mm)")
    print(f"  variacion de via   : {scrub:.4f} mm por mm de recorrido")
    print(f"  migracion del CB   : "
          f"{(estados[i+1]['altura_cb'] - estados[i-1]['altura_cb']) / paso:.3f}"
          f" mm/mm")
    print("\nEscrito cinematica_barrido.dat")


if __name__ == "__main__":
    main()
