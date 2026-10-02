"""
Mapa de dosis 3D, curvas de isodosis y DVH (histograma dosis-volumen) a
partir de un tally [T-Deposit] de PHITS (formato ANGEL), para completar
los tipos de salida que todavia faltaban (antes solo habia perfil de
dosis y mapa de error -- ver perfil_dosis.py y analizar_error_phits.py).

Reutiliza el mismo parser de archivos .out que el resto de los scripts
de esta carpeta (misma logica que leer_dosis_phits.py).

Uso:
    python mapas_dosis_3d.py robot-deposit-xz.out
    python mapas_dosis_3d.py robot-deposit-xz.out --niveles 90 50 10
    python mapas_dosis_3d.py robot-deposit-xz.out --out-prefix escenario4

Genera 3 figuras .png:
  <prefix>_isodosis.png : una fila de contornos de isodosis (% de la dosis
                           maxima del tally) por cada capa z, superpuestos
                           al mapa de dosis
  <prefix>_dvh.png       : histograma dosis-volumen acumulado (DVH),
                           fraccion de volumen que recibe >= D, para todo
                           el fantoma
  <prefix>_mapa3d.png    : mapa de dosis 3D simplificado (voxels de
                           matplotlib), mostrando solo los voxeles por
                           encima de cada nivel de isodosis pedido, en
                           capas de transparencia/color distintas (no es
                           un isosurface real, pero sirve para ver la
                           forma 3D de la distribucion sin depender de
                           libreria extra como scikit-image)
"""
import argparse
import re
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (necesario para projection='3d')
import numpy as np

NUM_LINE = re.compile(r'^[\s]*(-?\d\.\d+E[+-]\d+[\s]*)+$')
PAGE_HEADER = re.compile(r'no\.\s*=\s*(\d+)\s*i[xyz]\s*=\s*(\d+)')


def leer_tally(path):
    """Devuelve {indice_de_pagina: [N*N valores]} (una grilla NxN por pagina,
    tipicamente 11x11 en los escenarios actuales)."""
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
            if valores:
                paginas[pagina_actual] = valores
            i = j
            continue
        i += 1
    return paginas


def paginas_a_volumen(paginas):
    """Arma un array 3D (nz, lado, lado) a partir de las paginas, ordenadas
    por indice de pagina (que PHITS numera 1..nz)."""
    indices = sorted(paginas.keys())
    lado = int(round(len(paginas[indices[0]]) ** 0.5))
    vol = np.zeros((len(indices), lado, lado))
    for k, idx in enumerate(indices):
        vol[k] = np.array(paginas[idx]).reshape(lado, lado)
    return vol, indices


