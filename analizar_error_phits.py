"""
Lee un tally [T-Deposit] de PHITS (formato ANGEL) junto con su archivo de
error asociado (el que termina en "_err.out", que PHITS genera automaticamente
al lado del archivo de valores) y arma un mapa de calor del error relativo
por voxel, capa por capa, mucho mas facil de leer que las paginas del PDF.

Uso:
    python analizar_error_phits.py deposit_electron.out deposit_electron_err.out
    python analizar_error_phits.py deposit_electron.out deposit_electron_err.out --capas 5 6 7
    python analizar_error_phits.py deposit_electron.out deposit_electron_err.out --umbral 0.2

Genera:
  - un resumen numerico por consola (error minimo/maximo/mediana/promedio,
    y cuantos voxeles superan el umbral de error), calculado solo sobre
    voxeles con dosis > 0 (en los voxeles sin dosis el "error" que reporta
    PHITS es un valor de relleno sin significado estadistico real)
  - una figura .png con, para cada capa pedida, el mapa de dosis (log) y el
    mapa de error relativo (0-100%) lado a lado
"""
import argparse
import re
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# misma logica de lectura que leer_dosis_phits.py, reutilizada para poder
# leer tanto el archivo de valores como el de error (tienen el mismo formato)
NUM_LINE = re.compile(r'^[\s]*(-?\d\.\d+E[+-]\d+[\s]*)+$')
PAGE_HEADER = re.compile(r'no\.\s*=\s*(\d+)\s*i[xyz]\s*=\s*(\d+)')


def leer_tally(path):
    """Devuelve {indice_de_pagina: [121 valores]} (grilla 11x11 por pagina)."""
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


def estadisticas_error(paginas_valor, paginas_error, umbral):
    """Imprime un resumen del error relativo, solo sobre voxeles con dosis > 0."""
    errores_validos = []
    total_con_dosis = 0
    total_sobre_umbral = 0

    for pagina, valores in paginas_valor.items():
        errores = paginas_error.get(pagina)
        if errores is None:
            continue
        for v, e in zip(valores, errores):
            if v > 0:
                total_con_dosis += 1
                errores_validos.append(e)
                if e > umbral:
                    total_sobre_umbral += 1

    if not errores_validos:
        print("  no hay voxeles con dosis > 0 para calcular estadisticas de error")
        return

    arr = np.array(errores_validos)
    print(f"  voxeles con dosis > 0: {total_con_dosis}")
    print(f"  error relativo -> min: {arr.min()*100:.1f}%  "
          f"mediana: {np.median(arr)*100:.1f}%  "
          f"promedio: {arr.mean()*100:.1f}%  "
          f"max: {arr.max()*100:.1f}%")
    print(f"  voxeles con error > {umbral*100:.0f}%: "
          f"{total_sobre_umbral} ({100*total_sobre_umbral/total_con_dosis:.1f}% del total con dosis)")


def graficar(paginas_valor, paginas_error, capas, out_png):
    """Una fila por capa pedida: mapa de dosis (log) a la izquierda,
    mapa de error relativo (0-100%) a la derecha."""
    capas_validas = [c for c in capas if c in paginas_valor and c in paginas_error]
    if not capas_validas:
        print(f"  ninguna de las capas pedidas {capas} tiene datos (paginas "
              f"disponibles: {sorted(paginas_valor.keys())})")
        return

    fig, axes = plt.subplots(len(capas_validas), 2,
                              figsize=(9, 4 * len(capas_validas)), squeeze=False)

    for fila, capa in enumerate(capas_validas):
        valor = np.array(paginas_valor[capa]).reshape(11, 11)
        error = np.array(paginas_error[capa]).reshape(11, 11)
        error_pct = np.where(valor > 0, error * 100, np.nan)  # NaN = sin dosis, error no aplica

        ax_v = axes[fila][0]
        valor_plot = np.where(valor > 0, valor, np.nan)
        im_v = ax_v.imshow(valor_plot, origin='lower', cmap='viridis',
                            norm=matplotlib.colors.LogNorm())
        ax_v.set_title(f"Dosis - capa z (iz={capa})")
        fig.colorbar(im_v, ax=ax_v, label="Gy/source")

        ax_e = axes[fila][1]
        im_e = ax_e.imshow(error_pct, origin='lower', cmap='inferno_r',
                            vmin=0, vmax=min(100, np.nanmax(error_pct)) if np.any(~np.isnan(error_pct)) else 100)
        ax_e.set_title(f"Error relativo (%) - capa z (iz={capa})")
        fig.colorbar(im_e, ax=ax_e, label="% error")

    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    print(f"  figura guardada en: {out_png}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("valor", help="archivo .out con los valores (ej. deposit_electron.out)")
    ap.add_argument("error", help="archivo _err.out con el error (ej. deposit_electron_err.out)")
    ap.add_argument("--capas", type=int, nargs="+", default=[5, 6, 7],
                     help="indices de capa (iz) a graficar (default: 5 6 7)")
    ap.add_argument("--umbral", type=float, default=0.2,
                     help="umbral de error relativo para el resumen, como fraccion (default: 0.2 = 20%%)")
    ap.add_argument("--out", default="error_phits.png",
                     help="nombre del png de salida (default: error_phits.png)")
    args = ap.parse_args()

    paginas_valor = leer_tally(args.valor)
    paginas_error = leer_tally(args.error)

    if not paginas_valor or not paginas_error:
        print("no se pudo leer alguno de los dos archivos")
        sys.exit(1)

    print(f"--- {args.valor} / {args.error} ---")
    estadisticas_error(paginas_valor, paginas_error, args.umbral)
    graficar(paginas_valor, paginas_error, args.capas, args.out)


if __name__ == "__main__":
    main()
