import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder
from sqlalchemy import text
from src.database import engine, SessionLocal, Factura, AlertaAuditoria
from datetime import datetime

def cargar_facturas_df() -> pd.DataFrame:
    with engine.connect() as conn:
        df = pd.read_sql(
            "SELECT * FROM facturas",
            conn
        )
    return df

def detectar_anomalias(contamination: float = 0.05) -> dict:
    print("[Anomaly] Cargando facturas de PostgreSQL...")
    df = cargar_facturas_df()

    if len(df) < 10:
        print("[Anomaly] No hay suficientes datos")
        return {}

    print(f"[Anomaly] Analizando {len(df)} facturas...")

    le_rfc = LabelEncoder()
    le_uso = LabelEncoder()
    le_metodo = LabelEncoder()

    df["receptor_rfc_enc"] = le_rfc.fit_transform(df["receptor_rfc"].fillna("DESCONOCIDO"))
    df["uso_cfdi_enc"] = le_uso.fit_transform(df["receptor_uso_cfdi"].fillna("G03"))
    df["metodo_pago_enc"] = le_metodo.fit_transform(df["metodo_pago"].fillna("PUE"))
    df["hora"] = pd.to_datetime(df["fecha"], errors="coerce").dt.hour.fillna(12)
    df["dia_semana"] = pd.to_datetime(df["fecha"], errors="coerce").dt.dayofweek.fillna(0)
    df["mes"] = pd.to_datetime(df["fecha"], errors="coerce").dt.month.fillna(1)

    features = [
        "subtotal", "total", "total_impuestos",
        "concepto_cantidad", "concepto_importe",
        "receptor_rfc_enc", "uso_cfdi_enc",
        "metodo_pago_enc", "hora", "dia_semana", "mes"
    ]

    X = df[features].fillna(0)

    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=42,
        n_jobs=-1
    )

    preds = model.fit_predict(X)
    scores = model.score_samples(X)

    df["es_anomalia"] = (preds == -1).astype(bool)
    df["score_anomalia"] = scores

    session = SessionLocal()
    try:
        anomalias_detectadas = 0
        alertas_creadas = 0

        for _, row in df.iterrows():
            factura = session.query(Factura).filter_by(uuid=row["uuid"]).first()
            if factura:
                factura.es_anomalia = bool(row["es_anomalia"])
                factura.score_anomalia = float(row["score_anomalia"])

                if row["es_anomalia"]:
                    anomalias_detectadas += 1

                    monto_promedio = df[
                        df["receptor_rfc"] == row["receptor_rfc"]
                    ]["total"].mean()

                    if row["total"] > monto_promedio * 3:
                        tipo = "MONTO_ATIPICO"
                        desc = f"Factura de ${row['total']:,.2f} es 3x mayor al promedio del proveedor (${monto_promedio:,.2f})"
                        severidad = "ALTA"
                    elif row["hora"] < 6 or row["hora"] > 22:
                        tipo = "HORARIO_INUSUAL"
                        desc = f"Factura emitida a las {int(row['hora'])}:00 hrs — fuera de horario laboral"
                        severidad = "MEDIA"
                    else:
                        tipo = "PATRON_ANOMALO"
                        desc = f"Patrón estadístico anómalo detectado por Isolation Forest (score: {row['score_anomalia']:.4f})"
                        severidad = "BAJA"

                    alerta = AlertaAuditoria(
                        uuid_factura=row["uuid"],
                        tipo_alerta=tipo,
                        descripcion=desc,
                        severidad=severidad
                    )
                    session.add(alerta)
                    alertas_creadas += 1

        session.commit()

        uuid_duplicados = df[df.duplicated(subset=["uuid"], keep=False)]["uuid"].unique()
        for uuid in uuid_duplicados:
            alerta = AlertaAuditoria(
                uuid_factura=uuid,
                tipo_alerta="DUPLICADO",
                descripcion=f"UUID duplicado detectado: {uuid}",
                severidad="ALTA"
            )
            session.add(alerta)
        session.commit()

        resumen = {
            "total_analizadas": len(df),
            "anomalias_detectadas": anomalias_detectadas,
            "porcentaje_anomalias": round(anomalias_detectadas / len(df) * 100, 2),
            "alertas_creadas": alertas_creadas,
            "duplicados_detectados": len(uuid_duplicados)
        }

        print(f"[Anomaly] Detección completa:")
        print(f"  Anomalías: {anomalias_detectadas} ({resumen['porcentaje_anomalias']}%)")
        print(f"  Alertas generadas: {alertas_creadas}")
        print(f"  Duplicados: {len(uuid_duplicados)}")
        return resumen

    except Exception as e:
        session.rollback()
        print(f"[Anomaly] Error: {e}")
        return {}
    finally:
        session.close()

if __name__ == "__main__":
    detectar_anomalias()