import pandas as pd
import random
from datetime import datetime, timedelta
from fuzzywuzzy import fuzz
from src.database import SessionLocal, Factura
import os

def generar_estado_cuenta(output_path: str = "data/csv/estado_cuenta.csv"):
    os.makedirs("data/csv", exist_ok=True)
    session = SessionLocal()
    facturas = session.query(Factura).limit(400).all()
    session.close()

    movimientos = []
    for factura in facturas:
        if random.random() < 0.85:
            variacion = random.uniform(-0.02, 0.02)
            monto_pagado = round(factura.total * (1 + variacion), 2)
            fecha_pago = datetime.strptime(
                factura.fecha[:10], "%Y-%m-%d"
            ) + timedelta(days=random.randint(1, 30))

            nombre_banco = factura.receptor_nombre
            if random.random() < 0.3:
                nombre_banco = nombre_banco[:15].upper() + " SA"

            movimientos.append({
                "fecha_movimiento": fecha_pago.strftime("%Y-%m-%d"),
                "descripcion": f"PAGO PROV {nombre_banco}",
                "monto": monto_pagado,
                "referencia": f"REF{random.randint(100000, 999999)}",
                "tipo": "CARGO"
            })

    for _ in range(20):
        movimientos.append({
            "fecha_movimiento": datetime(
                random.randint(2022, 2025),
                random.randint(1, 12),
                random.randint(1, 28)
            ).strftime("%Y-%m-%d"),
            "descripcion": "PAGO PROV EMPRESA DESCONOCIDA SA DE CV",
            "monto": round(random.uniform(5000, 150000), 2),
            "referencia": f"REF{random.randint(100000, 999999)}",
            "tipo": "CARGO"
        })

    df = pd.DataFrame(movimientos)
    df.to_csv(output_path, index=False)
    print(f"[Conciliacion] Estado de cuenta generado: {len(movimientos)} movimientos")
    return df

def conciliar(umbral_fuzzy: int = 75) -> dict:
    print("[Conciliacion] Iniciando conciliación bancaria...")

    estado_path = "data/csv/estado_cuenta.csv"
    if not os.path.exists(estado_path):
        generar_estado_cuenta(estado_path)

    df_banco = pd.read_csv(estado_path)
    session = SessionLocal()
    facturas = session.query(Factura).all()
    session.close()

    conciliadas = []
    sin_match = []
    discrepancias = []

    for _, mov in df_banco.iterrows():
        mejor_score = 0
        mejor_factura = None

        for factura in facturas:
            nombre_factura = factura.receptor_nombre or ""
            score = fuzz.partial_ratio(
                mov["descripcion"].upper(),
                nombre_factura.upper()
            )
            if score > mejor_score:
                mejor_score = score
                mejor_factura = factura

        if mejor_score >= umbral_fuzzy and mejor_factura:
            diferencia = abs(mov["monto"] - mejor_factura.total)
            porcentaje_dif = diferencia / mejor_factura.total * 100

            if porcentaje_dif > 5:
                discrepancias.append({
                    "referencia": mov["referencia"],
                    "proveedor": mejor_factura.receptor_nombre,
                    "monto_banco": mov["monto"],
                    "monto_factura": mejor_factura.total,
                    "diferencia": round(diferencia, 2),
                    "porcentaje": round(porcentaje_dif, 2)
                })
            else:
                conciliadas.append(mov["referencia"])
        else:
            sin_match.append({
                "referencia": mov["referencia"],
                "descripcion": mov["descripcion"],
                "monto": mov["monto"],
                "fecha": mov["fecha_movimiento"]
            })

    df_sin_match = pd.DataFrame(sin_match)
    df_discrepancias = pd.DataFrame(discrepancias)

    if not df_sin_match.empty:
        df_sin_match.to_csv("data/csv/pagos_sin_factura.csv", index=False)

    if not df_discrepancias.empty:
        df_discrepancias.to_csv("data/csv/discrepancias.csv", index=False)

    resumen = {
        "total_movimientos": len(df_banco),
        "conciliados": len(conciliadas),
        "sin_match": len(sin_match),
        "discrepancias": len(discrepancias),
        "tasa_conciliacion": round(len(conciliadas) / len(df_banco) * 100, 2)
    }

    print(f"[Conciliacion] Resultados:")
    print(f"  Total movimientos: {resumen['total_movimientos']}")
    print(f"  Conciliados: {resumen['conciliados']}")
    print(f"  Sin match: {resumen['sin_match']}")
    print(f"  Discrepancias de monto: {resumen['discrepancias']}")
    print(f"  Tasa de conciliación: {resumen['tasa_conciliacion']}%")

    return resumen

if __name__ == "__main__":
    generar_estado_cuenta()
    conciliar()