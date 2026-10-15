# Contexto del proyecto — Caracterización ciudadana Ciudad Paraíso

> Documento de contexto para el agente (Kiro) y el equipo. Describe el objetivo,
> la estructura de trabajo, el entorno técnico, el estado de los datos y el flujo
> de trabajo acordado. Mantener actualizado a medida que avanza el proyecto.

Última actualización: 2026-10-15 · Corte de archivos de datos: 14/10/2026

---

## 1. Objetivo

Auditar, depurar y dar seguimiento operativo a la **caracterización ciudadana de
Ciudad Paraíso**. Se parte de un consolidado operativo ya recibido y de los
archivos fuente originales; el trabajo consiste en validar las cifras, documentar
la depuración, producir listados operativos (por avance, por territorio, por
hogar) y entregar salidas confiables para la toma de decisiones y el trabajo de
campo.

Rol de trabajo: **Data Steward** (gobierno de datos). Prioridad: trazabilidad,
no alterar las fuentes originales y dejar documentado cada criterio.

---

## 2. Estructura de carpetas del proyecto

Raíz: `caracterizacion_ciudadana_ciudad_Paraiso/`

| Carpeta      | Uso                                                                                     |
|--------------|-----------------------------------------------------------------------------------------|
| `contexto/`  | Contexto del proyecto, flujo y plan (este archivo y notas de apoyo).                     |
| `data/`      | Datos de entrada (fuentes originales, **no se modifican**).                              |
| `notebooks/` | Todos los notebooks (`.ipynb`) del proyecto (ej. mapa interactivo, análisis ITT).        |
| `output/`    | Todas las salidas y resultados organizados de lo que se entregue.                        |
| `scripts/`   | Todos los scripts del proyecto. Los **scripts temporales se borran al terminar**.        |

### Convenciones
- **`data/` es de solo lectura.** El análisis se hace sobre copias o en memoria; nunca
  se sobrescriben los archivos fuente.
- **`output/`**: resultados organizados y versionados por entrega. Cada salida debe poder
  reproducirse desde un script en `scripts/`.
- **`output/informes/`**: todos los informes solicitados se guardan aquí.
- **`scripts/`**: scripts reutilizables se conservan con nombre claro; los scripts de un
  solo uso (exploración, chequeos puntuales) se **eliminan al terminar** la tarea.

### Estándar de informes (OBLIGATORIO para todo informe que se entregue)
- **Formato:** Word (`.docx`).
- **Ubicación:** `output/informes/`.
- **Fuente:** Arial, tamaño 12.
- **Alineación:** texto justificado.
- **Colores de letra:** **azul** para los títulos; **negro** para el cuerpo de texto.
  (No se usan otros colores de letra.)

### Contenido actual de `data/`
- `data/encuesta_ciudad_paraiso/Consolidado_Operativo_Depurado_v2.xlsx` — consolidado depurado (20 hojas).
- `data/encuesta_ciudad_paraiso/Informe_Depuracion_Datos_Caracterizacion_v2.pdf` — informe de soporte (11 páginas).
- `data/catastral/` — shapefiles catastrales urbanos, corte enero 2024, CRS **EPSG:6249**
  (MAGNA Cali Valle del Cauca 2009, coordenadas planas en metros):
  - `ANEXOS_U_2024` (203 polígonos)
  - `CONSTRUCCION_U_2024` (1.346 polígonos)
  - `MANZANAS_U_2024` (28 polígonos)
  - `TERRENOS_U_2024` (857 polígonos)
  - `UNIDADES_U_2024` (23 polígonos)
  - Campos comunes: `DEPAPRED, MUNIPRED, SECTOR, COMUNA, BARRIO, MANZANA, TERRENO, PREDIO, ID_PREDIO/IDPREDIO, SHAPE_Leng, SHAPE_Area` (varían por capa).
