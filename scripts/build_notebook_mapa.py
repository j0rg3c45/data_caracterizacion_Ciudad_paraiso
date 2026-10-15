# -*- coding: utf-8 -*-
"""
Genera el notebook del mapa interactivo de Ciudad Paraíso siguiendo el patrón
canónico ITT (título, instalación, imports, parámetros, carga, verificación
espacial, cruce, limpieza, mapa interno y mapa público).

Salida: notebooks/01_mapa_interactivo_ciudad_paraiso.ipynb

Ejecutar con el entorno uv:
    uv run python scripts/build_notebook_mapa.py
"""
from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "notebooks"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / "01_mapa_interactivo_ciudad_paraiso.ipynb"

nb = nbf.v4.new_notebook()
cells = []
md = lambda t: cells.append(nbf.v4.new_markdown_cell(t))
code = lambda t: cells.append(nbf.v4.new_code_cell(t))

# --- Título -----------------------------------------------------------------
md("""# Mapa interactivo · Auditoría espacial — Ciudad Paraíso (Cali)

**Proyecto:** Caracterización ciudadana · Rol: Data Steward (Gobierno de Datos)
**Zona:** Ciudad Paraíso (planes parciales El Calvario, San Pascual, Sucre, Ciudadela de la Justicia)
**Corte de datos:** 14/10/2026 · **Fase:** diagnóstico espacial

Flujo (patrón canónico ITT adaptado): carga → cruce → validación/limpieza espacial →
Point-in-Polygon → mapa interactivo (interno y público).

> ⚠️ **Datos personales de acceso restringido.** El mapa interno (Celda 7) muestra documento,
> nombre y dirección: **uso interno únicamente**. El mapa público (Celda 8) no publica datos
> personales (regla de privacidad).""")

# --- Celda 1: instalación ---------------------------------------------------
md("""## Celda 1 · Dependencias y datos (solo Google Colab)

Instala solo lo que falte (no reinstala geopandas: ya viene en Colab). **No bloquea.**""")
code('''# Instala SOLO lo que falte en Colab. En local no hace nada.
try:
    import google.colab  # noqa
    import importlib.util as _u, subprocess, sys
    faltan = [p for p, m in [("folium", "folium"), ("mapclassify", "mapclassify"),
                             ("openpyxl", "openpyxl")]
              if _u.find_spec(m) is None]
    if faltan:
        print("Instalando:", faltan)
        subprocess.run([sys.executable, "-m", "pip", "-q", "install", *faltan], check=False)
    else:
        print("Dependencias ya disponibles (nada que instalar).")
except ImportError:
    print("Entorno local: librerías ya instaladas.")''')

# --- Celda 1B: clonado sparse del repo (patrón ITT, repo público) -----------
md("""## Celda 1B · Clonar el repo y traer los datos (solo Google Colab)

Patrón ITT: **clonado sparse** del repo **público** (rápido, sin token, no baja todo el repo).
El clon es de solo lectura: el notebook **no escribe al repo**.""")
code('''# ¿Estamos en Colab?
try:
    import google.colab  # noqa
    _EN_COLAB = True
except ImportError:
    _EN_COLAB = False

if not _EN_COLAB:
    print("Entorno local: no se clona nada (se usa data/ local).")
else:
    import os, shutil, zipfile, subprocess
    REPO_PATH = "/content/data_caracterizacion"
    SPARSE_DIRS = ["data/_zip"]          # solo la carpeta del ZIP (clon mínimo)
    DATA_DIR = "/content/data_cp"
    ZIP_EN_REPO = os.path.join(REPO_PATH, "data", "_zip", "ciudad_paraiso_data.zip")
    # Repo PÚBLICO -> clonado sin token (como en los notebooks ITT).
    REPO_URL = "https://github.com/j0rg3c45/data_caracterizacion_Ciudad_paraiso.git"
    try:
        if os.path.exists(REPO_PATH):          # borra copia previa (evita datos viejos)
            shutil.rmtree(REPO_PATH)
        # Clonado superficial + sparse (solo baja lo de SPARSE_DIRS).
        subprocess.run(["git", "clone", "--depth", "1", "--filter=blob:none",
                        "--sparse", REPO_URL, REPO_PATH], check=True)
        subprocess.run(["git", "-C", REPO_PATH, "sparse-checkout", "set",
                        *SPARSE_DIRS], check=True)
        os.makedirs(DATA_DIR, exist_ok=True)
        with zipfile.ZipFile(ZIP_EN_REPO) as z:
            z.extractall(DATA_DIR)
        print("Repo clonado (sparse) y datos listos en", DATA_DIR,
              "->", os.listdir(DATA_DIR))
    except subprocess.CalledProcessError as e:
        print("Fallo el clonado:", e, "\\nVerifica tu conexión a internet.")''')

