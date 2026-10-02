"""
Esqueleto del paso de preprocesamiento SPECT/CT -> fantoma voxelizado de
PHITS. Disenado para poder probarse de punta a punta con datos sinteticos
AHORA, y recibir datos DICOM reales de SPECT/CT mas adelante sin tener que
rediseniar el pipeline (solo hay que escribir las funciones de lectura
DICOM, que hoy son placeholders).

Pipeline:
  SPECT cuantitativo (actividad por voxel) -> tabla de intensidades de la
    fuente PHITS (s-type=22)
  CT (unidades Hounsfield por voxel) -> densidad y material por voxel ->
    bloques [Material]/[Cell] de PHITS
  Union de ambos -> archivo .inp completo, listo para pasarle a PHITS

Requiere (instalar si falta): numpy, y para DICOM real mas adelante,
pydicom (pip install pydicom --break-system-packages).

Uso (con datos sinteticos, para probar que el pipeline corre):
    python preprocesamiento_spect_ct.py --demo

Uso (con datos reales, una vez que esten disponibles):
    python preprocesamiento_spect_ct.py --spect carpeta_spect_dicom/ \
        --ct carpeta_ct_dicom/ --out mi_escenario_real.inp
(la carpeta_spect_dicom/ y carpeta_ct_dicom/ deben estar ya registradas/
co-registradas entre si, ya sea porque vienen del mismo estudio SPECT/CT
hibrido -lo usual en rastreo postterapeutico- o porque se registraron con
un software aparte; este script NO hace registro de imagenes)
"""
import argparse

import numpy as np

# %% [1. LECTURA DICOM] -------------------------------------------------------
# TODO: implementar con pydicom cuando haya datos reales. Por ahora son
# placeholders que fallan a proposito (NotImplementedError) para no generar
# un resultado silenciosamente incorrecto si alguien los llama sin
# completarlos.

def leer_spect_dicom(carpeta):
    """Debe devolver (actividad_Bq_ml: array 3D, voxel_size_mm: (dz,dy,dx),
    origen, orientacion). La actividad tiene que venir de una reconstruccion
    CUANTITATIVA (con correcciones de atenuacion, scatter y sensibilidad),
    no de cuentas crudas: un SPECT no cuantitativo no sirve como input
    directo, solo muestra captacion relativa."""
    raise NotImplementedError(
        "Completar con pydicom (pydicom.dcmread) + reconstruccion "
        "cuantitativa. Ver docstring de leer_spect_dicom."
    )


def leer_ct_dicom(carpeta):
    """Debe devolver (unidades_hounsfield: array 3D, voxel_size_mm, origen,
    orientacion). Co-registrado/alineado con el SPECT (ver docstring del
    modulo)."""
    raise NotImplementedError(
        "Completar con pydicom (pydicom.dcmread) + RescaleSlope/Intercept "
        "para pasar de valores crudos a HU. Ver docstring de leer_ct_dicom."
    )


# %% [2. SPECT -> FUENTE PHITS] ------------------------------------------------

def actividad_a_tabla_fuente(actividad_Bq_ml, normalizar=True):
    """Convierte un array 3D de actividad (Bq/ml) en los pesos relativos
    I_ijk que va la tabla de intensidades de s-type=22. PHITS normaliza la
    fuente total con 'norm=1', asi que lo que importa es la PROPORCION
    relativa entre voxeles, no la escala absoluta -- por eso alcanza con
    normalizar por el maximo (o por la suma, da lo mismo para PHITS)."""
    pesos = np.asarray(actividad_Bq_ml, dtype=float)
    pesos = np.clip(pesos, 0, None)  # por las dudas, no deberian existir
                                      # actividades negativas
    if normalizar and pesos.max() > 0:
        pesos = pesos / pesos.max()
    return pesos


def tabla_fuente_a_texto_inp(pesos):
    """Arma el bloque de texto de la tabla I_ijk para pegar despues de
    zmax en el [source] del .inp (mismo formato que los escenarios ya
    armados: una capa z por bloque, filas de N valores separados por
    espacio)."""
    nz = pesos.shape[0]
    lineas = []
    for iz in range(nz):
        lineas.append(f"$ capa z={iz+1}")
        for fila in pesos[iz]:
            lineas.append(' '.join(f"{v:g}" if v else '0' for v in fila))
    return '\n'.join(lineas)


# %% [3. CT -> MATERIAL/DENSIDAD PHITS] ----------------------------------------
# Curva de calibracion HU -> densidad: la misma logica que usa un sistema
# de planificacion de radioterapia (TPS). Esta es una curva simplificada
# de ejemplo (lineal a trozos, puntos de ICRU/Schneider tipicos de agua/
# tejido blando/hueso) -- para la tesis conviene usar la
# curva de calibracion propia del equipo de CT que se vaya a usar (cada
# escaner/protocolo tiene la suya, normalmente provista por el servicio de
# fisica medica del centro), no esta generica.
CURVA_HU_DENSIDAD_EJEMPLO = [
    (-1000, 0.001),   # aire
    (-100, 0.92),      # grasa
    (0, 1.00),         # agua
    (40, 1.05),        # tejido blando / tiroides (ICRP 89)
    (300, 1.3),        # tejido con algo de calcificacion
    (1000, 1.8),        # hueso cortical
    (3000, 2.2),        # hueso muy denso
]