- `data/geojson_poligono_ciudad_paraiso/` — capas convertidas a **GeoJSON (EPSG:4326 / WGS84)**:
  - `ANEXOS_U_2024.geojson`, `CONSTRUCCION_U_2024.geojson`, `MANZANAS_U_2024.geojson`,
    `TERRENOS_U_2024.geojson`, `UNIDADES_U_2024.geojson` (generados desde los shapefiles).
  - `poligono_ciudad_Paraiso.geojson` — **preexistente**; 1 feature, **sin CRS y en coordenadas
    en metros** (no WGS84). ⚠️ No alinea con las capas reproyectadas; revisar / reproyectar antes de usar.

### Documentación de referencia catastral (`contexto/contexto_catastral/`)
Modelo de datos y estándares del catastro multipropósito colombiano (LADM-COL), usados para
interpretar los atributos de las capas catastrales:
- `general_destinacion_economica.txt` — **tabla de referencia de destinación económica**
  (id, código, descripción y códigos de interoperabilidad: destino, malambo, datasoft, ilicode).
  Ej.: `A` Habitacional, `C` Comercial, `B` Industrial, `R`/`S` lotes, etc. Útil para clasificar predios.
- `Diccionario_de_Datos_Modelo_Extendido_Catastro_Registro_v4_1.pdf` — diccionario de datos del modelo extendido.
- `Modelo_Extendido_LADMCOL_Cat_Reg_V4_1.pdf` / `.ili` / `.uml` — modelo extendido LADM-COL catastro-registro v4.1.
- `LADM_COL_v_4_0_1_Nucleo_0.ili` — núcleo LADM-COL v4.0.1 (INTERLIS).
- `Submodelo_Cartografia_Catastral_V1_1.ili` — submodelo de cartografía catastral.
- `ISO19107_PLANAS_V3_1_0.ili` — perfil ISO 19107 para geometrías planas.
- `IN-GCT-PC01-06 Identificacion Predial_0.pdf` — instructivo IGAC de identificación predial (estructura del NPN).

---

## 3. Entorno técnico

- **SO:** Windows · shell **PowerShell** (separador de comandos `;`, no `&&`).
- **Python / entorno:** este PC tiene **un único entorno `uv`** ubicado en
  `C:\Users\Jorge\.venv`.
  - Gestor: `uv 0.11.11`.
  - Intérprete del venv: `C:\Users\Jorge\.venv\Scripts\python.exe` (CPython 3.14.x).
  - Paquetes clave ya disponibles: `pandas 3.0.x`, `openpyxl 3.1.5`, `pdfplumber 0.11.10`.
- **Cómo ejecutar scripts** (usar siempre el entorno uv, no un `python` global suelto):
  - `uv run python scripts/mi_script.py`
  - o directamente: `& "C:\Users\Jorge\.venv\Scripts\python.exe" scripts\mi_script.py`
- **Instalar dependencias** en ese entorno: `uv pip install <paquete>`.

---

## 4. Estado de los datos (resumen validado)

Cifras confirmadas contra la hoja `Panel` y `Resumen_Avance` del Excel y contra el PDF.

### Depuración del padrón
- Padrón: **809 → 746** personas analizadas.
  - 60 registros excluidos por relleno / inmueble registrado como persona.
  - 3 registros excluidos por posible duplicado de cédula.
  - 3 duplicados conservados (revisar) + 5 documentos a corregir (conservados).
- Nada se borra de las fuentes: la exclusión se marca con `incluido_en_analisis = SI/NO`.

### Indicadores (depurado vs original recibido)
| Indicador                         | Depurado | Original | Dif.  |
|-----------------------------------|----------|----------|-------|
| Ciudadanos en padrón              | 746      | 809      | -63   |
| Caracterizados validados          | 426      | 430      | -4    |
| Pendientes de ficha ciudadana     | 318      | 377      | -59   |
| Con visita registrada             | 202      | 203      | -1    |
| Verificar / programar visita      | 141      | 194      | -53   |
| Cobertura de fichas ciudadanas    | 57,1 %   | 53,2 %   | +3,9  |

### Avance por persona (regla estricta: ficha + Hogares + Salud)
| Clasificación                        | Personas |
|--------------------------------------|----------|
| 1. Completo                          | 66       |
| 2. Parcial                           | 64       |
| 3. Falta por visitar parcialmente    | 454      |
| 4. Falta por visitar totalmente      | 162      |
| **Total**                            | **746**  |