# --- Celda 2: imports -------------------------------------------------------
md("## Celda 2 · Imports y configuración")
code('''import numpy as np
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster, MeasureControl, MiniMap, Fullscreen, HeatMap

pd.set_option("display.max_columns", 60)
AZUL = "#1B4F8A"  # color institucional para contornos/títulos del mapa''')

# --- Celda 3: parámetros ----------------------------------------------------
md("""## Celda 3 · Parámetros

Todo lo editable va aquí: entorno, rutas, llaves de cruce, bbox esperado y paleta.""")
code('''from pathlib import Path

ZONA_NOMBRE = "Ciudad Paraíso"

# Detección automática de entorno: si está google.colab, es Colab.
try:
    import google.colab  # noqa
    EN_COLAB = True
except ImportError:
    EN_COLAB = False
print("Entorno:", "Google Colab" if EN_COLAB else "Local")

# Nombres de archivo que necesita el notebook.
NOMBRES = {
    "xlsx": "Consolidado_Operativo_Depurado_v2.xlsx",
    "terrenos": "TERRENOS_U_2024.geojson",
    "poligono": "poligono_ciudad_Paraiso.geojson",
}

if EN_COLAB:
    import os, zipfile, glob
    DATA_DIR = "/content/data_cp"

    # Respaldo 1: si faltan los archivos pero el ZIP ya fue clonado, descomprímelo.
    zip_clonado = "/content/data_caracterizacion/data/_zip/ciudad_paraiso_data.zip"
    faltan_dir = not all(os.path.exists(os.path.join(DATA_DIR, n))
                         for n in NOMBRES.values())
    if faltan_dir and os.path.exists(zip_clonado):
        os.makedirs(DATA_DIR, exist_ok=True)
        with zipfile.ZipFile(zip_clonado) as z:
            z.extractall(DATA_DIR)
        print("Descomprimido desde el repo clonado.")

    PATHS = {clave: os.path.join(DATA_DIR, nombre) for clave, nombre in NOMBRES.items()}

    # Respaldo 2: si aún falta alguno, búscalo por nombre en /content.
    for clave, nombre in NOMBRES.items():
        if not os.path.exists(PATHS[clave]):
            hits = glob.glob(f"/content/**/{nombre}", recursive=True)
            if hits:
                PATHS[clave] = hits[0]

    # Diagnóstico claro
    print("Contenido de", DATA_DIR, ":",
          os.listdir(DATA_DIR) if os.path.exists(DATA_DIR) else "(no existe)")
    todo_ok = True
    for clave, ruta in PATHS.items():
        ok = os.path.exists(ruta)
        todo_ok = todo_ok and ok
        print(f"[{clave}]", ruta, "OK" if ok else "-> NO ENCONTRADO")
    if not todo_ok:
        print("\\n⚠️ Faltan archivos. Ejecuta la Celda 1B (clonado del repo) "
              "ANTES de esta celda.")
else:
    # Local: localiza la carpeta data/ subiendo desde el cwd (sirve desde
    # notebooks/ o desde la raíz del proyecto).
    def _buscar_base():
        aqui = Path.cwd()
        for cand in [aqui, *aqui.parents]:
            if (cand / "data" / "encuesta_ciudad_paraiso").exists():
                return cand / "data"
        return aqui / "data"
    BASE = _buscar_base()
    print("Carpeta de datos:", BASE)
    PATHS = {
        "xlsx": str(BASE / "encuesta_ciudad_paraiso" / NOMBRES["xlsx"]),
        "terrenos": str(BASE / "geojson_poligono_ciudad_paraiso" / NOMBRES["terrenos"]),
        "poligono": str(BASE / "geojson_poligono_ciudad_paraiso" / NOMBRES["poligono"]),
    }

# Llaves de cruce caracterización <-> georreferenciación (verificadas).
LLAVE_CARAC = "numero_documento"
LLAVE_GEO = "Número documento"

# Rango geográfico esperado para Ciudad Paraíso (bbox de referencia).
LAT_MIN, LAT_MAX = 3.440, 3.455
LON_MIN, LON_MAX = -76.535, -76.520

COLORES = {
    "DENTRO + CRUCE COMPLETO": "green",
    "DENTRO SIN CARACTERIZACIÓN": "orange",
    "FUERA DE ZONA": "red",
}''')

