"""
Vinculación encuesta ↔ predio (terrenos) — Ciudad Paraíso.

Marco metodológico (ver contexto 8.5):
  1. Intersección directa (Point-in-Polygon) -> NPN del predio, distancia 0.
  2. Cardinalidad N a 1 (varias encuestas por lote) y 0 a 1 (lotes sin encuesta).
  3. Proximidad con umbral: sjoin_nearest, máximo 15 m; si supera -> requiere revisión.
  4. Semáforo de confianza (ALTA/MEDIA/BAJA) usando BARRIO (el GeoJSON no trae dirección).

Mediciones en metros: se reproyecta a EPSG:9377 (MAGNA-SIRGAS Origen Nacional).
Salida: output/vinculacion_predios.gpkg (+ resumen en consola y CSV de predios sin encuesta).

Ejecutar con el entorno uv:
    uv run python scripts/vincular_encuestas_predios.py
"""
from pathlib import Path
import pandas as pd
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "data" / "encuesta_ciudad_paraiso" / "Consolidado_Operativo_Depurado_v2.xlsx"
TERR = ROOT / "data" / "geojson_poligono_ciudad_paraiso" / "TERRENOS_U_2024.geojson"
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

EPSG_METROS = 9377      # MAGNA-SIRGAS Origen Nacional (metros)
UMBRAL_M = 15.0         # radio máximo para asignación por proximidad
PROX_ALTA_MEDIA_M = 5.0 # proximidad < 5 m puede ser MEDIA; >= baja la confianza


# ----------------------------------------------------------------- carga
def leer_hoja(sheet, header=3):
    df = pd.read_excel(XLSX, sheet_name=sheet, header=header)
    return df.dropna(axis=0, how="all").dropna(axis=1, how="all")


geo = leer_hoja("Georreferenciacion")
terr = gpd.read_file(TERR).to_crs(4326)

# Puntos válidos (lat/lon numéricos, sin (0,0))
geo = geo.copy()
geo["lat"] = pd.to_numeric(geo["Latitud"], errors="coerce")
geo["lon"] = pd.to_numeric(geo["Longitud"], errors="coerce")
geo.loc[(geo["lat"] == 0) & (geo["lon"] == 0), ["lat", "lon"]] = pd.NA
val = geo[geo["lat"].notna() & geo["lon"].notna()].copy()

pts = gpd.GeoDataFrame(
    val, geometry=gpd.points_from_xy(val["lon"], val["lat"]), crs="EPSG:4326"
)

# Campos de predio que conservamos
ID_PREDIO = "NPN"
campos_terr = [c for c in [ID_PREDIO, "IDPREDIO", "BARRIO", "COMUNA", "MANZANA"]
               if c in terr.columns]
terr_slim = terr[campos_terr + ["geometry"]].copy()

# ----------------------------------------------------------------- a metros
pts_m = pts.to_crs(EPSG_METROS)
terr_m = terr_slim.to_crs(EPSG_METROS)

# ----------------------------------------------------------------- 1) intersección
dir_join = gpd.sjoin(pts_m, terr_m, how="left", predicate="within")
# si un punto cae en 2 polígonos (bordes), nos quedamos con el primero
dir_join = dir_join[~dir_join.index.duplicated(keep="first")]

pts_m["id_terreno_asignado"] = dir_join[ID_PREDIO]
pts_m["barrio_predio"] = dir_join["BARRIO"] if "BARRIO" in dir_join else pd.NA
pts_m["metodo_asignacion"] = pts_m["id_terreno_asignado"].notna().map(
    {True: "INTERSECCION_DIRECTA", False: None})
pts_m["distancia_al_predio_m"] = pts_m["id_terreno_asignado"].notna().map(
    {True: 0.0, False: None})

# ----------------------------------------------------------------- 3) proximidad
sin_asignar = pts_m[pts_m["id_terreno_asignado"].isna()].copy()
if len(sin_asignar):
    cerca = gpd.sjoin_nearest(
        sin_asignar[["geometry"]], terr_m, how="left", distance_col="dist_m"
    )
    cerca = cerca[~cerca.index.duplicated(keep="first")]
    for idx in sin_asignar.index:
        d = float(cerca.loc[idx, "dist_m"])
        if d <= UMBRAL_M:
            pts_m.loc[idx, "id_terreno_asignado"] = cerca.loc[idx, ID_PREDIO]
            pts_m.loc[idx, "barrio_predio"] = cerca.loc[idx, "BARRIO"] if "BARRIO" in cerca else pd.NA
            pts_m.loc[idx, "metodo_asignacion"] = "PROXIMIDAD_UMBRAL"
            pts_m.loc[idx, "distancia_al_predio_m"] = round(d, 2)
        else:
            pts_m.loc[idx, "metodo_asignacion"] = "MANUAL_PENDIENTE"
            pts_m.loc[idx, "distancia_al_predio_m"] = round(d, 2)

# ----------------------------------------------------------------- 4) confianza
# NOTA: el GeoJSON de terrenos NO trae dirección y su campo BARRIO son CÓDIGOS
# ('06','07'...), no nombres, así que NO es comparable con el barrio de la encuesta
# ('El Calvario', 'Sucre'...). Por eso la validación alfanumérica por barrio NO es
# viable con los insumos actuales. El semáforo se basa en método + distancia:
#   ALTA  = intersección directa (el punto cae dentro del lote).
#   MEDIA = proximidad < 5 m.
#   BAJA  = proximidad >= 5 m, o huérfana (requiere revisión).
def nivel_confianza(r):
    if r["metodo_asignacion"] == "INTERSECCION_DIRECTA":
        return "ALTA"
    if r["metodo_asignacion"] == "PROXIMIDAD_UMBRAL" and \
            r["distancia_al_predio_m"] is not None and \
            r["distancia_al_predio_m"] < PROX_ALTA_MEDIA_M:
        return "MEDIA"
    return "BAJA"