### Calidad de formularios
- **83 formularios** con "Finalizada = Sí" y 0 % de avance → formularios vacíos; **no**
  cuentan como completos.
- 23 "finalizados con avance parcial" → se cuentan como parciales (decisión pendiente).
- 1 "no finalizada con 100 %" → probablemente completa sin marcar.

### Territorio / georreferenciación
- Comuna diligenciada solo en 434/809; 295 personas (40 %) siguen sin comuna → aún no
  conviene comparar comunas.
- Solo 421/746 (56 %) con coordenadas válidas; la lista de visitas aún no es operativa en campo.

---

## 5. Hojas del consolidado (`Consolidado_Operativo_Depurado_v2.xlsx`)

20 hojas. **Importante al leer con pandas:** cada hoja de datos trae un título y una nota
de uso en las primeras filas; el **encabezado real suele estar en la fila 4** (`header=3`).
Hay texto con acentos y `→`: ejecutar con `PYTHONIOENCODING=utf-8` en Windows.

### Hojas de resumen / tablero (fórmulas)
- `Panel` — indicadores depurado vs original (fórmulas sobre `Ciudadanos`).
- `Resumen_Avance` — avance por persona y por comuna/componente.
- `Analisis_Avance` — explicación del cálculo del avance.
- `Parametros_Avance` — parámetros editables de la regla de "completo" (recalcula).
- `Comunas` — cobertura por comuna (fórmulas sobre `Ciudadanos`).
- `Calidad` — hallazgos de calidad y cruces.

### Hojas de datos (una fila por registro)
| Hoja | Filas | Grano | Columnas clave |
|------|-------|-------|----------------|
| `Ciudadanos` | 809 | 1 x persona (padrón) | `numero_documento`, `estado_caracterizacion_ciudadana`, `incluido_en_analisis` (SI/NO), `comuna_final`, `hogares/salud/empresas_estado_programa`, `ficha_existente`, `max_numero_visita` |
| `Avance_Persona` | 746 | 1 x persona analizada | `clasificacion` (1–4), `ficha_ciudadana`, `programa_*`, `cumple_requeridos`, `faltantes`, `accion_sugerida` |
| `1_Completos` / `2_Parciales` / `3_Falta_Visita_Parcial` / `4_Falta_Visita_Total` | 66 / 64 / 454 / 162 | listados operativos por categoría (con teléfono y dirección) |
| `Ciudadanos` → derivadas `Visitados` (71) y `Parciales` (68) | | subconjuntos operativos |
| `Hogares` | 95 | 1 x hogar | `integrantes`, `integrantes_caracterizados`, `cobertura_integrantes_pct`, `un_solo_integrante` |
| `Inmuebles` | 74 | 1 x dirección | `formularios`, `motivos`, `max_visita_valida`, `revisar_visita` |
| `Contradicciones` | 107 | 1 x formulario | `Finalizada`, `% de avance`, `tipo_contradiccion` (vacío / falso positivo) |
| `Predios_Por_Visitar` | 145 | 1 x persona por visitar | `Estado GPS`, `Prioridad`, `Gestión operativa (editable)` |
| `Georreferenciacion` | 750 | 1 x persona | `Latitud`, `Longitud`, `Fuente coordenadas`, `GPS discrepante entre fuentes`, `Estado georreferenciación` |
| `Excluidos_Revisar` | 71 | 1 x registro excluido/revisar | `clasificacion`, `motivo`, `incluido_en_analisis` |

Notas:
- `Panel` y `Comunas` son fórmulas sobre `Ciudadanos`: cambiar una marca recalcula todo.
- Clave de cruce entre todas las fuentes: **`numero_documento`** (leer como texto).
- `incluido_en_analisis = SI` filtra el padrón analizado (746); `NO` = relleno/duplicado (63).

