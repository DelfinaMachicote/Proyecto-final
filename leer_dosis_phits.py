"""
Lee un archivo de salida de un tally [T-Deposit] de PHITS (formato ANGEL,
por ejemplo "robot-deposit-xz.out") y extrae la dosis por voxel.

Uso:
    python leer_dosis_phits.py archivo1.out archivo2.out ...

Para cada archivo imprime:
  - la dosis en el voxel central del fantoma (x=0, y=0, z=0)
  - la dosis total sumada en la capa central (11x11 voxeles)
  - la dosis total sumada en todo el fantoma (11x11x11 voxeles)

Funciona tanto si el tally usa axis=xy (páginas en z, "iz = N") como
axis=xz (páginas en y, "iy = N"), ya que ambos casos listan 11 páginas
de 11x11 valores que juntas cubren el fantoma completo de 1331 voxeles.
"""
import re
import sys

# una linea de datos es una seguidilla de numeros en notacion cientifica,
# por ejemplo "  5.248E-17  0.000E+00  5.711E-15 ..."
NUM_LINE = re.compile(r'^[\s]*(-?\d\.\d+E[+-]\d+[\s]*)+$')

# encabezado de cada pagina, ej: "#   no. =  6   iz  =  6   part. = all"
PAGE_HEADER = re.compile(r'no\.\s*=\s*(\d+)\s*i[xyz]\s*=\s*(\d+)')


def leer_tally_deposit(path):
    """Devuelve un diccionario {indice_de_pagina: [121 valores de dosis]}."""
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

        # cada pagina tiene DOS bloques que empiezan con "hc:": el de los
        # datos de dosis y, mas abajo, uno del dibujo de la geometria
        # (gshow) que no nos interesa. Nos quedamos solo con el primero.
        if linea.strip().startswith('hc:') and pagina_actual is not None \
                and pagina_actual not in paginas:
            valores = []
            j = i + 1
            while j < len(lineas) and NUM_LINE.match(lineas[j]):
                valores.extend(float(x) for x in lineas[j].split())
                j += 1
            if len(valores) == 121:  # 11 x 11, una pagina completa
                paginas[pagina_actual] = valores
            i = j
            continue

        i += 1
    return paginas


def analizar(path):
    paginas = leer_tally_deposit(path)
    if not paginas:
        print(f"  no se pudo leer ninguna pagina de datos en {path}")
        return

    n_paginas = len(paginas)
    pagina_central = sorted(paginas.keys())[n_paginas // 2]
    valores_centrales = paginas[pagina_central]

    lado = int(len(valores_centrales) ** 0.5)  # normalmente 11
    fila_central = valores_centrales[(lado // 2) * lado: (lado // 2) * lado + lado]
    dosis_voxel_central = fila_central[lado // 2]

    dosis_capa_central = sum(valores_centrales)
    dosis_total = sum(sum(v) for v in paginas.values())

    print(f"  paginas leidas: {n_paginas} (se esperaban {lado})")
    print(f"  dosis voxel central (x=0,y=0,z=0): {dosis_voxel_central:.6e} Gy/source")
    print(f"  dosis total capa central ({lado}x{lado}): {dosis_capa_central:.6e} Gy/source")
    print(f"  dosis total en el fantoma ({lado}x{lado}x{lado}): {dosis_total:.6e} Gy/source")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("uso: python leer_dosis_phits.py archivo1.out [archivo2.out ...]")
        sys.exit(1)
    for path in sys.argv[1:]:
        print(f"--- {path} ---")
        analizar(path)
        print()
