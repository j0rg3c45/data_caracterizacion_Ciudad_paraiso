"""
Convierte los shapefiles catastrales a GeoJSON (EPSG:4326 / WGS84).

Entrada : data/catastral/*.shp        (CRS EPSG:6249 - MAGNA Cali Valle 2009)
Salida  : data/geojson_poligono_ciudad_paraiso/*.geojson

GeoJSON (RFC 7946) requiere coordenadas en WGS84, por eso se reproyecta.
Las fuentes en data/ no se modifican.

Ejecutar con el entorno uv:
    uv run python scripts/shp_to_geojson.py
"""
from pathlib import Path
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "catastral"
DST = ROOT / "data" / "geojson_poligono_ciudad_paraiso"
DST.mkdir(parents=True, exist_ok=True)

shapefiles = sorted(SRC.glob("*.shp"))
if not shapefiles:
    raise SystemExit(f"No se encontraron shapefiles en {SRC}")

for shp in shapefiles:
    gdf = gpd.read_file(shp)
    src_crs = gdf.crs
    if gdf.crs is None:
        raise SystemExit(f"{shp.name} no tiene CRS definido; revisar el .prj")
    gdf_wgs84 = gdf.to_crs(epsg=4326)

    out = DST / f"{shp.stem}.geojson"
    gdf_wgs84.to_file(out, driver="GeoJSON")
    size_kb = out.stat().st_size / 1024
    print(f"{shp.name:28s} -> {out.name:28s} "
          f"{len(gdf_wgs84):5d} feats  CRS {src_crs.to_epsg()} -> 4326  "
          f"({size_kb:,.0f} KB)")

print(f"\nListo. {len(shapefiles)} archivos en {DST}")
