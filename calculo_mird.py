"""
Calculo de dosis convencional MIRD (organo completo, actividad uniforme,
densidad uniforme) para usar como comparacion/baseline contra los 4
escenarios de PHITS (Escenario 1 es el que deberia coincidir mejor con
este calculo, porque tambien tiene fuente uniforme + tejido homogeneo).

Formalismo MIRD estandar (Loevinger-Berman / MIRD Pamphlet 1):

    D = A~ * S(T<-S)
    S(T<-S) = sum_i [ n_i * E_i * phi_i(T<-S) ] / m_T

donde (para autoirradiacion, T=S=remanente tiroideo):
    A~    = actividad acumulada en la fuente (Bq*s): integral en el tiempo
            de A(t). Para un clearance monoexponencial con vida media
            efectiva T_ef, A~ = A0 * tau, con tau = T_ef / ln(2).
    n_i   = numero de emisiones de tipo i por desintegracion
    E_i   = energia de la emision i (J)
    phi_i = fraccion absorbida especifica (adimensional). Para radiacion
            NO penetrante (particulas beta) en un organo mucho mas grande
            que el alcance de la particula, phi=1 (toda la energia se
            deposita localmente: esto es el caso tipico para el beta de
            I-131, alcance submilimetrico, en un remanente de varios mm).
            Para radiacion PENETRANTE (fotones gamma), phi<1 y depende de
            la masa/geometria del organo: requiere tablas (MIRD Pamphlet 5
            / ICRP 110 Annex, o un codigo como OLINDA/EXM) o, alternativa-
            mente, puede estimarse corriendo el propio Escenario 1 de PHITS
            (fuente uniforme + tejido homogeneo) y comparando la dosis total
            tallada contra la dosis "solo no-penetrante" de este script.

IMPORTANTE: los datos nucleares de I-131
(n_i, E_i de cada emision beta y gamma) NO estan hardcodeados en este
script. Hay que completarlos en DATOS_NUCLEARES_I131 tomandolos de una
fuente verificada -- la referencia estandar en dosimetria MIRD/ICRP es
ICRP Publication 107 "Nuclear Decay Data for Dosimetric Calculations"
-- en vez de usar un valor recordado de memoria, para no introducir un
numero no verificado en los calculos de la tesis. phi_fotones tambien
se deja como parametro a completar/justificar (ver nota arriba).

Uso:
    python calculo_mird.py
(edita las variables en la seccion [CONFIGURACION] con tus valores de
A0, T_ef y masa del remanente antes de correr)
"""
import math

# %% [DATOS NUCLEARES I-131] --------------------------------------------------
# TODO: completar con valores verificados de ICRP 107 (no usar de memoria).
# Cada tupla es (n_i: emisiones por desintegracion, E_i: energia en MeV).
# Separar por tipo de radiacion porque phi depende del tipo (ver docstring).
DATOS_NUCLEARES_I131 = {
    "beta_no_penetrante": [
        # (n_i, E_i_MeV), una fila por rama beta -- completar con ICRP 107
    ],
    "gamma_penetrante": [
        # (n_i, E_i_MeV), una fila por linea gamma -- completar con ICRP 107
    ],
}

MeV_a_J = 1.602176634e-13  # 1 MeV en Joule (constante fisica, no nuclear-especifica)


# %% [CONFIGURACION] -----------------------------------------------------------
# Completar antes de correr. Estos son los unicos numeros "de paciente"
# que entran al calculo; todo lo demas es fisica de la desintegracion.
A0_Bq = None          # actividad administrada/en el remanente al tiempo 0 (Bq)
T_fisica_dias = 8.02  # semivida fisica del I-131 (dias) -- valor de libro de
                       # texto estandar, pero conviene re-chequear contra
                       # ICRP 107 antes de usar en la tesis
T_biologica_dias = None  # semivida biologica efectiva de eliminacion del
                          # remanente (dias) -- esto SI depende del paciente
                          # y debe salir de la curva de actividad medida
                          # (idealmente de SPECT/CT seriado, varios puntos
                          # temporales; con un unico punto se puede asumir
                          # solo decaimiento fisico como aproximacion gruesa)
masa_remanente_g = None   # masa del remanente tiroideo (g), de la
                           # segmentacion del CT (volumen x densidad 1.05
                           # g/cm3, ICRP 89)