def hu_a_densidad(hu, curva=CURVA_HU_DENSIDAD_EJEMPLO):
    """Interpola linealmente la curva HU->densidad. hu puede ser un array."""
    xs = [p[0] for p in curva]
    ys = [p[1] for p in curva]
    return np.interp(hu, xs, ys)


def hu_a_universo_material(hu, umbral_tejido_denso=150):
    """Clasificacion MINIMA de ejemplo: separa en 2 materiales (tejido
    tiroideo 'blando' vs. una insercion densa), analoga a la que ya usan
    los 4 escenarios sinteticos (m1=tiroides, m2=insercion de alto
    contraste). Para la tesis real probablemente convenga mas de 2
    materiales (al menos agua/tejido blando/hueso, como en un TPS real);
    esto es a proposito un punto de partida simple, no la version final."""
    return np.where(hu >= umbral_tejido_denso, 3, 2)  # universos u=3 / u=2,
                                                        # mismos indices que
                                                        # ya usan los .inp


# %% [4. ENSAMBLADO DEL .inp] --------------------------------------------------

def armar_bloque_fill(universos):
    """Mismo formato que [Cell] fill= en los .inp ya armados."""
    nz = universos.shape[0]
    bloques = []
    for iz in range(nz):
        lineas = ['      ' + ' '.join(str(v) for v in fila) for fila in universos[iz]]
        bloques.append('\n'.join(lineas))
    return '\n\n'.join(bloques)


def resumen_pipeline(pesos_fuente, universos_material):
    nz, ny, nx = pesos_fuente.shape
    print(f"grilla: {nz} x {ny} x {nx} voxeles")
    print(f"voxeles con actividad > 0: {(pesos_fuente > 0).sum()} / {pesos_fuente.size}")
    print(f"voxeles clasificados como insercion densa (u=3): "
          f"{(universos_material == 3).sum()} / {universos_material.size}")
    print("\nEsto arma los BLOQUES de texto (tabla de fuente, fill de [Cell])")
    print("que hay que pegar en un .inp con la misma estructura de cabecera/")
    print("tallies que ya usan los Escenarios 1-4 (parametros, mesh, tallies,")
    print("[T-Deposit], etc. -- eso no depende de la imagen y no hace falta")
    print("regenerarlo cada vez).")


# %% [DEMO con datos sinteticos] ----------------------------------------------

def demo():
    """Simula una 'actividad SPECT' y un 'CT' sinteticos del mismo tamaño
    que los escenarios actuales (11x11x11), solo para probar que las
    funciones de conversion corren de punta a punta antes de tener datos
    reales."""
    rng = np.random.default_rng(0)
    nz = ny = nx = 11
    actividad = np.zeros((nz, ny, nx))
    actividad[5, 2:5, 5:9] = rng.uniform(50, 100, size=(3, 4))  # "remanente"
    hu = np.full((nz, ny, nx), 40.0)  # tejido blando por defecto
    hu[5, 3, 6] = 400.0  # un voxel "mas denso" adentro del remanente

    pesos = actividad_a_tabla_fuente(actividad)
    densidad = hu_a_densidad(hu)
    universos = hu_a_universo_material(hu)

    print("--- demo con datos sinteticos ---")
    resumen_pipeline(pesos, universos)
    print(f"\ndensidad minima/maxima en el volumen: "
          f"{densidad.min():.3f} / {densidad.max():.3f} g/cm3")
    print("\n(tabla de fuente generada, capa z=6, la que tiene actividad:)")
    lineas_tabla = tabla_fuente_a_texto_inp(pesos).split('\n')
    inicio_z6 = lineas_tabla.index("$ capa z=6")
    print('\n'.join(lineas_tabla[inicio_z6:inicio_z6 + 12]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true",
                     help="correr con datos sinteticos, para probar el pipeline")
    ap.add_argument("--spect", help="carpeta DICOM del SPECT cuantitativo")
    ap.add_argument("--ct", help="carpeta DICOM del CT")
    ap.add_argument("--out", default="escenario_real.inp",
                     help="nombre del .inp de salida (bloques de fuente/material)")
    args = ap.parse_args()

    if args.demo or not (args.spect and args.ct):
        if not args.demo:
            print("faltan --spect y --ct; corriendo con --demo (datos sinteticos)\n")
        demo()
        return

    actividad, vox_spect, origen_spect, orient_spect = leer_spect_dicom(args.spect)
    hu, vox_ct, origen_ct, orient_ct = leer_ct_dicom(args.ct)
    # TODO: verificar que vox_spect/vox_ct, origen y orientacion coincidan
    # (o re-samplear al mismo grid) antes de combinar -- no implementado.

    pesos = actividad_a_tabla_fuente(actividad)
    universos = hu_a_universo_material(hu)
    resumen_pipeline(pesos, universos)

    with open(args.out, 'w', encoding='utf-8') as f:
        f.write("$ --- tabla de fuente (pegar en [source], despues de zmax) ---\n")
        f.write(tabla_fuente_a_texto_inp(pesos))
        f.write("\n\n$ --- fill de [Cell] (pegar en el bloque fill=0:10 0:10 0:10) ---\n")
        f.write(armar_bloque_fill(universos))
    print(f"\nbloques escritos en: {args.out}")


if __name__ == "__main__":
    main()
