# Avances del Proyecto Final

## Dosimetría computacional de alta resolución en el tratamiento con ¹³¹I del cáncer diferenciado de tiroides

Delfina Machicote

---

5. Procedimiento

5.1. Antecedente directo y punto de partida

Como antecedente directo de la implementación computacional, se relevó el conjunto de simulaciones en PHITS desarrollado por Jiménez Scholz [13], que compara la dosis calculada en un único vóxel fuente al variar el radionucleido, la posición subvoxel de la fuente y la resolución espacial de la grilla (4, 1 y 0,5 mm), siempre sobre un fantoma de agua homogénea y con una fuente puntual o uniforme dentro de un solo vóxel. Ese trabajo no aborda la heterogeneidad de tejido ni una distribución de actividad realista entre múltiples vóxeles, que es precisamente donde se ubica el aporte de la presente propuesta. Todos los modelos se construyeron sobre el mismo esqueleto geométrico que utiliza esa referencia: un fantoma voxelizado tipo lattice de PHITS, con la fuente generada mediante espectros de decaimiento nuclear incorporados (e-type=28), basados en los datos evaluados de ICRP Publication 107 [4], y con transporte detallado de electrones (modo EGS5) para representar correctamente el alcance submilimétrico de la rama beta del ¹³¹I.

5.2. Prueba 1: fuente puntual frente a fuente volumétrica en tejido homogéneo

Como primer paso de validación, antes de introducir heterogeneidad de fuente o de tejido, se reprodujo y extendió la comparación de posiciones subvoxel de la referencia [13], contrastando una fuente puntual ubicada en el centro de un vóxel con una fuente volumétrica uniforme que ocupa la totalidad de ese mismo vóxel, sobre un fantoma de agua homogénea de 11×11×11 vóxeles de 4 mm de arista, resolución comparable a la de una reconstrucción SPECT/CT clínica [12]. Se calcularon, para ambas configuraciones de fuente, la dosis total depositada, la contribución separada de electrones y de fotones, y el perfil de dosis desde el centro del fantoma hasta su borde, con el fin de caracterizar cuánto se atenúa el gradiente de dosis en función de la distancia a la fuente. El procesamiento de las salidas de los tallies de tipo [T-Deposit] se automatizó mediante scripts propios.

5.3. Incorporación de heterogeneidad de fuente: fuente voxelizada

Como paso hacia el Escenario 3 planteado en los Objetivos (actividad heterogénea en tejido homogéneo), se reemplazó la fuente puntual/volumétrica de un único vóxel por una fuente distribuida sobre la totalidad de la grilla voxelizada, utilizando la funcionalidad de PHITS para fuentes de distribución espacial en malla xyz [15]. Esta funcionalidad permite asignar una intensidad de emisión relativa e independiente a cada vóxel de la geometría, lo que constituye el mecanismo directo para representar, en una etapa posterior, un mapa de actividad real proveniente de una imagen SPECT cuantitativa, en línea con las extensiones voxelizadas del esquema MIRD [10]. Se aplicó además una opción de muestreo estadístico (isbias=2) que iguala la cantidad de historias generadas en cada vóxel con actividad no nula, ajustando el peso estadístico correspondiente, a fin de evitar que los vóxeles de menor actividad relativa queden subrepresentados en términos de precisión estadística respecto de los de mayor actividad, un problema conocido en el cálculo de factores S a nivel de vóxel con distribuciones no uniformes [10]. Esta opción se adoptó de manera definitiva para la totalidad de los escenarios descriptos en la sección 5.6, dado que el objetivo de la comparación entre zonas de distinta intensidad de fuente requiere una precisión estadística comparable entre ellas.

5.4. Incorporación de heterogeneidad de tejido

Como paso hacia el Escenario 4 (actividad heterogénea en tejido heterogéneo), se extendió el modelo anterior introduciendo un segundo material en el fantoma, de mayor densidad que el tejido circundante, asignado a la misma región de vóxeles donde se concentra la fuente. La densidad y composición elemental de este segundo material se tomaron de la base de datos ICRU-44 de sustitutos tisulares [18], ampliamente utilizada como referencia de composición y densidad de tejidos en dosimetría por radiación y en los propios fantomas computacionales de referencia de ICRP [19].

5.5. Herramientas y verificación

Todas las simulaciones se ejecutaron con el código PHITS [15,21], cuya aplicación a problemas de dosimetría médica, incluyendo geometrías voxelizadas y fuentes de radionucleidos basadas en ICRP-107, está documentada en la literatura [21]. Como antecedente adicional del uso de PHITS específicamente para dosimetría interna con fantomas de referencia, puede citarse la herramienta PARaDIM, que automatiza la generación de archivos de entrada de PHITS a partir de fantomas de referencia y coeficientes de actividad integrada en el tiempo por región [22]; a diferencia de PARaDIM, que emplea fantomas de malla tetraédrica y asume actividad uniforme dentro de cada región fuente, el enfoque aquí adoptado trabaja sobre una geometría voxelizada con asignación de actividad vóxel a vóxel, lo que permite una resolución espacial de la fuente más fina dentro de cada región anatómica.

