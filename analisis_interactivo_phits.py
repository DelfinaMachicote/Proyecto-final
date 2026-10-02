"""
Analisis interactivo de una corrida de PHITS (tally [T-Deposit]): perfil de
dosis + mapa de error relativo, pensado para correr celda por celda en VS
Code (con la extension de Python, "Run Cell" arriba de cada "# %%") en vez
de por linea de comandos.

Como usarlo:
  1. Abrir este archivo en VS Code.
  2. Editar la seccion "CONFIGURACION" de abajo con la carpeta y los
     archivos que quieras analizar.
  3. Correr las celdas en orden (con "Run Cell" o Ctrl+Enter/Shift+Enter).
     Cada grafico se abre en el panel de "Python Interactive" de VS Code y
     ademas se guarda como .png en la carpeta actual.

Reutiliza la misma logica de lectura que leer_dosis_phits.py, perfil_dosis.py
y analizar_error_phits.py (formato ANGEL de los .out de PHITS).
"""

# %% [CONFIGURACION] -- editar esto segun la corrida que quieras mirar --------
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Si este script vive junto a los .out (adentro de la carpeta de la corrida),
# usar: CARPETA = Path(__file__).resolve().parent
# Si vive en Prueba/ (un nivel arriba de las carpetas de corrida), poner el
# nombre de la subcarpeta a analizar:
CARPETA = Path(__file__).resolve().parent / "FuenteVoxelizada-FantomaHeterogeneo-ZonasRectangulares"

# etiqueta -> archivo de valores (dosis)
ARCHIVOS_DOSIS = {
    "electrones": CARPETA / "deposit_electron.out",
    "fotones": CARPETA / "deposit_photon.out",
    "total": CARPETA / "robot-deposit-xz.out",
}

# etiqueta -> archivo de error relativo (mismo nombre + "_err")
ARCHIVOS_ERROR = {
    "electrones": CARPETA / "deposit_electron_err.out",
    "fotones": CARPETA / "deposit_photon_err.out",
    "total": CARPETA / "robot-deposit-xz_err.out",
}

# archivo .inp de la corrida (de aca se lee el tipo de tejido por voxel,
# bloque fill= del [Cell])
ARCHIVO_INP = CARPETA / "I131-Voxelizada-Heterogeneo.inp"

# fila a usar para el perfil de dosis (se grafican las 11 capas para esa
# misma fila). fila=5 pasa por el centro de la cruz de hueso (iz=5,6,7);
# para ver el rectangulo de peso 1.0 de la fuente (iz=6, filas 2-4) usar
# fila=3, pero ahi no hay hueso en esta fila.
FILA_PERFIL = 5

# capas a mirar en el mapa de error (las tres zonas de la fuente)
CAPAS_ERROR = [5, 6, 7]
UMBRAL_ERROR = 0.2  # 20%, para el resumen numerico

# %% [LECTURA] -- funciones de parseo, no hace falta tocarlas ----------------
NUM_LINE = re.compile(r'^[\s]*(-?\d\.\d+E[+-]\d+[\s]*)+$')
PAGE_HEADER = re.compile(r'no\.\s*=\s*(\d+)\s*i[xyz]\s*=\s*(\d+)')
CELL_ROW = re.compile(r'^\s*(\d+(?:\s+\d+){10})\s*(?:\$.*)?$', re.MULTILINE)

# nombre de cada material segun el codigo usado en el bloque fill= del [Cell]
# (ver comentario "2 = agua, 3 = hueso ICRU" en el .inp)
TEJIDOS = {2: "Agua", 3: "Hueso"}
COLOR_TEJIDO = {2: "tab:blue", 3: "tab:orange"}


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


