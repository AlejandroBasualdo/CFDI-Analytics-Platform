import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from src.database import SessionLocal, Factura

CATEGORIAS = {
    "Materia prima": [
        "acero", "aluminio", "lamina", "metal", "hierro", "cobre",
        "plastico", "resina", "quimico", "materia prima", "material"
    ],
    "Servicios industriales": [
        "mantenimiento", "soldadura", "reparacion", "instalacion",
        "servicio", "maquinado", "maquila", "proceso", "calibracion"
    ],
    "Logística y transporte": [
        "transporte", "flete", "logistica", "envio", "traslado",
        "carga", "distribucion", "almacen", "paqueteria"
    ],
    "Herramientas y equipos": [
        "herramienta", "equipo", "maquinaria", "refaccion", "tornillo",
        "tornilleria", "pieza", "componente", "accesorio", "herramienta"
    ],
    "Consultoría y profesionales": [
        "consultoria", "asesoria", "proyecto", "ingenieria", "auditoria",
        "capacitacion", "honorarios", "profesional", "arquitectura"
    ],
    "Pinturas y recubrimientos": [
        "pintura", "recubrimiento", "epoxica", "barniz", "anticorrosivo",
        "galvanizado", "cromado", "tratamiento superficial"
    ],
    "Gastos generales": [
        "papeleria", "oficina", "limpieza", "cafeteria", "uniformes",
        "equipo computo", "software", "licencia", "renta"
    ]
}

try:
    nlp = spacy.load("es_core_news_sm")
except OSError:
    nlp = None
    print("[Classifier] Modelo spaCy no disponible, usando TF-IDF básico")

def clasificar_concepto(descripcion: str) -> str:
    if not descripcion:
        return "Sin clasificar"

    descripcion_lower = descripcion.lower()

    mejor_categoria = "Gastos generales"
    mejor_score = 0

    for categoria, palabras_clave in CATEGORIAS.items():
        score = sum(1 for palabra in palabras_clave if palabra in descripcion_lower)
        if score > mejor_score:
            mejor_score = score
            mejor_categoria = categoria

    if mejor_score == 0 and nlp:
        doc = nlp(descripcion_lower)
        tokens = [token.lemma_ for token in doc if not token.is_stop]
        for categoria, palabras_clave in CATEGORIAS.items():
            score = sum(1 for t in tokens if any(t in p for p in palabras_clave))
            if score > mejor_score:
                mejor_score = score
                mejor_categoria = categoria

    return mejor_categoria

def clasificar_todas_las_facturas() -> dict:
    session = SessionLocal()
    try:
        facturas = session.query(Factura).filter(
            Factura.categoria_concepto == None
        ).all()

        if not facturas:
            facturas = session.query(Factura).all()

        clasificadas = 0
        conteo_categorias = {}

        for factura in facturas:
            categoria = clasificar_concepto(factura.concepto_descripcion)
            factura.categoria_concepto = categoria
            conteo_categorias[categoria] = conteo_categorias.get(categoria, 0) + 1
            clasificadas += 1

        session.commit()

        print(f"[Classifier] {clasificadas} facturas clasificadas:")
        for cat, count in sorted(conteo_categorias.items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count}")

        return conteo_categorias

    except Exception as e:
        session.rollback()
        print(f"[Classifier] Error: {e}")
        return {}
    finally:
        session.close()

if __name__ == "__main__":
    clasificar_todas_las_facturas()