5.6. Asignación de tejido tiroideo real y diseño factorial de los cuatro escenarios

Conforme a los objetivos específicos de construir modelos voxelizados a partir de datos documentados en bibliografía y de simular los cuatro escenarios planteados (actividad uniforme/heterogénea combinada con tejido homogéneo/heterogéneo), se reemplazó el material de tejido circundante genérico empleado en las secciones 5.3 y 5.4 por tejido tiroideo real: densidad de 1,05 g/cm³ (ICRP Publication 89, sección 11.12.2, valor de referencia para la gravedad específica de la glándula tiroides) [23] y composición elemental de "Tissue, Soft" de la base ICRU-44 [18], adoptada como sustituto de la composición tiroidea específica por no existir una entrada propia para tiroides en esa base de datos.

El material de mayor densidad introducido en la sección 5.4 para validar el mecanismo de fantoma heterogéneo se conservó con el mismo valor de densidad, pero se reposicionó dentro de la misma región en la que se concentra la actividad de la fuente en cada uno de los tres planos activos, de modo de poder estudiar el efecto local de una inhomogeneidad de densidad en la zona efectivamente irradiada. Este material se mantiene, en esta etapa, como objeto de contraste genérico para la validación del mecanismo de heterogeneidad tisular, no como un valor verificado de alguna condición patológica específica del remanente tiroideo.

Sobre esta base se construyeron los cuatro escenarios de los Objetivos sobre una misma grilla de referencia (11×11×11 vóxeles de 4 mm de arista) y una misma región de vóxeles activos, de modo que la comparación entre escenarios aísle el efecto de cada tipo de heterogeneidad por separado: Escenario 1 (actividad uniforme, tejido homogéneo), que constituye además el caso de comparación directa con el cálculo convencional de MIRD a escala de órgano descripto en la sección 5.7; Escenario 2 (actividad uniforme, tejido heterogéneo); Escenario 3 (actividad heterogénea, tejido homogéneo); y Escenario 4 (actividad heterogénea, tejido heterogéneo). Resta, dentro de este punto, extender cada uno de los cuatro escenarios a las resoluciones de 1 mm y 0,5 mm indicadas en los Objetivos; esto se postergó hasta contar con una distribución de actividad real, dado que la comparación de resolución espacial adquiere un significado físico pleno al remuestrear una imagen real a distintos tamaños de vóxel y no al remuestrear una distribución sintética (sección 5.9).

5.7. Implementación del cálculo convencional de MIRD a escala de órgano

Conforme al objetivo específico de comparar los resultados de los cuatro escenarios con una implementación convencional del esquema MIRD a escala de órgano, se implementó el formalismo D=Ã·S [9,10], con S expresado como la suma, sobre cada tipo de emisión, del producto entre el número de emisiones por desintegración, su energía y la fracción absorbida específica, dividido por la masa del órgano. Para la componente no penetrante (partículas beta) se adopta una fracción absorbida unitaria, dado que el alcance de la rama beta del ¹³¹I es sustancialmente menor que las dimensiones típicas del remanente tiroideo. Para la componente penetrante (fotones gamma), la fracción absorbida específica requiere una tabla de referencia o una estimación independiente —por ejemplo, a partir del propio Escenario 1— y se dejó como parámetro explícito pendiente de completar. Los datos nucleares del ¹³¹I empleados en el cálculo (número y energía de cada emisión) se dejaron como parámetros a completar con la referencia estándar en la materia, ICRP Publication 107 [4].

5.8. Generación de mapas tridimensionales de dosis, curvas de isodosis e histogramas dosis-volumen

Conforme al objetivo específico correspondiente, se implementó el procesamiento de las salidas de los tallies [T-Deposit] (formato ANGEL, sección 5.2) para producir, a partir de cualquiera de los cuatro escenarios de la sección 5.6: curvas de isodosis por plano, expresadas como porcentaje de la dosis máxima del tally; un histograma dosis-volumen acumulado, con los puntos de referencia habituales D90, D50 y D10; y un mapa de dosis tridimensional simplificado mediante cáscaras de isodosis. Estas salidas complementan el perfil de dosis y el mapa de error relativo ya disponibles desde la sección 5.2.

5.9. Prototipo de preprocesamiento de imágenes SPECT/CT