## 5.1 Validaciones de calidad hechas (coherencia confirmada)
- `Ciudadanos`: 809 filas, **documentos 100 % únicos** (0 repetidos). 746 SI + 63 NO.
  Estados (SI): 426 validados + 318 pendientes + 2 revisar = 746. ✔ cuadra con `Panel`.
- `Avance_Persona`: 66 + 64 + 454 + 162 = 746. ✔
- `Excluidos_Revisar`: 60 no válidos + 3 dup. excluidos + 3 dup. conservados + 5 doc. a corregir.
  (60 + 3 = 63 salen del análisis). ✔
- **Georreferenciación (hallazgo):** 432 registros con coordenadas; **403 caen dentro del
  polígono catastral de Ciudad Paraíso y 29 tienen coordenadas pero FUERA** del área del
  proyecto. 11 con GPS discrepante entre fuentes (>200 m). → relevante para el cruce catastral.

---

## 6. Decisiones pendientes (del equipo)

1. Confirmar con la cédula física cuál es la correcta en los 3 pares de duplicados.
2. Definir si los 23 formularios "finalizados con avance parcial" cuentan como terminados.
3. Definir el tamaño real esperado de los hogares de un solo integrante (63 de 95).
4. Definir qué se exige para considerar a una persona "completa" (ficha, Hogares, Salud;
   y si Empresas aplica a quienes tienen negocio).
5. Aprobar la exclusión de los 60 registros de relleno y decidir si se eliminan del maestro
   o se conservan marcados.

---

## 7. Protocolo de control de calidad geoespacial

Checklist obligatorio para validar coordenadas y georreferenciación de la caracterización.

### 7.1 Control de coordenadas y Sistema de Referencia (CRS)
- **Detección del CRS:** verificar si los datos vienen en coordenadas geográficas
  (**WGS84 / EPSG:4326**) o proyectadas oficiales de Colombia:
  - **MAGNA-SIRGAS Origen Nacional / EPSG:9377**.
  - Local antiguo **Cali / EPSG:3115**.
  - (La cartografía catastral de este proyecto venía en **EPSG:6249** — MAGNA Cali Valle 2009.)
- **Rango geográfico esperado (bounding box Ciudad Paraíso, en geográficas):**
  - Latitud ≈ **3.440 a 3.455**.
  - Longitud ≈ **-76.535 a -76.520**.
- **Inversión de ejes:** comprobar que Latitud y Longitud no estén trocadas
  (error frecuente de captura en campo).
- **Valores nulos, ceros o duplicados exactos:** identificar registros con `(0, 0)`,
  valores en blanco (`NaN`) o varias encuestas registradas en el mismo punto exacto por
  error de GPS.

### 7.2 Validación espacial contra el polígono de intervención
- **Point-in-Polygon:** cruzar las coordenadas contra el shapefile/GeoJSON oficial de los
  planes parciales de Ciudad Paraíso: **El Calvario, San Pascual, Sucre, Ciudadela de la
  Justicia**.
- **Detección de outliers:** puntos que caigan fuera del área de estudio o en comunas
  distintas por pérdida de señal satelital o desfase en la captura.
- **Consistencia dirección vs. coordenada:** cotejar la nomenclatura reportada en campo
  (carreras 10 a 15, calles 12 a 15) con la ubicación espacial estimada.

### 7.3 Calidad de la información de campo
- **Identificador único y vinculación catastral:** coherencia de códigos prediales
  (**NPN de 30 dígitos**, predial nacional o código interno) para cruzar con las demás
  pestañas del diagnóstico socioeconómico o físico.
- **Metadatos de captura:** dispositivo utilizado, fecha/hora de la visita y precisión
  estimada (en metros) si la aplicación de campo la registró.
- **Trazabilidad:** marcar los registros que requieran **regreso a campo (re-visita)** frente
  a los que tienen **inconsistencias subsanables en gabinete**.

> Nota: el bounding box de este protocolo (lat 3.440–3.455 / lon -76.535 a -76.520) es un poco
> más amplio que el bbox observado en la cartografía catastral entregada
> (lat ≈ 3.4425–3.4478 / lon ≈ -76.5325 a -76.5261). Usar el polígono oficial de planes
> parciales como referencia definitiva para el Point-in-Polygon.