# --- Celda 4: carga ---------------------------------------------------------
md("""## Celda 4 · Carga de insumos (tolerante a archivos faltantes)

Las hojas de datos del Excel traen título + nota en las primeras filas: el encabezado real
está en la fila 4 (`header=3`). El polígono viene en MAGNA-SIRGAS_CMT12 (metros) y se
reproyecta a EPSG:4326.""")
code('''import os

def leer_hoja(sheet, header=3):
    """Lee una hoja del Excel; si falta el archivo o la hoja, devuelve DataFrame vacío."""
    ruta = PATHS["xlsx"]
    if not os.path.exists(ruta):
        print(f"[FALTA] Excel no encontrado: {ruta} -> se continúa sin esa fuente.")
        return pd.DataFrame()
    try:
        df = pd.read_excel(ruta, sheet_name=sheet, header=header)
        return df.dropna(axis=0, how="all").dropna(axis=1, how="all")
    except ValueError as e:
        print(f"[FALTA] Hoja '{sheet}' no disponible ({e}) -> DataFrame vacío.")
        return pd.DataFrame()

def leer_geo(clave):
    """Lee una capa vectorial y la reproyecta a 4326; si falta, devuelve GeoDataFrame vacío."""
    ruta = PATHS.get(clave)
    if not ruta or not os.path.exists(ruta):
        print(f"[FALTA] Capa '{clave}' no encontrada: {ruta} -> capa vacía.")
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    try:
        return gpd.read_file(ruta).to_crs(4326)
    except Exception as e:
        print(f"[ERROR] No se pudo leer '{clave}' ({e}) -> capa vacía.")
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

carac = leer_hoja("Avance_Persona")      # caracterización / avance por persona
geo = leer_hoja("Georreferenciacion")    # georreferenciación y trabajo de campo
poligono = leer_geo("poligono")
terrenos = leer_geo("terrenos")

# Simplifica la geometría de los lotes (857 polígonos) para que el mapa renderice
# rápido en Colab: reduce vértices sin cambiar la forma visible (~1 m de tolerancia).
if len(terrenos):
    terrenos["geometry"] = terrenos.geometry.simplify(0.00001, preserve_topology=True)

print("Caracterización:", carac.shape, "| Georreferenciación:", geo.shape)
print("Polígono:", len(poligono), "feats | Terrenos:", len(terrenos), "lotes")

# Identificador predial para el tooltip de lotes (si hay capa de terrenos).
if len(terrenos.columns):
    CAMPO_PREDIO = next(
        (c for c in ["NPN", "IDPREDIO", "ID_PREDIO", "PREDIO", "TERRENO", "OBJECTID"]
         if c in terrenos.columns), terrenos.columns[0])
    # Deja SOLO el identificador + geometría: aligera el to_json() del mapa
    # (si no, se serializan ~20 columnas por cada uno de los 857 lotes).
    terrenos = terrenos[[CAMPO_PREDIO, "geometry"]].copy()
else:
    CAMPO_PREDIO = None
print("Campo identificador de lote:", CAMPO_PREDIO)''')