phi_fotones = None         # fraccion absorbida especifica para los fotones
                            # (target<-source, autoirradiacion). Dejar en
                            # None hasta tener una justificacion (tabla o
                            # corrida de PHITS); el script avisa si falta.


# %% [CALCULO] ------------------------------------------------------------------
def tiempo_de_residencia_efectivo(t_fisica_dias, t_biologica_dias):
    """T_ef tal que 1/T_ef = 1/T_fisica + 1/T_biologica (vidas medias)."""
    if t_biologica_dias is None:
        return t_fisica_dias
    return 1.0 / (1.0 / t_fisica_dias + 1.0 / t_biologica_dias)


def actividad_acumulada_Bq_s(A0_Bq, T_ef_dias):
    """A~ = A0 * tau, tau = T_ef/ln(2). T_ef en dias -> tau en segundos."""
    tau_s = (T_ef_dias * 86400.0) / math.log(2)
    return A0_Bq * tau_s


def delta_por_tipo(lista_n_E):
    """sum_i(n_i * E_i) en J por desintegracion, para un tipo de radiacion."""
    return sum(n * E * MeV_a_J for n, E in lista_n_E)


def dosis_mird(A_tilde_Bq_s, masa_kg, datos_nucleares, phi_fotones):
    delta_beta = delta_por_tipo(datos_nucleares["beta_no_penetrante"])
    delta_gamma = delta_por_tipo(datos_nucleares["gamma_penetrante"])

    # No penetrante: phi=1 (ver docstring)
    dosis_beta_Gy = A_tilde_Bq_s * delta_beta / masa_kg

    # Penetrante: requiere phi
    if phi_fotones is None:
        dosis_gamma_Gy = None
    else:
        dosis_gamma_Gy = A_tilde_Bq_s * delta_gamma * phi_fotones / masa_kg

    return dosis_beta_Gy, dosis_gamma_Gy


def main():
    faltantes = [nombre for nombre, v in [
        ("A0_Bq", A0_Bq),
        ("T_biologica_dias", T_biologica_dias),
        ("masa_remanente_g", masa_remanente_g),
    ] if v is None]
    if faltantes or not DATOS_NUCLEARES_I131["beta_no_penetrante"]:
        print("Faltan completar antes de calcular:")
        for f in faltantes:
            print(f"  - {f}")
        if not DATOS_NUCLEARES_I131["beta_no_penetrante"]:
            print("  - DATOS_NUCLEARES_I131 (emisiones beta/gamma de ICRP 107)")
        print("\nEste script no inventa esos valores -- completalos en el")
        print("codigo (seccion [CONFIGURACION] y [DATOS NUCLEARES I-131]) y")
        print("volve a correr.")
        return

    T_ef = tiempo_de_residencia_efectivo(T_fisica_dias, T_biologica_dias)
    A_tilde = actividad_acumulada_Bq_s(A0_Bq, T_ef)
    masa_kg = masa_remanente_g / 1000.0

    dosis_beta, dosis_gamma = dosis_mird(A_tilde, masa_kg, DATOS_NUCLEARES_I131, phi_fotones)

    print(f"T efectivo: {T_ef:.2f} dias")
    print(f"Actividad acumulada (A~): {A_tilde:.3e} Bq*s")
    print(f"Dosis MIRD (beta, no penetrante, phi=1): {dosis_beta:.3f} Gy")
    if dosis_gamma is None:
        print("Dosis MIRD (gamma, penetrante): no calculada (falta phi_fotones)")
        print(f"Dosis MIRD total (parcial, solo beta): {dosis_beta:.3f} Gy")
    else:
        print(f"Dosis MIRD (gamma, penetrante, phi={phi_fotones}): {dosis_gamma:.3f} Gy")
        print(f"Dosis MIRD total: {dosis_beta + dosis_gamma:.3f} Gy")

    print("\nPara comparar contra PHITS: correr el Escenario 1 (fuente")
    print("uniforme + tejido homogeneo), sumar la dosis total tallada en")
    print("robot-deposit-xz.out (ver leer_dosis_phits.py), escalar de")
    print("'Gy/particula simulada' a 'Gy real' usando la actividad acumulada")
    print("real (A~) en vez de 1 particula, y comparar contra el numero de")
    print("arriba. Una diferencia grande puede venir de: el supuesto phi=1")
    print("para el beta, el valor de phi_fotones, o diferencias geometricas")
    print("entre el fantoma cubico de PHITS y el remanente real.")


if __name__ == "__main__":
    main()
