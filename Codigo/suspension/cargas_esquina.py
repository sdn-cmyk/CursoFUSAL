"""
Cargas en las barras de una esquina de suspension.
Curso de Ingenieria FUSAL - capitulo 19.

Que hace
--------
Dada una fuerza en la huella de contacto, reparte esa carga entre las seis
barras biarticuladas de una esquina de doble trapecio (cuatro brazos de
trapecio, tirante de direccion y pushrod) resolviendo el equilibrio de la
mangueta como solido rigido.

El planteamiento es el del capitulo 5: la mangueta esta en equilibrio bajo la
fuerza de la huella mas las seis fuerzas axiales de las barras. Son seis
incognitas y seis ecuaciones -- tres de fuerzas y tres de momentos -- asi que
el sistema es isostatico y se resuelve de una sola vez.

    [ u_1 ... u_6 ] [N_1]   [ -F  ]
    [ r_1xu_1 ...  ] [...] = [ -M  ]
                     [N_6]

donde u_i es el vector unitario de cada barra y r_i el vector del punto de
aplicacion respecto al centro de reduccion.

Signo: N positivo = TRACCION.

Limitaciones
------------
Supone barras biarticuladas ideales, sin rozamiento ni holguras, y la mangueta
infinitamente rigida. Si algun extremo no gira libre, esa barra tambien flecta
y este calculo se queda corto: hay que ir al FEA.

Uso
---
    python cargas_esquina.py

Requiere numpy. Coordenadas en mm, fuerzas en N.
"""

import numpy as np

G = 9.81

# =====================================================================
#  Geometria de EJEMPLO de la esquina delantera izquierda, en
#  coordenadas del coche: x hacia delante, y a la derecha, z hacia
#  arriba. Origen en la proyeccion del centro de rueda sobre el suelo.
#  NO son nuestros puntos duros.
# =====================================================================
PUNTOS = {
    # extremos en la mangueta
    "rotula_inf":  np.array([   0.0,  -45.0, 120.0]),
    "rotula_sup":  np.array([   0.0,  -60.0, 300.0]),
    "tirante_ext": np.array([ -70.0,  -70.0, 165.0]),
    "pushrod_ext": np.array([  10.0,  -50.0, 135.0]),
    # extremos en el chasis
    "inf_del":     np.array([ 180.0, -415.0, 122.0]),
    "inf_tra":     np.array([-180.0, -415.0, 122.0]),
    "sup_del":     np.array([ 150.0, -385.0, 280.0]),
    "sup_tra":     np.array([-150.0, -385.0, 280.0]),
    "tirante_int": np.array([-190.0, -405.0, 161.0]),
    "pushrod_int": np.array([  10.0, -230.0, 520.0]),
}

# Cada barra: (nombre, punto en la mangueta, punto en el chasis)
BARRAS = [
    ("trapecio inf. delantero", "rotula_inf",  "inf_del"),
    ("trapecio inf. trasero",   "rotula_inf",  "inf_tra"),
    ("trapecio sup. delantero", "rotula_sup",  "sup_del"),
    ("trapecio sup. trasero",   "rotula_sup",  "sup_tra"),
    ("tirante de direccion",    "tirante_ext", "tirante_int"),
    ("pushrod",                 "pushrod_ext", "pushrod_int"),
]

HUELLA = np.array([0.0, 0.0, 0.0])      # punto de aplicacion de la fuerza
CENTRO_RUEDA = np.array([0.0, 0.0, 230.0])

# Carga estatica de la rueda, en N, y casos de carga en g.
CARGA_ESTATICA = 706.0
CASOS = {
    #  nombre                     ax     ay     az(bump)
    "frenada maxima":           (-1.5,   0.0,   1.0),
    "curva maxima":             ( 0.0,   1.4,   1.0),
    "frenada en curva":         (-1.1,   1.0,   1.0),
    "aceleracion":              ( 1.0,   0.0,   1.0),
    "bache con frenada":        (-1.0,   0.0,   3.0),
    "bordillo (solo vertical)": ( 0.0,   0.0,   3.5),
}


def resolver(fuerza, punto_aplicacion=HUELLA):
    """Devuelve las seis fuerzas axiales, en N, positivas a traccion."""
    matriz = np.zeros((6, 6))
    for j, (_, ext, int_) in enumerate(BARRAS):
        p_ext, p_int = PUNTOS[ext], PUNTOS[int_]
        u = (p_int - p_ext) / np.linalg.norm(p_int - p_ext)
        matriz[0:3, j] = u
        matriz[3:6, j] = np.cross(p_ext, u)     # momento respecto al origen
    termino = np.concatenate([-fuerza, -np.cross(punto_aplicacion, fuerza)])
    if abs(np.linalg.det(matriz)) < 1e-6:
        raise ValueError("mecanismo mal condicionado: barras casi coplanarias")
    return np.linalg.solve(matriz, termino)


def fuerza_del_caso(ax, ay, az):
    """Fuerza en la huella, en N, para un caso dado en g.

    La vertical escala la carga estatica; las horizontales salen de esa
    vertical multiplicada por la aceleracion, que es como se transmite el
    agarre. Es la simplificacion del capitulo 19: conservadora y suficiente
    para dimensionar.
    """
    fz = CARGA_ESTATICA * az
    return np.array([ax * fz, ay * fz, fz])


def main():
    print("Longitudes de barra (comprobacion de que la geometria es sensata)")
    for nombre, ext, int_ in BARRAS:
        largo = np.linalg.norm(PUNTOS[int_] - PUNTOS[ext])
        print(f"  {nombre:26s} {largo:7.1f} mm")

    # Comprobacion: una carga vertical pura debe dar reacciones que sumen
    # exactamente esa carga. Si no, la matriz esta mal montada.
    prueba = resolver(np.array([0.0, 0.0, 1000.0]))
    suma = np.zeros(3)
    for j, (_, ext, int_) in enumerate(BARRAS):
        u = PUNTOS[int_] - PUNTOS[ext]
        suma += prueba[j] * u / np.linalg.norm(u)
    print(f"\nComprobacion con 1000 N verticales: las barras devuelven "
          f"({suma[0]:+.1f}, {suma[1]:+.1f}, {suma[2]:+.1f}) N")
    print(f"  error: {np.linalg.norm(suma + np.array([0, 0, 1000.0])):.6f} N")

    print(f"\n{'caso':<26}" + "".join(f"{n.split()[0][:9]:>10}"
                                      for n, _, _ in BARRAS))
    filas = []
    for nombre, (ax, ay, az) in CASOS.items():
        cargas = resolver(fuerza_del_caso(ax, ay, az))
        filas.append((nombre, cargas))
        print(f"{nombre:<26}" + "".join(f"{c:10.0f}" for c in cargas))

    print("\nEnvolvente por barra (lo que hay que dimensionar):")
    print(f"{'barra':<26}{'traccion':>11}{'compresion':>13}{'caso critico':>28}")
    with open("cargas_barras.dat", "w", encoding="ascii") as f:
        f.write("barra traccion compresion\n")
        for j, (nombre, _, _) in enumerate(BARRAS):
            valores = [c[j] for _, c in filas]
            tmax, cmax = max(valores), min(valores)
            critico = filas[int(np.argmax(np.abs(valores)))][0]
            print(f"{nombre:<26}{tmax:11.0f}{cmax:13.0f}{critico:>28}")
            f.write(f"{j+1} {tmax:.1f} {cmax:.1f}\n")

    print("\nEscrito cargas_barras.dat")
    print("Recuerda: estas son cargas SIN coeficiente de seguridad.")


if __name__ == "__main__":
    main()