# --- Celda 5: cruce ---------------------------------------------------------
md("## Celda 5 · Cruce y consistencia de atributos (reporte diagnóstico)")
code('''# Llave de cruce (solo si cada fuente tiene su columna de documento).
carac["_key"] = (carac[LLAVE_CARAC].astype(str).str.strip()
                 if LLAVE_CARAC in carac.columns else pd.Series(dtype=str))
geo["_key"] = (geo[LLAVE_GEO].astype(str).str.strip()
               if LLAVE_GEO in geo.columns else pd.Series(dtype=str))

if carac.empty or geo.empty:
    print("[AVISO] Falta una fuente (caracterización o georreferenciación): "
          "no se puede generar el reporte de cruce.")
else:
    en_ambos = len(set(carac["_key"]) & set(geo["_key"]))
    solo_carac = set(carac["_key"]) - set(geo["_key"])  # ficha sin coordenada
    solo_geo = set(geo["_key"]) - set(carac["_key"])    # coordenada sin ficha
    dup_geo = int((geo["_key"].value_counts() > 1).sum())
    print("================ REPORTE DIAGNÓSTICO DE CRUCE ================")
    print(f"Registros en caracterización   : {carac['_key'].nunique()}")
    print(f"Registros en georreferenciación: {geo['_key'].nunique()}")
    print(f"Cruzaron exitosamente          : {en_ambos}")
    print(f"Huérfanos ficha SIN coordenada : {len(solo_carac)}")
    print(f"Huérfanos coordenada SIN ficha : {len(solo_geo)}")
    print(f"Duplicados en llave (georref)  : {dup_geo}")''')

# --- Celda 6: validación/limpieza + PiP ------------------------------------
md("""## Celda 6 · Validación y limpieza espacial + Point-in-Polygon

Convierte lat/lon a numérico, descarta nulos y (0,0), corrige ejes invertidos, marca
duplicados exactos, construye los puntos en EPSG:4326 y evalúa pertenencia al polígono.
La verificación espacial se hace por geometría (`within`), **no** por los campos de barrio
o comuna de las fuentes.""")
code('''g = geo.copy()
# Si falta la georreferenciación, se crean columnas vacías para no romper el flujo.
for col in ("Latitud", "Longitud", "_key"):
    if col not in g.columns:
        g[col] = pd.Series(dtype="object")
g["lat"] = pd.to_numeric(g["Latitud"], errors="coerce")
g["lon"] = pd.to_numeric(g["Longitud"], errors="coerce")

# (0,0) -> NaN
g.loc[(g["lat"] == 0) & (g["lon"] == 0), ["lat", "lon"]] = np.nan

# Ejes invertidos: en Cali lat ~+3, lon ~-76. Si vienen trocados, se intercambian.
troc = (g["lat"] < 0) & (g["lon"] > 0)
if troc.any():
    g.loc[troc, ["lat", "lon"]] = g.loc[troc, ["lon", "lat"]].values
print("Ejes invertidos corregidos:", int(troc.sum()))

# Duplicados exactos de coordenada (posible error de GPS repetido)
g["coord_dup"] = g.duplicated(subset=["lat", "lon"], keep=False) & g["lat"].notna()
print("Coordenadas exactas repetidas:", int(g["coord_dup"].sum()))

val = g[g["lat"].notna() & g["lon"].notna()].copy()
pts = gpd.GeoDataFrame(val, geometry=gpd.points_from_xy(val["lon"], val["lat"]), crs="EPSG:4326")

# Point-in-Polygon solo si hay polígono cargado; si falta, no se evalúa pertenencia.
if len(poligono):
    area_proyecto = poligono.geometry.union_all()
    pts["dentro_poligono"] = pts.within(area_proyecto)
else:
    area_proyecto = None
    pts["dentro_poligono"] = False
    print("[AVISO] Sin polígono: no se evalúa Point-in-Polygon.")

keys_carac = set(carac["_key"]) if "_key" in carac.columns else set()
pts["tiene_ficha"] = pts["_key"].isin(keys_carac)

def clasificar(row):
    if not row["dentro_poligono"]:
        return "FUERA DE ZONA"
    return "DENTRO + CRUCE COMPLETO" if row["tiene_ficha"] else "DENTRO SIN CARACTERIZACIÓN"

pts["estado_mapa"] = pts.apply(clasificar, axis=1)
print("\\nPuntos válidos:", len(pts))
print("Dentro del polígono:", int(pts["dentro_poligono"].sum()),
      "| Fuera (outliers):", int((~pts["dentro_poligono"]).sum()))
print(pts["estado_mapa"].value_counts())''')

