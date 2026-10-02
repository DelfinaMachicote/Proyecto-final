"""
Compara el error relativo entre dos corridas identicas salvo por el valor
de isbias (0 = default, historias proporcionales al peso del voxel; 2 =
misma cantidad de historias por voxel activo, ajustando el peso
estadistico), para responder: en las zonas de la fuente con menor
intensidad (peso 0.6), ¿isbias=2 mejora el error de forma significativa,
o no vale la pena?

Requiere que ambas carpetas tengan los mismos nombres de archivo de salida
(deposit_electron.out + _err.out, deposit_photon.out + _err.out,
robot-deposit-xz.out + _err.out) sobre la MISMA geometria y fuente (mismas
zonas rectangulares), corridas con el mismo maxcas/maxbch para que la
comparacion sea justa.

Uso:
    python comparar_isbias.py

(las rutas de las dos carpetas se configuran abajo, en CARPETA_ISBIAS0 /
CARPETA_ISBIAS2)
"""
import re
from pathlib import Path

import numpy as np

# %% [CONFIGURACION] ----------------------------------------------------------
# Path(__file__) ancla las rutas a la ubicacion de este script (Prueba/), sin
# importar el directorio de trabajo desde donde lo corras (VS Code, terminal, etc).
_BASE = Path(__file__).resolve().parent
CARPETA_ISBIAS0 = _BASE / "FuenteVoxelizada-FantomaHeterogeneo-ZonasRectangulares-Isbias0"
CARPETA_ISBIAS2 = _BASE / "FuenteVoxelizada-FantomaHeterogeneo-ZonasRectangulares"

ARCHIVO_VALOR = "robot-deposit-xz.out"       # tally "total" (electron+photon)
ARCHIVO_ERROR = "robot-deposit-xz_err.out"

# Zonas de la fuente (documentadas en el .inp, convertidas a indices 0-based:
# fila/columna 0-based = fila/columna documentada en el .inp menos 1).
# etiqueta -> (capa iz, filas, columnas, peso de la fuente en esa zona)
ZONAS = {
    "z=5 (peso 0.6)": (5, range(7, 9), range(1, 5), 0.6),
    "z=6 (peso 1.0)": (6, range(1, 4), range(5, 10), 1.0),
    "z=7 (peso 0.6)": (7, range(5, 6), range(2, 9), 0.6),
}

# %% [LECTURA] -----------------------------------------------------------------
NUM_LINE = re.compile(r'^[\s]*(-?\d\.\d+E[+-]\d+[\s]*)+$')
PAGE_HEADER = re.compile(r'no\.\s*=\s*(\d+)\s*i[xyz]\s*=\s*(\d+)')


def leer_tally(path):
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


def valores_de_zona(paginas_valor, paginas_error, capa, filas, columnas):
    """Devuelve (dosis, errores) de los voxeles de una zona, ya reshapeados
    a grillas 11x11 por capa."""
    valor = np.array(paginas_valor[capa]).reshape(11, 11)
    error = np.array(paginas_error[capa]).reshape(11, 11)
    dosis = [valor[f, c] for f in filas for c in columnas]
    errores = [error[f, c] for f in filas for c in columnas]
    return dosis, errores


def resumen_run(carpeta, etiqueta_run):
    paginas_valor = leer_tally(carpeta / ARCHIVO_VALOR)
    paginas_error = leer_tally(carpeta / ARCHIVO_ERROR)
    print(f"=== {etiqueta_run} ({carpeta}) ===")
    resultado = {}
    for etiqueta_zona, (capa, filas, columnas, peso) in ZONAS.items():
        dosis, errores = valores_de_zona(paginas_valor, paginas_error, capa, filas, columnas)
        arr_e = np.array(errores) * 100
        arr_d = np.array(dosis)
        print(f"  {etiqueta_zona}: dosis media = {arr_d.mean():.3e} Gy/source, "
              f"error mediana = {np.median(arr_e):.1f}%, "
              f"error medio = {arr_e.mean():.1f}%, "
              f"error max = {arr_e.max():.1f}%  ({len(errores)} voxeles)")
        resultado[etiqueta_zona] = np.median(arr_e)
    print()
    return resultado


def main():
    res0 = resumen_run(CARPETA_ISBIAS0, "isbias=0")
    res2 = resumen_run(CARPETA_ISBIAS2, "isbias=2")

    print("=== Comparacion (error mediana, isbias=0 vs isbias=2) ===")
    for etiqueta_zona in ZONAS:
        e0 = res0[etiqueta_zona]
        e2 = res2[etiqueta_zona]
        mejora = 100 * (e0 - e2) / e0 if e0 else float('nan')
        print(f"  {etiqueta_zona}: {e0:.1f}%  ->  {e2:.1f}%  "
              f"(mejora relativa: {mejora:+.0f}%)")
    print()
    print("Si la mejora relativa en las zonas de peso 0.6 es chica (por ejemplo")
    print("menor a la de la zona de peso 1.0, o menor a ~10-20%), isbias=2 no")
    print("esta ayudando mucho ahi y puede no justificar el uso. Si en cambio")
    print("la mejora es grande justo en las zonas de baja intensidad, es donde")
    print("isbias=2 esta cumpliendo su funcion.")


if __name__ == "__main__":
    main()
