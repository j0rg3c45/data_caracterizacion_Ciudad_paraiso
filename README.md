# Caracterización ciudadana · Ciudad Paraíso (Cali)

Auditoría, depuración y seguimiento operativo de la caracterización ciudadana de
Ciudad Paraíso. Rol: **Data Steward** (gobierno de datos).

## ⚠️ Datos personales (acceso restringido)

Los insumos (`data/`) y las salidas (`output/`) contienen **datos personales**
(documento, nombre, teléfono, correo, dirección). **No se versionan en este repositorio**
(ver `.gitignore`). Cada integrante conserva su copia local de `data/`; en Google Colab
los archivos se suben en sesión.

Este repositorio contiene **solo código y documentación**.

## Estructura

| Carpeta      | Contenido                                                      | ¿En Git? |
|--------------|----------------------------------------------------------------|----------|
| `contexto/`  | Contexto del proyecto, flujo y documentación de referencia.    | Sí (`.md`) |
| `data/`      | Insumos originales (datos personales).                         | **No**   |
| `notebooks/` | Notebooks (`.ipynb`): mapa interactivo, análisis.              | Sí       |
| `output/`    | Salidas e informes.                                            | **No**   |
| `scripts/`   | Scripts del proyecto (los temporales se borran al terminar).   | Sí       |

## Entorno

- Python vía **uv** (`C:\Users\Jorge\.venv`): pandas, geopandas, folium, openpyxl, python-docx.
- Ejecutar scripts: `uv run python scripts/<script>.py`
- Notebooks: detectan el entorno automáticamente (Local vs. Google Colab).

## Documentación

El contexto completo del proyecto está en
[`contexto/CONTEXTO_PROYECTO.md`](contexto/CONTEXTO_PROYECTO.md).