Conforme al objetivo específico de desarrollar un prototipo de investigación que reúna la generación de los modelos, la ejecución de las simulaciones y el análisis de los resultados, y en previsión de la incorporación exploratoria de imágenes SPECT/CT o PET/CT prevista en los Objetivos, se implementó el esqueleto del paso de preprocesamiento que traduce una imagen SPECT/CT en los bloques de fuente y de material de un archivo de entrada de PHITS: actividad cuantitativa por vóxel (Bq/ml) a tabla de intensidades relativas de la fuente (s-type=22, sección 5.3), y unidades Hounsfield del CT a densidad y material por vóxel, mediante una curva de calibración análoga a la empleada en un sistema de planificación de radioterapia. Este último paso requiere, para su uso con datos reales, la curva de calibración específica del equipo y protocolo de CT que se utilice, que reemplazará a la curva de ejemplo incorporada en esta etapa. La lectura de los archivos DICOM de SPECT y de CT, así como la verificación de su correspondencia espacial, quedan como funciones a completar cuando se cuente con acceso a imágenes reales; el resto del flujo se verificó con una distribución sintética equivalente a la descripta en la sección 5.3.

5.10. Próximos pasos

Restan: (i) ejecutar los cuatro escenarios descriptos en la sección 5.6; (ii) completar los datos nucleares del ¹³¹I en la implementación del cálculo de MIRD convencional (sección 5.7) a partir de ICRP Publication 107 [4]; (iii) incorporar la lectura de archivos DICOM de SPECT y de CT reales, y la curva de calibración específica del equipo utilizado, al prototipo de preprocesamiento (sección 5.9), cuando se cuente con acceso a imágenes de pacientes; y (iv) escalar los cuatro escenarios a las resoluciones de 1 mm y 0,5 mm una vez disponible una distribución de actividad real (sección 5.6).

---

Archivos adjuntos

- `Escenario1-FuenteUniforme-TejidoHomogeneo/I131-Escenario.inp` — Escenario 1 (sección 5.6).
- `Escenario2-FuenteUniforme-TejidoHeterogeneo/I131-Escenario.inp` — Escenario 2 (sección 5.6).
- `Escenario3-FuenteHeterogenea-TejidoHomogeneo/I131-Escenario.inp` — Escenario 3 (sección 5.6).
- `Escenario4-FuenteHeterogenea-TejidoHeterogeneo/I131-Escenario4.inp` — Escenario 4 (sección 5.6).
- `calculo_mird.py` — implementación del cálculo convencional de MIRD (sección 5.7).
- `mapas_dosis_3d.py` — mapas de dosis 3D, isodosis y DVH (sección 5.8).
- `preprocesamiento_spect_ct.py` — prototipo de preprocesamiento SPECT/CT (sección 5.9).

Bibliografía (continuación, desde [4])

4. ICRP Publication 107. Nuclear Decay Data for Dosimetric Calculations. Annals of the ICRP. 2008;38(3).
9. Bolch WE, Eckerman KF, Sgouros G, Thomas SR. MIRD Pamphlet No. 21: A Generalized Schema for Radiopharmaceutical Dosimetry—Standardization of Nomenclature. Journal of Nuclear Medicine. 2009;50(3):477–484.
10. Bolch WE, Bouchet LG, Robertson JS, et al. MIRD Pamphlet No. 17: The Dosimetry of Nonuniform Activity Distributions—Radionuclide S Values at the Voxel Level. Journal of Nuclear Medicine. 1999;40(1):11S–36S.
12. Dewaraja YK, Ljungberg M, Green AJ, Zanzonico PB, Frey EC. MIRD Pamphlet No. 24: Guidelines for Quantitative I-131 SPECT in Dosimetry Applications. Journal of Nuclear Medicine. 2013;54(12):2182–2188.
13. Jiménez Scholz R. Estudio sobre la utilización de imágenes tomográficas de alta resolución para evaluaciones dosimétricas en terapias radiantes dirigidas de alta selectividad. Tesis de grado, Universidad Favaloro, 2024.
15. Sato T, Iwamoto Y, Hashimoto S, et al. Features of Particle and Heavy Ion Transport code System (PHITS) version 3.02. Journal of Nuclear Science and Technology. 2018;55(6):684–690. doi: 10.1080/00223131.2017.1419890.
18. International Commission on Radiation Units and Measurements. Tissue Substitutes in Radiation Dosimetry and Measurement. ICRU Report 44. Bethesda, MD: ICRU; 1989.
19. International Commission on Radiological Protection. Adult Reference Computational Phantoms. ICRP Publication 110. Annals of the ICRP. 2009;39(2).
21. Furuta T, Sato T. Medical application of particle and heavy ion transport code system PHITS. Radiological Physics and Technology. 2021;14(3):215–225. doi: 10.1007/s12194-021-00628-0.
22. Carter LM, Crawford TM, Sato T, Furuta T, Choi C, Kim CH, Brown JL, Bolch WE, Zanzonico PB, Lewis JS. PARaDIM: A PHITS-Based Monte Carlo Tool for Internal Dosimetry with Tetrahedral Mesh Computational Phantoms. Journal of Nuclear Medicine. 2019;60(12):1802–1811. doi: 10.2967/jnumed.119.229013.
23. International Commission on Radiological Protection. Basic Anatomical and Physiological Data for Use in Radiological Protection: Reference Values. ICRP Publication 89. Annals of the ICRP. 2002;32(3–4).