# --- Celda 6B: vinculación a predios + semáforo por predio ------------------
md("""## Celda 6B · Vincular encuestas a predios y semáforo por terreno

Asigna cada encuesta a un lote (intersección directa; si no, proximidad ≤15 m en metros
reales con EPSG:9377) y colorea cada terreno según la **mejor** confianza de sus encuestas:
🟢 ALTA (intersección) · 🟡 MEDIA (<5 m) · 🟠 BAJA (5-15 m) · ⚪ sin encuesta.""")
code('''UMBRAL_M, PROX_MEDIA_M = 15.0, 5.0
ID_PREDIO = CAMPO_PREDIO  # 'NPN'
COLOR_SEM = {"ALTA": "#2E7D32", "MEDIA": "#F9A825",
             "BAJA": "#EF6C00", "SIN_ENCUESTA": "#BDBDBD"}
terr_sem = None

if len(terrenos) and ID_PREDIO and len(pts):
    pm = pts.to_crs(9377)
    tm = terrenos.to_crs(9377)[[ID_PREDIO, "geometry"]]

    # 1) intersección directa
    dj = gpd.sjoin(pm, tm, how="left", predicate="within")
    dj = dj[~dj.index.duplicated(keep="first")]
    pm["pred"] = dj[ID_PREDIO]
    pm["metodo"] = pm["pred"].notna().map({True: "INTERSECCION_DIRECTA", False: None})
    pm["dist_m"] = pm["pred"].notna().map({True: 0.0, False: None})

    # 2) proximidad con umbral para los no asignados
    falt = pm[pm["pred"].isna()]
    if len(falt):
        near = gpd.sjoin_nearest(falt[["geometry"]], tm, how="left", distance_col="d")
        near = near[~near.index.duplicated(keep="first")]
        for i in falt.index:
            d = float(near.loc[i, "d"])
            if d <= UMBRAL_M:
                pm.loc[i, "pred"] = near.loc[i, ID_PREDIO]
                pm.loc[i, "metodo"] = "PROXIMIDAD_UMBRAL"
                pm.loc[i, "dist_m"] = round(d, 2)
            else:
                pm.loc[i, "metodo"] = "MANUAL_PENDIENTE"
                pm.loc[i, "dist_m"] = round(d, 2)

    def conf(r):
        if r["metodo"] == "INTERSECCION_DIRECTA":
            return "ALTA"
        if r["metodo"] == "PROXIMIDAD_UMBRAL" and r["dist_m"] is not None and r["dist_m"] < PROX_MEDIA_M:
            return "MEDIA"
        return "BAJA"
    pm["conf"] = pm.apply(conf, axis=1)

    # semáforo por predio = mejor confianza de sus encuestas
    asig = pm[pm["pred"].notna()]
    RANGO = {"ALTA": 3, "MEDIA": 2, "BAJA": 1}
    inv = {v: k for k, v in RANGO.items()}
    mejor = asig.assign(_r=asig["conf"].map(RANGO)).groupby("pred")["_r"].max()
    npred = asig.groupby("pred").size()

    terr_sem = terrenos[[ID_PREDIO, "geometry"]].copy()
    terr_sem["n_encuestas"] = terr_sem[ID_PREDIO].map(npred).fillna(0).astype(int)
    terr_sem["confianza_predio"] = terr_sem[ID_PREDIO].map(
        lambda x: inv.get(mejor.get(x), "SIN_ENCUESTA"))
    terr_sem["color"] = terr_sem["confianza_predio"].map(COLOR_SEM)
    print("Semáforo por predio:", terr_sem["confianza_predio"].value_counts().to_dict())
else:
    print("[AVISO] Sin terrenos o sin puntos: no se calcula el semáforo por predio.")''')

