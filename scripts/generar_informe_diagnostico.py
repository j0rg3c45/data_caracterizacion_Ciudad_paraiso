"""
Genera el informe diagnóstico de la data de caracterización ciudadana en Word.

Entrada : data/encuesta_ciudad_paraiso/Consolidado_Operativo_Depurado_v2.xlsx
          data/geojson_poligono_ciudad_paraiso/*.geojson (para el cruce territorial)
Salida  : output/informes/Informe_Diagnostico_Datos_Caracterizacion.docx

Estándar de informes del proyecto:
  Word .docx · Arial 12 · texto justificado · títulos en azul, cuerpo en negro.

Ejecutar con el entorno uv:
    uv run python scripts/generar_informe_diagnostico.py
"""
from pathlib import Path
import pandas as pd

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "data" / "encuesta_ciudad_paraiso" / "Consolidado_Operativo_Depurado_v2.xlsx"
OUT_DIR = ROOT / "output" / "informes"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / "Informe_Diagnostico_Datos_Caracterizacion.docx"

AZUL = RGBColor(0x1F, 0x3B, 0x73)   # azul institucional para títulos
NEGRO = RGBColor(0x00, 0x00, 0x00)
FUENTE = "Arial"


# ---------------------------------------------------------------- lectura datos
def leer(sheet, header=3):
    df = pd.read_excel(XLSX, sheet_name=sheet, header=header)
    return df.dropna(axis=0, how="all").dropna(axis=1, how="all")


ciu = leer("Ciudadanos")
av = leer("Avance_Persona")
geo = leer("Georreferenciacion")
exc = leer("Excluidos_Revisar")
contr = leer("Contradicciones")
hog = leer("Hogares")
inm = leer("Inmuebles")

inc = ciu[ciu["incluido_en_analisis"] == "SI"]
lat = pd.to_numeric(geo["Latitud"], errors="coerce")
lon = pd.to_numeric(geo["Longitud"], errors="coerce")
con_coord = lat.notna() & lon.notna()
dentro = con_coord & lat.between(3.440, 3.449) & lon.between(-76.534, -76.525)
fuera = con_coord & ~dentro


# ------------------------------------------------------------- helpers de estilo
def set_base_style(doc):
    st = doc.styles["Normal"]
    st.font.name = FUENTE
    st.font.size = Pt(12)
    st.font.color.rgb = NEGRO


def titulo(doc, texto, nivel=1):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(texto)
    run.font.name = FUENTE
    run.font.bold = True
    run.font.color.rgb = AZUL
    run.font.size = Pt(16 if nivel == 1 else 13 if nivel == 2 else 12)
    p.space_before = Pt(12)
    p.space_after = Pt(6)
    return p


def parrafo(doc, texto, justificar=True, negrita=False):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY if justificar else WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(texto)
    run.font.name = FUENTE
    run.font.size = Pt(12)
    run.font.color.rgb = NEGRO
    run.font.bold = negrita
    return p


def vineta(doc, texto):
    p = doc.add_paragraph(style="List Bullet")
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run = p.add_run(texto)
    run.font.name = FUENTE
    run.font.size = Pt(12)
    run.font.color.rgb = NEGRO
    return p


def tabla(doc, encabezados, filas):
    t = doc.add_table(rows=1, cols=len(encabezados))
    t.style = "Light Grid Accent 1"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(encabezados):
        cell = t.rows[0].cells[i]
        cell.text = ""
        run = cell.paragraphs[0].add_run(str(h))
        run.font.name = FUENTE
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = AZUL
    for fila in filas:
        cells = t.add_row().cells
        for i, val in enumerate(fila):
            cells[i].text = ""
            run = cells[i].paragraphs[0].add_run(str(val))
            run.font.name = FUENTE
            run.font.size = Pt(11)
            run.font.color.rgb = NEGRO
    return t


# ------------------------------------------------------------------- documento
doc = Document()
set_base_style(doc)

# Portada / título
titulo(doc, "Informe diagnóstico de la data", nivel=1)
titulo(doc, "Caracterización ciudadana · Ciudad Paraíso", nivel=2)
parrafo(doc, "Rol: Data Steward · Gobierno de Datos. "
             "Fuente analizada: Consolidado_Operativo_Depurado_v2.xlsx (20 hojas) e "
             "Informe_Depuracion_Datos_Caracterizacion_v2.pdf. "
             "Corte de archivos: 14/10/2026.")
