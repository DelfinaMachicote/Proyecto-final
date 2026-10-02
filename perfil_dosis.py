"""
Grafica el perfil de dosis desde el centro del fantoma hasta el borde,
a partir de uno o mas archivos de salida de un tally [T-Deposit] de PHITS
(formato ANGEL, por ejemplo "robot-deposit-xz.out" o "deposit_electron.out").

Toma la fila central de la pagina central (es decir, el corte que pasa
justo por el voxel donde esta la fuente) y grafica la dosis en funcion
de la posicion x, de -2.2 a 2.2 cm.

Uso:
    python perfil_dosis.py "Centro=I131-Centro/robot-deposit-xz.out" "VoxelSolido=I131-VoxelSolido/robot-deposit-xz.out"

Cada argumento es "etiqueta=ruta_al_archivo". La etiqueta es lo que va a
aparecer en la leyenda del grafico. Si no ponés "=etiqueta", usa el
nombre de archivo tal cual.

Guarda el grafico como "perfil_dosis.png" en la carpeta actual.
"""
import re
import sys

NUM_LINE = re.compile(r'^[\s]*(-?\d\.\d+E[+-]\d+[\s]*)+$')
PAGE_HEADER = re.compile(r'no\.\s*=\s*(\d+)\s*i[xyz]\s*=\s*(\d+)')


def leer_tally_deposit(path):
    texto = open(path, encoding='utf-8', errors='replace').read()
    lineas = texto.split('\n')
    paginas = {}
    i = 0
    pagina_actual = None
    while i < len(lineas):
        linea = lineas[i]
        m = PAGE_HEADER.search(linea)
        if m:
            pagina_actual = int(m.group(2))
        if linea.strip().startswith('hc:') and pagina_actual is not None \
                and pagina_actual not in paginas:
            valores = []
            j = i + 1
            while j < len(lineas) and NUM_LINE.match(lineas[j]):
                valores.extend(float(x) for x in lineas[j].split())
                j += 1
            if len(valores) == 121:
                paginas[pagina_actual] = valores
            i = j
            continue
        i += 1
    return paginas


def perfil_central(path):
    """Devuelve (posiciones_x, dosis) tomando la fila central de la pagina central."""
    paginas = leer_tally_deposit(path)
    n = len(paginas)
    if n == 0:
        raise RuntimeError(f"no se pudo leer ninguna pagina de datos en {path}")
    pagina_central = sorted(paginas.keys())[n // 2]
    valores = paginas[pagina_central]
    lado = int(len(valores) ** 0.5)  # 11
    fila_central = valores[(lado // 2) * lado: (lado // 2) * lado + lado]

    # las posiciones van de -2.2+0.2=-2.0 a 2.2-0.2=2.0 cm, en pasos de 0.4 cm
    # (11 voxeles de 0.4 cm, malla total de -2.2 a 2.2)
    paso = 0.4
    x0 = -2.0
    posiciones = [x0 + k * paso for k in range(lado)]
    return posiciones, fila_central


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    plt.figure(figsize=(7, 5))
    piso = 1e-18  # valor minimo para poder graficar en escala log (evita log(0))
    for arg in sys.argv[1:]:
        if '=' in arg:
            etiqueta, path = arg.split('=', 1)
        else:
            etiqueta, path = arg, arg
        posiciones, dosis = perfil_central(path)
        dosis_graf = [max(d, piso) for d in dosis]
        plt.semilogy(posiciones, dosis_graf, marker='o', label=etiqueta)
        print(f"{etiqueta}:")
        for x, d in zip(posiciones, dosis):
            print(f"  x = {x:+.1f} cm   dosis = {d:.4e} Gy/source")
        print()

    plt.xlabel("posicion x [cm]  (0 = centro del fantoma)")
    plt.ylabel("dosis [Gy/source]  (escala log)")
    plt.title("Perfil de dosis: centro -> borde del fantoma")
    plt.legend()
    plt.grid(True, alpha=0.3, which="both")
    plt.tight_layout()
    plt.savefig("perfil_dosis.png", dpi=150)
    print("Grafico guardado como perfil_dosis.png")


if __name__ == "__main__":
    main()