---

## 8. Estándar de notebooks y mapa interactivo (patrón ITT adaptado)

Los notebooks de este proyecto siguen el patrón canónico de los notebooks ITT: se **clona y
adapta** el patrón, no se escribe desde cero. Estructura por celdas, parámetros arriba,
carga tolerante a archivos faltantes, verificación espacial con `sjoin`, y mapa Folium.

### 8.1 Estructura del notebook (orden de celdas)
1. **Título** (markdown): zona, área, periodo, fase.
2. **Celda 1** — instalación de dependencias (solo Colab; neutralizar en local).
3. **Celda 2** — imports y config.
4. **Celda 3 (parámetros)** — `EN_COLAB`, rutas (`PATHS`), llaves de cruce, bbox esperado,
   centro del polígono, paleta de colores.
5. **Celda 4 (carga)** — `leer_hoja()` tolerante; carga del polígono y las capas.
6. **Celda 4B (verificación espacial)** — `gpd.sjoin(..., predicate="within")` contra el
   polígono; **no** se confía en los campos `barrio/comuna` de las fuentes.
7. **Celda 5 (mapa)** — ver 8.3.
8. **Celdas siguientes** — cruce/diagnóstico, limpieza, exportes.

### 8.2 Reglas metodológicas
- CRS: puntos en EPSG:4326; si vienen planos, proyectar desde el CRS de origen y `.to_crs(4326)`.
- Donde no hay dato → `NaN`, nunca inventar.
- Ejecución local para verificar: `EN_COLAB=False`, neutralizar celdas de pip/clone,
  `matplotlib.use("Agg")` si aplica.

### 8.3 Mapa interactivo Folium (Celda 5) — detalle
- **Base:** `folium.Map(location=centro, zoom_start=16, tiles=None)` (ninguna fija).
- **5 capas base alternables:** CartoDB Positron, OpenStreetMap, **Esri Satélite**
  (`World_Imagery/.../{z}/{y}/{x}`), **Google Streets** (`lyrs=m`, subdominios mt0-mt3),
  **Google Satélite** (`lyrs=s`).
- **Polígono de zona:** solo contorno, `color="#1B4F8A"`, `weight=2.5`, `fill=False`.
- **Subzonas** (El Calvario, San Pascual, Sucre, Ciudadela de la Justicia) con color propio,
  `dashArray="6,4"`, `fillOpacity=0.08`. ⚠️ Capturar el color en el loop con
  `lambda x, c=_col:` (default arg) para evitar el bug de closure.
- **Capa de lotes/terrenos:** relleno gris tenue, borde oscuro, `GeoJsonTooltip` con el
  identificador predial.
- **Red peatonal OSM** (`osmnx`): dentro de `try/except` para que el mapa salga aunque falle
  la descarga (requiere internet).
- **Puntos de campo:** función reutilizable por tipo/estado, cada capa en su `FeatureGroup`
  o `MarkerCluster`; colores por estado (verde / naranja / rojo).
- **Herramientas:** `MeasureControl`, `MiniMap`, `Fullscreen`.
- **Cierre:** `folium.LayerControl(collapsed=True)` y `m` como última expresión.

### 8.4 Dos versiones del mapa y PRIVACIDAD (regla estricta)
Hay **dos** versiones: la del **notebook** (completa, interna) y la **pública**
(`build_map` para publicar). En la **versión pública**:
- De cada punto se publica **SOLO geometría (lat/lon) + etiqueta de tipo fija**.
  **NUNCA** properties crudas: documento, nombre, dirección, teléfono, correo, edad, sexo, etc.
- **Datos sensibles** (p. ej. hogares vulnerables, menores, salud) → **solo HeatMap**, nunca
  puntos individuales, para no re-identificar en zonas pequeñas.
- Al abrir: solo **Polígono** activo (`show=True`); todo lo demás arranca apagado (`show=False`).
- CartoDB puede omitirse (exige API key en público); OSM por defecto.
- Un chequeo de privacidad debe revisar el `.html` y **bloquear la publicación** si detecta
  atributos sensibles o properties embebidas distintas de identificador/área.