def perfil(path, capa=None, fila=None):
    """Devuelve (posiciones_x, dosis) de una fila de una capa dada.
    Si no se especifican capa/fila, usa la capa central y su fila central
    (como perfil_dosis.py)."""
    paginas = leer_tally(path)
    if not paginas:
        raise RuntimeError(f"no se pudo leer ninguna pagina de datos en {path}")
    n = len(paginas)
    capa = capa if capa is not None else sorted(paginas.keys())[n // 2]
    valores = paginas[capa]
    lado = int(len(valores) ** 0.5)  # 11
    fila = fila if fila is not None else lado // 2
    fila_valores = valores[fila * lado: fila * lado + lado]

    paso = 0.4
    x0 = -2.0
    posiciones = [x0 + k * paso for k in range(lado)]
    return posiciones, fila_valores


def leer_material_grid(inp_path):
    """Lee el bloque fill= del [Cell] del .inp (voxel universe: 2=agua,
    3=hueso) y devuelve {capa (iz, 1..11): [11 filas de 11 materiales]},
    con el mismo orden fila/capa que usan leer_tally/perfil para los
    tallies (ambos bloques fueron corregidos juntos para el flip en y,
    asi que quedan alineados en el mismo orden de impresion)."""
    texto = open(inp_path, encoding='utf-8', errors='replace').read()
    inicio = texto.index("[ C e l l ]")
    fin = texto.index("[ surface ]")
    bloque = texto[inicio:fin]
    filas_txt = CELL_ROW.findall(bloque)
    if len(filas_txt) != 121:
        raise RuntimeError(
            f"se esperaban 121 filas de material (11 capas x 11 filas) en "
            f"[Cell], se encontraron {len(filas_txt)}. Revisar el formato "
            f"del bloque fill= en {inp_path}.")
    filas = [[int(x) for x in f.split()] for f in filas_txt]
    return {capa: filas[(capa - 1) * 11: capa * 11] for capa in range(1, 12)}


# %% [PERFIL DE DOSIS -- todas las capas, con tipo de tejido] ----------------
piso = 1e-18  # valor minimo para poder graficar en escala log (evita log(0))
material_grid = leer_material_grid(ARCHIVO_INP)
paginas_total = leer_tally(ARCHIVOS_DOSIS["total"])
capas = sorted(paginas_total.keys())

# rango de dosis compartido entre subplots, para poder comparar capas entre si
todos_los_valores = [v for pagina in paginas_total.values() for v in pagina if v > 0]
ymin, ymax = min(todos_los_valores) * 0.5, max(todos_los_valores) * 2

ncols = 3
nrows = -(-len(capas) // ncols)  # redondeo hacia arriba
fig, axes = plt.subplots(nrows, ncols, figsize=(4.5 * ncols, 3.5 * nrows), sharey=True)
axes = axes.flatten()

for idx, capa in enumerate(capas):
    ax = axes[idx]
    posiciones, dosis = perfil(ARCHIVOS_DOSIS["total"], capa=capa, fila=FILA_PERFIL)
    materiales_fila = material_grid[capa][FILA_PERFIL]
    dosis_graf = [max(d, piso) for d in dosis]

    ax.semilogy(posiciones, dosis_graf, '-', color='0.6', linewidth=1, zorder=1)
    colores = [COLOR_TEJIDO.get(m, 'gray') for m in materiales_fila]
    ax.scatter(posiciones, dosis_graf, c=colores, zorder=2, s=35, edgecolor='k', linewidth=0.3)

    ax.set_title(f"iz={capa}")
    ax.set_ylim(ymin, ymax)
    ax.grid(True, alpha=0.3, which="both")

    print(f"capa iz={capa}, fila={FILA_PERFIL}:")
    for x, d, m in zip(posiciones, dosis, materiales_fila):
        print(f"  x = {x:+.1f} cm   dosis = {d:.4e} Gy/source   tejido = {TEJIDOS.get(m, m)}")
    print()

for ax in axes[len(capas):]:
    ax.axis('off')

from matplotlib.lines import Line2D
leyenda = [Line2D([0], [0], marker='o', color='w', markerfacecolor=color,
                   markeredgecolor='k', label=nombre, markersize=8)
           for m, nombre in TEJIDOS.items() for color in [COLOR_TEJIDO[m]]]
fig.suptitle(f"Perfil de dosis total, todas las capas (fila={FILA_PERFIL})", y=0.995)
fig.legend(handles=leyenda, loc='upper center', bbox_to_anchor=(0.5, 0.965), ncol=len(leyenda))
fig.supxlabel("posicion x [cm]")
fig.supylabel("dosis [Gy/source]  (escala log)")
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(CARPETA / "perfil_dosis_interactivo.png", dpi=150)
plt.show()

# %% [ERROR RELATIVO -- resumen numerico] -------------------------------------
for etiqueta in ARCHIVOS_DOSIS:
    paginas_valor = leer_tally(ARCHIVOS_DOSIS[etiqueta])
    paginas_error = leer_tally(ARCHIVOS_ERROR[etiqueta])

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
                if e > UMBRAL_ERROR:
                    total_sobre_umbral += 1

    print(f"--- {etiqueta} ---")
    if not errores_validos:
        print("  no hay voxeles con dosis > 0")
        continue
    arr = np.array(errores_validos)
    print(f"  voxeles con dosis > 0: {total_con_dosis}")
    print(f"  error relativo -> min: {arr.min()*100:.1f}%  "
          f"mediana: {np.median(arr)*100:.1f}%  "
          f"promedio: {arr.mean()*100:.1f}%  "
          f"max: {arr.max()*100:.1f}%")
    print(f"  voxeles con error > {UMBRAL_ERROR*100:.0f}%: "
          f"{total_sobre_umbral} ({100*total_sobre_umbral/total_con_dosis:.1f}%)")
    print()

# %% [ERROR RELATIVO -- mapas de calor por capa] ------------------------------
etiqueta_mapa = "total"  # cambiar por "electrones" o "fotones" si se quiere
paginas_valor = leer_tally(ARCHIVOS_DOSIS[etiqueta_mapa])
paginas_error = leer_tally(ARCHIVOS_ERROR[etiqueta_mapa])

capas_validas = [c for c in CAPAS_ERROR if c in paginas_valor and c in paginas_error]
fig, axes = plt.subplots(len(capas_validas), 2,
                          figsize=(9, 4 * len(capas_validas)), squeeze=False)

for fila_idx, capa in enumerate(capas_validas):
    valor = np.array(paginas_valor[capa]).reshape(11, 11)
    error = np.array(paginas_error[capa]).reshape(11, 11)
    error_pct = np.where(valor > 0, error * 100, np.nan)

    ax_v = axes[fila_idx][0]
    valor_plot = np.where(valor > 0, valor, np.nan)
    im_v = ax_v.imshow(valor_plot, origin='lower', cmap='viridis',
                        norm=plt.matplotlib.colors.LogNorm())
    ax_v.set_title(f"Dosis ({etiqueta_mapa}) - capa iz={capa}")
    fig.colorbar(im_v, ax=ax_v, label="Gy/source")

    ax_e = axes[fila_idx][1]
    vmax = np.nanmax(error_pct) if np.any(~np.isnan(error_pct)) else 100
    im_e = ax_e.imshow(error_pct, origin='lower', cmap='inferno_r',
                        vmin=0, vmax=min(100, vmax))
    ax_e.set_title(f"Error relativo (%) - capa iz={capa}")
    fig.colorbar(im_e, ax=ax_e, label="% error")

fig.tight_layout()
fig.savefig(CARPETA / "error_interactivo.png", dpi=150)
plt.show()