# --- Celda 7: mapa interno --------------------------------------------------
md("""## Celda 7 · Mapa interactivo — versión INTERNA (uso restringido)

⚠️ Muestra datos personales en los popups. **No publicar.**""")
code('''try:
    import osmnx as ox
    HAY_OSM = True
except ImportError:
    HAY_OSM = False

# Centro: centroide del polígono si existe; si no, centro del bbox esperado.
if len(poligono):
    cen = poligono.geometry.union_all().centroid
    CENTRO = [cen.y, cen.x]
else:
    CENTRO = [(LAT_MIN + LAT_MAX) / 2, (LON_MIN + LON_MAX) / 2]
m = folium.Map(location=CENTRO, zoom_start=16, tiles=None, control_scale=True)

# 5 capas base alternables
folium.TileLayer("CartoDB positron", name="CartoDB Claro").add_to(m)
folium.TileLayer("OpenStreetMap", name="OpenStreetMap").add_to(m)
folium.TileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/"
                 "World_Imagery/MapServer/tile/{z}/{y}/{x}",
                 attr="Esri", name="Esri Satélite").add_to(m)
folium.TileLayer("http://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
                 attr="Google", name="Google Streets",
                 subdomains=["mt0", "mt1", "mt2", "mt3"]).add_to(m)
folium.TileLayer("http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
                 attr="Google", name="Google Satélite",
                 subdomains=["mt0", "mt1", "mt2", "mt3"]).add_to(m)

# Polígono: solo contorno (si hay)
if len(poligono):
    folium.GeoJson(poligono.to_json(), name="Polígono Ciudad Paraíso",
                   style_function=lambda x: {"color": AZUL, "weight": 2.5, "fill": False}).add_to(m)

# Lotes con tooltip del identificador predial (si hay)
if len(terrenos) and CAMPO_PREDIO:
    folium.GeoJson(
        terrenos.to_json(), name="Lotes / Terrenos",
        style_function=lambda x: {"color": "#444", "weight": 1,
                                  "fillColor": "#9e9e9e", "fillOpacity": 0.15},
        highlight_function=lambda x: {"weight": 2.5, "fillOpacity": 0.35},
        tooltip=folium.GeoJsonTooltip(fields=[CAMPO_PREDIO], aliases=["Lote / Predio:"]),
        show=False).add_to(m)

# Predios coloreados por SEMÁFORO de encuesta (capa aparte, encendida por defecto)
if terr_sem is not None and len(terr_sem):
    folium.GeoJson(
        terr_sem.to_json(), name="Predios · semáforo de encuesta",
        style_function=lambda feat: {
            "color": "#555", "weight": 0.6,
            "fillColor": feat["properties"]["color"], "fillOpacity": 0.55},
        highlight_function=lambda x: {"weight": 2, "fillOpacity": 0.75},
        tooltip=folium.GeoJsonTooltip(
            fields=[CAMPO_PREDIO, "confianza_predio", "n_encuestas"],
            aliases=["Predio:", "Confianza:", "N° encuestas:"]),
        show=True).add_to(m)

# Red peatonal OSM (try/except: el mapa sale aunque falle la descarga)
if HAY_OSM and area_proyecto is not None:
    try:
        G = ox.graph_from_polygon(area_proyecto, network_type="walk", simplify=False)
        _, edges = ox.graph_to_gdfs(G)
        folium.GeoJson(edges.to_json(), name="Red peatonal (OSM)",
                       style_function=lambda x: {"color": "#2A9C8A", "weight": 1.2},
                       show=False).add_to(m)
    except Exception as e:
        print("Red peatonal OSM no disponible:", e)

# Puntos por estado, clusterizados, con popup detallado (INTERNO)
grupos = {e: MarkerCluster(name=f"Puntos · {e}").add_to(m) for e in COLORES}
car_idx = carac.set_index("_key") if "_key" in carac.columns else pd.DataFrame()
for _, r in pts.iterrows():
    est, doc = r["estado_mapa"], r["_key"]
    nombre = r.get("Nombre ciudadano", "")
    direccion = r.get("Dirección para visita", "") or r.get("Dirección padrón", "")
    ef = r.get("Estado ficha", "")
    clasif = faltan = accion = ""
    if doc in car_idx.index:
        fila = car_idx.loc[doc]
        fila = fila.iloc[0] if isinstance(fila, pd.DataFrame) else fila
        clasif = fila.get("clasificacion", ""); faltan = fila.get("faltantes", "")
        accion = fila.get("accion_sugerida", "")
    html = (f'<div style="font-family:Arial;font-size:12px;max-width:280px">'
            f'<b style="color:{AZUL}">{nombre}</b><br><b>Documento:</b> {doc}<br>'
            f'<b>Estado cruce:</b> {est}<br><b>Estado ficha:</b> {ef}<br>'
            f'<b>Dirección:</b> {direccion}<hr style="margin:4px 0">'
            f'<b>Clasificación:</b> {clasif}<br><b>Faltantes:</b> {faltan}<br>'
            f'<b>Acción:</b> {accion}</div>')
    folium.CircleMarker([r["lat"], r["lon"]], radius=5, color=COLORES[est], fill=True,
                        fill_color=COLORES[est], fill_opacity=0.85, weight=1,
                        popup=folium.Popup(html, max_width=300),
                        tooltip=f"{nombre} · {est}").add_to(grupos[est])

m.add_child(MeasureControl(primary_length_unit="meters"))
MiniMap(toggle_display=True, position="bottomleft").add_to(m)
Fullscreen().add_to(m)
leyenda = ('<div style="position:fixed;bottom:30px;right:30px;z-index:9999;background:white;'
           'padding:10px 14px;border:1px solid #999;border-radius:6px;font-family:Arial;'
           f'font-size:12px;color:#000"><b style="color:{AZUL}">Puntos de campo</b><br>'
           '<span style="color:green">●</span> Dentro + cruce completo<br>'
           '<span style="color:orange">●</span> Dentro sin caracterización<br>'
           '<span style="color:red">●</span> Fuera de zona (revisar)<br>'
           f'<b style="color:{AZUL}">Predios (semáforo)</b><br>'
           '<span style="color:#2E7D32">■</span> ALTA (intersección)<br>'
           '<span style="color:#F9A825">■</span> MEDIA (&lt;5 m)<br>'
           '<span style="color:#EF6C00">■</span> BAJA (5-15 m)<br>'
           '<span style="color:#BDBDBD">■</span> Sin encuesta</div>')
m.get_root().html.add_child(folium.Element(leyenda))
folium.LayerControl(collapsed=True).add_to(m)
# m.save("../output/mapa_interno_ciudad_paraiso.html")
m''')