pts_m["nivel_confianza"] = pts_m.apply(nivel_confianza, axis=1)
pts_m["requiere_visita_campo"] = pts_m["metodo_asignacion"].isin(
    ["MANUAL_PENDIENTE"]) | (pts_m["nivel_confianza"] == "BAJA")
pts_m["id_encuesta"] = pts_m["Número documento"].astype(str).str.strip()

# ----------------------------------------------------------------- cardinalidad
asignadas = pts_m[pts_m["id_terreno_asignado"].notna()]
n_por_predio = asignadas.groupby("id_terreno_asignado").size()
pts_m["n_encuestas_en_predio"] = pts_m["id_terreno_asignado"].map(n_por_predio)
predios_con = set(n_por_predio.index)
predios_sin = terr_slim[~terr_slim[ID_PREDIO].isin(predios_con)]

# -------------------------------------------- semáforo A NIVEL DE PREDIO
# Un predio puede tener varias encuestas con confianzas distintas -> toma la MEJOR.
RANGO = {"ALTA": 3, "MEDIA": 2, "BAJA": 1}
mejor = (asignadas.assign(_r=asignadas["nivel_confianza"].map(RANGO))
         .groupby("id_terreno_asignado")["_r"].max())
inv = {v: k for k, v in RANGO.items()}

terr_sem = terr_slim.copy()
terr_sem["n_encuestas"] = terr_sem[ID_PREDIO].map(n_por_predio).fillna(0).astype(int)
terr_sem["confianza_predio"] = terr_sem[ID_PREDIO].map(
    lambda x: inv.get(mejor.get(x)) if x in predios_con else "SIN_ENCUESTA")
# color del semáforo para el mapa
COLOR_SEM = {"ALTA": "#2E7D32", "MEDIA": "#F9A825",
             "BAJA": "#EF6C00", "SIN_ENCUESTA": "#BDBDBD"}
terr_sem["color_semaforo"] = terr_sem["confianza_predio"].map(COLOR_SEM)
terr_sem = terr_sem.to_crs(4326)

# ----------------------------------------------------------------- salida
salida = pts_m.to_crs(4326)[[
    "id_encuesta", "id_terreno_asignado", "metodo_asignacion",
    "distancia_al_predio_m", "nivel_confianza", "requiere_visita_campo",
    "n_encuestas_en_predio", "Barrio", "barrio_predio", "geometry",
]].copy()

GPKG = OUT_DIR / "vinculacion_predios.gpkg"
salida.to_file(GPKG, layer="encuestas_vinculadas", driver="GPKG")
predios_sin[[ID_PREDIO, "geometry"]].to_file(GPKG, layer="predios_sin_encuesta", driver="GPKG")
predios_sin[[ID_PREDIO]].to_csv(OUT_DIR / "predios_sin_encuesta.csv", index=False)
# capa de predios con semáforo (todos los lotes, coloreados)
terr_sem[[ID_PREDIO, "n_encuestas", "confianza_predio", "color_semaforo",
          "geometry"]].to_file(GPKG, layer="predios_semaforo", driver="GPKG")
# también como GeoJSON para que el notebook la pinte fácil
terr_sem[[ID_PREDIO, "n_encuestas", "confianza_predio", "color_semaforo",
          "geometry"]].to_file(OUT_DIR / "predios_semaforo.geojson", driver="GeoJSON")

# ----------------------------------------------------------------- balance
tot = len(pts_m)
n_dir = int((pts_m["metodo_asignacion"] == "INTERSECCION_DIRECTA").sum())
n_prox = int((pts_m["metodo_asignacion"] == "PROXIMIDAD_UMBRAL").sum())
n_huerf = int((pts_m["metodo_asignacion"] == "MANUAL_PENDIENTE").sum())

print("================ BALANCE DIAGNÓSTICO DE VINCULACIÓN ================")
print(f"Encuestas con coordenada procesadas : {tot}")
print(f"  Asignadas por intersección directa: {n_dir}")
print(f"  Asignadas por proximidad (≤{UMBRAL_M:g} m): {n_prox}")
print(f"  Huérfanas (> {UMBRAL_M:g} m, revisión): {n_huerf}")
print("Confianza:", pts_m["nivel_confianza"].value_counts().to_dict())
print(f"Requieren visita de campo           : {int(pts_m['requiere_visita_campo'].sum())}")
print(f"Predios con ≥1 encuesta             : {len(predios_con)} de {len(terr_slim)}")
print(f"Predios SIN encuesta (cobertura)    : {len(predios_sin)}")
multi = int((n_por_predio > 1).sum())
print(f"Predios con MÚLTIPLES encuestas (N:1): {multi}")
print("Semáforo por predio:", terr_sem["confianza_predio"].value_counts().to_dict())
print(f"\nGuardado: {GPKG}")
print("  capas: encuestas_vinculadas, predios_sin_encuesta, predios_semaforo")
print(f"GeoJSON para el mapa: {OUT_DIR / 'predios_semaforo.geojson'}")
print(f"CSV predios sin encuesta: {OUT_DIR / 'predios_sin_encuesta.csv'}")