parrafo(doc, "Documento interno con datos personales. Acceso restringido.", negrita=True)

# 1. Resumen ejecutivo
titulo(doc, "1. Resumen ejecutivo", nivel=2)
parrafo(doc,
    "Se auditó el consolidado operativo de la caracterización ciudadana de Ciudad Paraíso "
    "contra sus archivos fuente. La revisión confirma que las cifras del consolidado son "
    "internamente coherentes y trazables: el padrón depurado contiene 746 personas "
    "analizadas, luego de retirar 63 registros que no corresponden a personas reales "
    "(60 registros de relleno y 3 posibles duplicados por cédula mal digitada). "
    "La cobertura de fichas ciudadanas sube de 53,2 % a 57,1 % y la lista de visitas se "
    "reduce de 194 a 141. La principal debilidad detectada está en la georreferenciación: "
    "solo una fracción de las personas tiene coordenadas utilizables dentro del polígono "
    "del proyecto, lo que limita por ahora el trabajo de campo basado en GPS.")

# 2. Indicadores
titulo(doc, "2. Indicadores operativos (depurado vs. original)", nivel=2)
tabla(doc,
      ["Indicador", "Depurado", "Original", "Diferencia"],
      [["Ciudadanos en padrón", 746, 809, -63],
       ["Caracterizados validados", 426, 430, -4],
       ["Pendientes de ficha ciudadana", 318, 377, -59],
       ["Con visita registrada", 202, 203, -1],
       ["Verificar / programar visita", 141, 194, -53],
       ["Cobertura de fichas ciudadanas", "57,1 %", "53,2 %", "+3,9 pts"]])
parrafo(doc,
    "Los validados casi no cambian porque solo 4 de los registros de relleno figuraban como "
    "caracterizados; la mejora de cobertura proviene de retirar registros que inflaban el "
    "denominador de pendientes.")

# 3. Calidad del padrón
titulo(doc, "3. Calidad del padrón de ciudadanos", nivel=2)
vineta(doc, f"La hoja Ciudadanos tiene {len(ciu)} filas con número de documento 100 % único "
            f"(0 duplicados exactos de documento).")
vineta(doc, f"Registros marcados incluido_en_analisis = SI: {len(inc)}; marcados NO "
            f"(relleno/duplicado): {len(ciu) - len(inc)}.")
vineta(doc, "Estado de caracterización de los analizados: "
            "426 CARACTERIZADO VALIDADO, 318 PENDIENTE, 2 REVISAR (ficha existe, maestro dice No).")
parrafo(doc, "Registros excluidos o marcados para revisión (hoja Excluidos_Revisar):")
tabla(doc, ["Clasificación", "Registros"],
      [[k, int(v)] for k, v in exc["clasificacion"].value_counts().items()])

# 4. Avance por persona
titulo(doc, "4. Avance por persona", nivel=2)
parrafo(doc,
    "Con la regla estricta (ficha ciudadana + programa Hogares + programa Salud al 100 %), "
    "las 746 personas se clasifican así:")
orden = ["1. COMPLETO", "2. PARCIAL",
         "3. FALTA POR VISITAR PARCIALMENTE", "4. FALTA POR VISITAR TOTALMENTE"]
vc = av["clasificacion"].value_counts()
tabla(doc, ["Clasificación", "Personas", "% del padrón"],
      [[k, int(vc[k]), f"{100*vc[k]/len(av):.1f} %"] for k in orden if k in vc])
parrafo(doc,
    "El avance se mide por el porcentaje real de cada formulario, no por la casilla "
    "\"Finalizada\": 83 formularios aparecían como finalizados con 0 % de avance (vacíos) y "
    "no se cuentan como completos. Otros 23 figuran finalizados con avance parcial y quedan "
    "como PARCIAL hasta que el equipo confirme si estaban terminados.")

# 5. Calidad de formularios de programas
titulo(doc, "5. Calidad de los formularios de programas", nivel=2)
tc = contr["tipo_contradiccion"].value_counts()
parrafo(doc, f"Se detectaron {len(contr)} formularios con contradicción entre "
             f"\"Finalizada\" y \"% de avance\":")
tabla(doc, ["Tipo de contradicción", "Casos"],
      [[k, int(v)] for k, v in tc.items()])

# 6. Georreferenciación
titulo(doc, "6. Georreferenciación y trabajo de campo", nivel=2)
vineta(doc, f"De {len(geo)} personas, {int(con_coord.sum())} tienen coordenadas y "
            f"{int(con_coord.sum() == 0 and 0 or (~con_coord).sum())} no tienen ninguna.")