# --- Celda 8: mapa público --------------------------------------------------
md("""## Celda 8 · Mapa PÚBLICO (sin datos personales)

Regla de privacidad: de cada punto solo geometría + etiqueta de tipo fija. Nunca documento,
nombre, dirección ni teléfono. Al abrir, solo el polígono activo; lo demás apagado.""")
code('''if len(poligono):
    cen_p = poligono.geometry.union_all().centroid
    centro_pub = [cen_p.y, cen_p.x]
else:
    centro_pub = [(LAT_MIN + LAT_MAX) / 2, (LON_MIN + LON_MAX) / 2]
m_pub = folium.Map(location=centro_pub, zoom_start=16, tiles="OpenStreetMap")

if len(poligono):
    folium.GeoJson(poligono.to_json(), name="Polígono Ciudad Paraíso",
                   style_function=lambda x: {"color": AZUL, "weight": 2.5, "fill": False},
                   show=True).add_to(m_pub)

if len(terrenos) and CAMPO_PREDIO:
    folium.GeoJson(terrenos.to_json(), name="Lotes / Terrenos",
                   style_function=lambda x: {"color": "#444", "weight": 1,
                                             "fillColor": "#9e9e9e", "fillOpacity": 0.15},
                   tooltip=folium.GeoJsonTooltip(fields=[CAMPO_PREDIO], aliases=["Lote:"]),
                   show=False).add_to(m_pub)

# Puntos: SOLO lat/lon + etiqueta de estado (sin properties personales)
for est, color in COLORES.items():
    fg = folium.FeatureGroup(name=f"Puntos · {est}", show=False)
    for _, r in pts[pts["estado_mapa"] == est].iterrows():
        folium.CircleMarker([r["lat"], r["lon"]], radius=4, color=color, fill=True,
                            fill_color=color, fill_opacity=0.8, weight=1,
                            tooltip=est).add_to(fg)
    fg.add_to(m_pub)

# Densidad de pendientes como HeatMap (agregado, no re-identifica)
pend = pts[pts["estado_mapa"] != "DENTRO + CRUCE COMPLETO"]
pend_xy = pend[["lat", "lon"]].dropna().values.tolist()
if pend_xy:
    HeatMap(pend_xy, name="Densidad de pendientes (calor)", radius=18, blur=15,
            min_opacity=0.3, show=False).add_to(m_pub)

folium.LayerControl(collapsed=True).add_to(m_pub)
# m_pub.save("../output/mapa_publico_ciudad_paraiso.html")
m_pub''')

nb["cells"] = cells
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
}
nbf.write(nb, OUT)
print("Notebook generado:", OUT)
print("Celdas:", len(cells))