def graficar_isodosis(vol, indices, niveles_pct, out_png):
    dmax = vol.max()
    if dmax <= 0:
        print("  dosis maxima es 0, no se puede graficar isodosis")
        return
    nz = vol.shape[0]
    fig, axes = plt.subplots(1, nz, figsize=(3.2 * nz, 3.2), squeeze=False)
    niveles_abs = [dmax * p / 100.0 for p in niveles_pct]
    for k in range(nz):
        ax = axes[0][k]
        capa = vol[k]
        capa_plot = np.where(capa > 0, capa, np.nan)
        im = ax.imshow(capa_plot, origin='lower', cmap='viridis')
        if np.any(capa > 0):
            cs = ax.contour(capa, levels=sorted(niveles_abs), colors='white', linewidths=1.0)
            ax.clabel(cs, fmt=lambda v: f"{100*v/dmax:.0f}%", fontsize=6)
        ax.set_title(f"iz={indices[k]}", fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle("Curvas de isodosis (% de la dosis maxima del tally), por capa z")
    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    print(f"  figura guardada en: {out_png}")


def graficar_dvh(vol, out_png):
    """DVH acumulado: fraccion de volumen que recibe >= D, para D de 0 a
    dmax. Todos los voxeles tienen el mismo volumen en este fantoma, asi
    que 'volumen' = cantidad de voxeles (no hace falta pesar por mascara
    de organo todavia porque el fantoma completo ES la region de interes)."""
    valores = vol.flatten()
    dmax = valores.max()
    if dmax <= 0:
        print("  dosis maxima es 0, no se puede graficar DVH")
        return
    niveles_D = np.linspace(0, dmax, 200)
    frac_volumen = [np.mean(valores >= d) for d in niveles_D]

    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.plot(niveles_D / dmax * 100, np.array(frac_volumen) * 100)
    ax.set_xlabel("Dosis (% de la dosis maxima)")
    ax.set_ylabel("Volumen que recibe >= esa dosis (%)")
    ax.set_title("DVH acumulado")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    print(f"  figura guardada en: {out_png}")

    # algunos puntos de referencia comunes en DVH (D90, D50, etc. del lado
    # "dosis que recibe el X% del volumen")
    for pct_vol in (90, 50, 10):
        frac = pct_vol / 100.0
        # dosis minima tal que al menos 'frac' del volumen la recibe
        candidatos = [d for d, fv in zip(niveles_D, frac_volumen) if fv >= frac]
        d_x = max(candidatos) if candidatos else 0.0
        print(f"  D{pct_vol} (dosis que recibe >= {pct_vol}% del volumen): "
              f"{d_x:.3e} Gy/source ({100*d_x/dmax:.1f}% de la dosis maxima)")


def graficar_mapa3d(vol, niveles_pct, out_png):
    dmax = vol.max()
    if dmax <= 0:
        print("  dosis maxima es 0, no se puede graficar el mapa 3D")
        return
    fig = plt.figure(figsize=(7, 7))
    ax = fig.add_subplot(111, projection='3d')

    colores = plt.cm.viridis(np.linspace(0.2, 0.95, len(niveles_pct)))
    niveles_ordenados = sorted(niveles_pct)  # de menor a mayor, para dibujar
    # las "cascaras" grandes primero y las chicas (mas opacas) encima
    for nivel, color in zip(niveles_ordenados, colores):
        umbral = dmax * nivel / 100.0
        mascara = vol >= umbral
        if not mascara.any():
            continue
        ax.voxels(mascara, facecolors=color, edgecolor=None,
                  alpha=0.35 + 0.5 * (nivel / 100.0))

    ax.set_xlabel("x (voxel)")
    ax.set_ylabel("y (voxel)")
    ax.set_zlabel("z (voxel)")
    ax.set_title(f"Mapa de dosis 3D (cascaras de isodosis: {sorted(niveles_pct)}% de la maxima)")
    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    print(f"  figura guardada en: {out_png}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("archivo", help="tally .out (ej. robot-deposit-xz.out)")
    ap.add_argument("--niveles", type=float, nargs="+", default=[90, 50, 10],
                     help="niveles de isodosis en %% de la dosis maxima (default: 90 50 10)")
    ap.add_argument("--out-prefix", default="dosis",
                     help="prefijo para los 3 .png de salida (default: dosis)")
    args = ap.parse_args()

    paginas = leer_tally(args.archivo)
    if not paginas:
        print(f"no se pudo leer ninguna pagina de datos en {args.archivo}")
        sys.exit(1)

    vol, indices = paginas_a_volumen(paginas)
    print(f"--- {args.archivo} ---")
    print(f"  volumen leido: {vol.shape} (nz, ny, nx), paginas z: {indices}")
    print(f"  dosis maxima: {vol.max():.3e} Gy/source, dosis total: {vol.sum():.3e} Gy/source")

    graficar_isodosis(vol, indices, args.niveles, f"{args.out_prefix}_isodosis.png")
    graficar_dvh(vol, f"{args.out_prefix}_dvh.png")
    graficar_mapa3d(vol, args.niveles, f"{args.out_prefix}_mapa3d.png")


if __name__ == "__main__":
    main()