> Nota de este proyecto: la data ciudadana contiene documento, nombre, teléfono, correo y
> dirección → **datos personales de acceso restringido**. El mapa con popups detallados
> (BLOQUE 5 del script actual) es **solo para uso interno**; cualquier versión publicable debe
> pasar por la regla de privacidad 8.4.

---

## 9. Flujo de trabajo acordado

1. **Entrada:** trabajar siempre desde `data/` sin modificar los originales.
2. **Procesamiento:** scripts en `scripts/`, ejecutados con el entorno `uv`.
3. **Salida:** resultados a `output/`, organizados por entrega y reproducibles.
4. **Limpieza:** borrar los scripts temporales al terminar cada tarea.
5. **Trazabilidad:** cada cifra entregada debe poder cruzarse con el Excel o el PDF de soporte.
6. **Privacidad:** los archivos contienen identificadores y direcciones → acceso restringido;
   no exponer datos personales en salidas públicas.

### 9.1 Repositorio Git y versionado
- **Repo remoto:** `https://github.com/j0rg3c45/data_caracterizacion_Ciudad_paraiso.git`
  (origin, rama `main`).
- **REGLA CRÍTICA:** `data/` y `output/` **NO se versionan** (contienen datos personales).
  El `.gitignore` los excluye, junto con `*.xlsx/*.pdf/*.geojson/*.docx/*.rar/*.shp...`,
  caché y temporales. El repo lleva **solo código y documentación** (`scripts/`, `notebooks/`,
  `contexto/*.md`, `README.md`, y los modelos de referencia `.ili/.uml/.txt`).
- **Antes de cada commit:** revisar con `git add -A --dry-run` que no se cuele ningún dato
  personal; usar `git status` y nunca `git add` masivo sin verificar.
- **Flujo de actualización:** tras cada cambio relevante (nuevo script/notebook, ajuste de
  contexto), hacer commit descriptivo y `git push origin main`.
- Cada integrante conserva su copia local de `data/`; en Colab se sube en sesión.

---

## 10. Registro de avances

| Fecha       | Avance                                                                 |
|-------------|------------------------------------------------------------------------|
| 2026-10-15  | Creación de la estructura de carpetas y del documento de contexto.     |
| 2026-10-15  | Validación de cifras del consolidado contra `Panel`/`Resumen_Avance` y el PDF. |
| 2026-10-15  | Conversión de 5 shapefiles catastrales a GeoJSON WGS84 (`scripts/shp_to_geojson.py`). |
| 2026-10-15  | Registro de la documentación de referencia catastral (LADM-COL) en el contexto. |
| 2026-10-15  | Revisión y perfilado de las 20 hojas del consolidado; mapeo de columnas y validación de coherencia (29 GPS fuera del polígono detectados). |
| 2026-10-15  | Definición del estándar de informes (Word, Arial 12, justificado, títulos azul / texto negro). |
| 2026-10-15  | Informe diagnóstico en Word: `output/informes/Informe_Diagnostico_Datos_Caracterizacion.docx` (generador: `scripts/generar_informe_diagnostico.py`). |
| 2026-10-15  | Agregado el protocolo de control de calidad geoespacial (CRS, Point-in-Polygon, calidad de campo) al contexto. |
| 2026-10-15  | Estándar de notebooks + mapa Folium (patrón ITT, 5 bases, privacidad pública) al contexto; carpeta `notebooks/`. |
| 2026-10-15  | Notebook del mapa interactivo: `notebooks/01_mapa_interactivo_ciudad_paraiso.ipynb` (generador `scripts/build_notebook_mapa.py`). Validado en local: 741 cruces, 368 dentro / 64 fuera. |
| 2026-10-15  | Notebook: detección automática Colab/Local y rutas robustas (busca `data/` sin depender del cwd). |
| 2026-10-15  | Repo Git inicializado con `.gitignore` que excluye datos personales; `data/` y `output/` fuera del control de versiones. |