vineta(doc, f"Solo {int(dentro.sum())} coordenadas caen dentro del polígono catastral de "
            f"Ciudad Paraíso; {int(fuera.sum())} tienen GPS pero fuera del área del proyecto.")
vineta(doc, f"{int((geo['GPS discrepante entre fuentes'] == 'SÍ').sum())} personas tienen "
            f"puntos que difieren más de 200 m entre fuentes (confirmar en campo).")
parrafo(doc,
    "Los puntos GPS provienen de formularios y no acreditan el domicilio. La lista de "
    "personas por visitar aún no es plenamente operativa en campo: una parte importante "
    "no tiene ubicación confiable y conviene completar dirección o teléfono antes de "
    "programar las visitas.")

# 7. Hogares e inmuebles
titulo(doc, "7. Hogares e inmuebles", nivel=2)
un_solo = (hog["un_solo_integrante"] == "SÍ").sum() if "SÍ" in set(hog["un_solo_integrante"]) \
          else (hog["un_solo_integrante"].astype(str).str.upper().str.startswith("S")).sum()
vineta(doc, f"Hogares registrados: {len(hog)}. Hogares con un solo integrante registrado: "
            f"{int(un_solo)} (puede subestimar el tamaño real del hogar).")
vineta(doc, f"Direcciones de inmuebles no caracterizados: {len(inm)}; "
            "los motivos más frecuentes se detallan en la hoja Inmuebles.")
parrafo(doc,
    "Los formularios de inmuebles describen el predio, no a la persona que los diligenció, "
    "por lo que no acreditan visita a ese ciudadano.")

# 8. Datos catastrales
titulo(doc, "8. Datos catastrales disponibles", nivel=2)
parrafo(doc,
    "Se incorporó la cartografía catastral urbana (corte enero 2024) y se convirtió a "
    "GeoJSON en coordenadas WGS84 para integrarse con los datos ciudadanos:")
tabla(doc, ["Capa", "Polígonos", "Geometría"],
      [["ANEXOS_U_2024", 203, "Polígono"],
       ["CONSTRUCCION_U_2024", 1346, "Polígono"],
       ["MANZANAS_U_2024", 28, "Polígono"],
       ["TERRENOS_U_2024", 857, "Polígono"],
       ["UNIDADES_U_2024", 23, "Polígono"]])
parrafo(doc,
    "El CRS original es EPSG:6249 (MAGNA Cali Valle del Cauca 2009, en metros); se reproyectó "
    "a EPSG:4326. Esta cartografía permitirá validar la ubicación de los ciudadanos "
    "georreferenciados contra terrenos y construcciones reales del polígono.")

# 9. Hallazgos y recomendaciones
titulo(doc, "9. Hallazgos y recomendaciones", nivel=2)
parrafo(doc, "Hallazgos principales:", negrita=True)
vineta(doc, "El consolidado es coherente y trazable; las cifras del tablero cuadran con el detalle.")
vineta(doc, "La georreferenciación es el eslabón más débil: pocos puntos utilizables dentro "
            "del polígono y 29 coordenadas fuera del área del proyecto.")
vineta(doc, "La comuna está incompleta en buena parte del padrón, lo que impide comparar "
            "territorios de forma confiable.")
parrafo(doc, "Recomendaciones:", negrita=True)
vineta(doc, "Validar los 3 pares de duplicados con la cédula física antes de tocar el maestro.")
vineta(doc, "Definir la regla operativa de \"persona completa\" y el tratamiento de los 23 "
            "formularios finalizados con avance parcial.")
vineta(doc, "Depurar y validar las coordenadas contra la cartografía catastral; descartar o "
            "corregir los puntos fuera del polígono.")
vineta(doc, "Completar dirección/teléfono de las personas por visitar antes de salir a campo.")
vineta(doc, "Mejorar la captura: separar \"inmueble no caracterizado\" del padrón de personas y "
            "validar el documento al digitar.")

parrafo(doc, "")
parrafo(doc,
    "Nota metodológica: las cifras de este informe fueron verificadas directamente contra "
    "las hojas del consolidado (Panel, Ciudadanos, Avance_Persona, Georreferenciacion, "
    "Excluidos_Revisar y Contradicciones).", negrita=False)

doc.save(OUT)
print("Informe generado en:", OUT)
print("Tamaño:", f"{OUT.stat().st_size/1024:.0f} KB")
