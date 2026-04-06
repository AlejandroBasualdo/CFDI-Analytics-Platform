from src.parser import parsear_directorio
from src.validator import validar_cfdi
from src.database import insertar_facturas, init_db
from datetime import datetime

def ejecutar_pipeline(directorio: str = "data/xml") -> dict:
    inicio = datetime.now()
    print(f"\n[ETL] Iniciando pipeline — {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    print("[ETL] Paso 1/3 — Parseando CFDIs...")
    cfdis = parsear_directorio(directorio)

    print("[ETL] Paso 2/3 — Validando reglas fiscales del SAT...")
    validos = 0
    invalidos = 0
    cfdis_enriquecidos = []

    for cfdi in cfdis:
        resultado = validar_cfdi(cfdi)
        cfdi["es_valido"] = resultado["es_valido"]
        cfdi["errores"] = resultado["errores"]
        if resultado["es_valido"]:
            validos += 1
        else:
            invalidos += 1
        cfdis_enriquecidos.append(cfdi)

    print(f"[ETL] Validación completa — {validos} válidos, {invalidos} inválidos")

    print("[ETL] Paso 3/3 — Insertando en PostgreSQL...")
    insertadas = insertar_facturas(cfdis_enriquecidos)

    fin = datetime.now()
    duracion = (fin - inicio).seconds

    resumen = {
        "total_procesados": len(cfdis),
        "validos": validos,
        "invalidos": invalidos,
        "insertadas_db": insertadas,
        "duracion_segundos": duracion
    }

    print("=" * 55)
    print(f"[ETL] Pipeline completado en {duracion}s")
    print(f"[ETL] Total procesados: {len(cfdis)}")
    print(f"[ETL] Insertados en DB: {insertadas}")
    return resumen

if __name__ == "__main__":
    init_db()
    ejecutar_pipeline()