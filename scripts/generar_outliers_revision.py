"""
Genera el listado de puntos para revisión en campo / gabinete (protocolo 7.3).

Clasifica cada punto georreferenciado según el control de calidad geoespacial:
  - FUERA DE ZONA        -> outlier; requiere verificación (posible re-visita).
  - COORDENADA REPETIDA  -> mismo punto exacto que otro registro (posible error GPS).
  - EJES INVERTIDOS      -> lat/lon trocadas y corregidas.
  - OK                   -> dentro del polígono, coordenada única.

Entrada : data/encuesta_ciudad_paraiso/Consolidado_Operativo_Depurado_v2.xlsx
          data/geojson_poligono_ciudad_paraiso/poligono_ciudad_Paraiso.geojson
Salida  : output/Puntos_Revision_Campo.xlsx

Ejecutar con el entorno uv:
    uv run python scripts/generar_outliers_revision.py
"""
from pathlib import Path
import pandas as pd
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "data" / "encuesta_ciudad_paraiso" / "Consolidado_Operativo_Depurado_v2.xlsx"
POLY = ROOT / "data" / "geojson_poligono_ciudad_paraiso" / "poligono_ciudad_Paraiso.geojson"
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / "Puntos_Revision_Campo.xlsx"


def leer_hoja(sheet, header=3):
    df = pd.read_excel(XLSX, sheet_name=sheet, header=header)
    return df.dropna(axis=0, how="all").dropna(axis=1, how="all")


geo = leer_hoja("Georreferenciacion")

# --- validación/limpieza igual que el notebook ---
g = geo.copy()
g["lat"] = pd.to_numeric(g["Latitud"], errors="coerce")
g["lon"] = pd.to_numeric(g["Longitud"], errors="coerce")
g.loc[(g["lat"] == 0) & (g["lon"] == 0), ["lat", "lon"]] = pd.NA

troc = (g["lat"] < 0) & (g["lon"] > 0)
g["ejes_invertidos"] = troc
if troc.any():
    g.loc[troc, ["lat", "lon"]] = g.loc[troc, ["lon", "lat"]].values

g["coord_repetida"] = g.duplicated(subset=["lat", "lon"], keep=False) & g["lat"].notna()

val = g[g["lat"].notna() & g["lon"].notna()].copy()
pts = gpd.GeoDataFrame(val, geometry=gpd.points_from_xy(val["lon"], val["lat"]), crs="EPSG:4326")

poligono = gpd.read_file(POLY).to_crs(4326)
area = poligono.geometry.union_all()
pts["dentro_poligono"] = pts.within(area)


def motivo(r):
    motivos = []
    if not r["dentro_poligono"]:
        motivos.append("FUERA DE ZONA")
    if r["coord_repetida"]:
        motivos.append("COORDENADA REPETIDA")
    if r["ejes_invertidos"]:
        motivos.append("EJES INVERTIDOS (corregidos)")
    return " | ".join(motivos) if motivos else "OK"


def accion(r):
    if not r["dentro_poligono"]:
        return "RE-VISITA / verificar ubicación en campo"
    if r["coord_repetida"] or r["ejes_invertidos"]:
        return "Revisar en gabinete (coordenada dudosa)"
    return "Sin acción"


pts["motivo_revision"] = pts.apply(motivo, axis=1)
pts["accion_sugerida_qc"] = pts.apply(accion, axis=1)

# --- selección de columnas para el entregable ---
cols = [
    "Nombre ciudadano", "Número documento", "Tipo documento", "Estado ficha",
    "Dirección para visita", "Barrio", "Comuna", "Teléfono móvil",
    "lat", "lon", "Fuente coordenadas", "GPS discrepante entre fuentes",
    "motivo_revision", "accion_sugerida_qc",
]
cols = [c for c in cols if c in pts.columns]
revision = pts[pts["motivo_revision"] != "OK"][cols].copy()
revision = revision.rename(columns={"lat": "Latitud", "lon": "Longitud"})

# resumen por motivo
resumen = (pts["motivo_revision"].value_counts().rename_axis("motivo")
           .reset_index(name="registros"))

with pd.ExcelWriter(OUT, engine="openpyxl") as xl:
    resumen.to_excel(xl, sheet_name="Resumen", index=False)
    revision.to_excel(xl, sheet_name="Puntos_a_revisar", index=False)

print("Listado generado:", OUT)
print("Total puntos con coordenada:", len(pts))
print("Puntos a revisar:", len(revision))
print(resumen.to_string(index=False))
