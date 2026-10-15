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
md("## Celda 1 · Instalación de dependencias (solo Google Colab)")
code('''# Dependencias. En Colab, geopandas/shapely/pyproj YA vienen preinstalados;
# reinstalarlos es lo que hace lenta esta celda, así que solo se instala lo que falte.
# osmnx NO se instala aquí (es pesado y solo lo usa la capa opcional de red peatonal).
try:
    import google.colab  # noqa
    import importlib.util as _u, subprocess, sys
    faltan = [p for p, m in [("geopandas", "geopandas"), ("folium", "folium"),
                             ("mapclassify", "mapclassify"), ("openpyxl", "openpyxl")]
              if _u.find_spec(m) is None]
    if faltan:
        print("Instalando lo que falta:", faltan)
        subprocess.run([sys.executable, "-m", "pip", "-q", "install", *faltan], check=False)
    else:
        print("Dependencias ya disponibles en Colab (nada que instalar).")
    # osmnx opcional: descomenta la línea de abajo SOLO si quieres la red peatonal.
    # subprocess.run([sys.executable, "-m", "pip", "-q", "install", "osmnx"], check=False)
except ImportError:
    print("Entorno local: se usan las librerías ya instaladas.")''')

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
    import os
    # --- Opción recomendada: leer desde Google Drive (sin re-subir nada) ------
    # Sube la carpeta data/ a tu Drive una sola vez; aquí se monta y se buscan
    # los 3 archivos por NOMBRE en todo el Drive (no importa la subcarpeta).
    PATHS = {}
    try:
        from google.colab import drive
        drive.mount("/content/drive")
        raiz_drive = "/content/drive/MyDrive"
        # índice nombre -> primera ruta encontrada
        encontrados = {}
        objetivo = set(NOMBRES.values())
        for base, _dirs, archivos in os.walk(raiz_drive):
            for a in archivos:
                if a in objetivo and a not in encontrados:
                    encontrados[a] = os.path.join(base, a)
            if len(encontrados) == len(objetivo):
                break
        for clave, nombre in NOMBRES.items():
            if nombre in encontrados:
                PATHS[clave] = encontrados[nombre]
                print(f"[DRIVE] {nombre} -> {encontrados[nombre]}")
            else:
                print(f"[DRIVE] No se encontró {nombre} en el Drive.")
    except Exception as e:
        print("No se pudo montar/leer Drive:", e)

    # --- Respaldo: subir manualmente los que falten --------------------------
    faltan = [NOMBRES[k] for k in NOMBRES if k not in PATHS]
    if faltan:
        from google.colab import files
        print("\\nFaltan archivos; súbelos manualmente:")
        for n in faltan:
            print("   -", n)
        files.upload()
        disponibles = set(os.listdir("."))
        for clave, nombre in NOMBRES.items():
            if clave not in PATHS and nombre in disponibles:
                PATHS[clave] = nombre
    # Rellena los que sigan faltando (la carga avisará y seguirá con capa vacía).
    for clave, nombre in NOMBRES.items():
        PATHS.setdefault(clave, nombre)
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

print("Caracterización:", carac.shape, "| Georreferenciación:", geo.shape)
print("Polígono:", len(poligono), "feats | Terrenos:", len(terrenos), "lotes")

# Identificador predial para el tooltip de lotes (si hay capa de terrenos).
if len(terrenos.columns):
    CAMPO_PREDIO = next(
        (c for c in ["NPN", "IDPREDIO", "ID_PREDIO", "PREDIO", "TERRENO", "OBJECTID"]
         if c in terrenos.columns), terrenos.columns[0])
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
           f'font-size:12px;color:#000"><b style="color:{AZUL}">Trabajo de campo</b><br>'
           '<span style="color:green">●</span> Dentro + cruce completo<br>'
           '<span style="color:orange">●</span> Dentro sin caracterización<br>'
           '<span style="color:red">●</span> Fuera de zona (revisar)</div>')
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
