import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Float, Boolean, DateTime, Integer, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import text
from datetime import datetime

load_dotenv()

DB_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Factura(Base):
    __tablename__ = "facturas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False)
    archivo = Column(String(200))
    serie = Column(String(10))
    folio = Column(String(20))
    fecha = Column(String(30))
    subtotal = Column(Float)
    total = Column(Float)
    total_impuestos = Column(Float)
    tipo_comprobante = Column(String(5))
    metodo_pago = Column(String(5))
    forma_pago = Column(String(5))
    moneda = Column(String(5))
    emisor_rfc = Column(String(15))
    emisor_nombre = Column(String(200))
    emisor_regimen = Column(String(10))
    receptor_rfc = Column(String(15))
    receptor_nombre = Column(String(200))
    receptor_uso_cfdi = Column(String(10))
    concepto_descripcion = Column(Text)
    concepto_clave = Column(String(20))
    concepto_cantidad = Column(Float)
    concepto_importe = Column(Float)
    fecha_timbrado = Column(String(30))
    no_certificado_sat = Column(String(30))
    es_valido = Column(Boolean, default=True)
    errores_validacion = Column(Text)
    es_anomalia = Column(Boolean, default=False)
    score_anomalia = Column(Float, default=0.0)
    categoria_concepto = Column(String(100))
    creado_en = Column(DateTime, default=datetime.now)

class AlertaAuditoria(Base):
    __tablename__ = "alertas_auditoria"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid_factura = Column(String(36))
    tipo_alerta = Column(String(50))
    descripcion = Column(Text)
    severidad = Column(String(20))
    creado_en = Column(DateTime, default=datetime.now)

def init_db():
    Base.metadata.create_all(engine)
    print("[DB] Tablas creadas en PostgreSQL")

def insertar_facturas(facturas: list) -> int:
    session = SessionLocal()
    insertadas = 0
    try:
        for f in facturas:
            existente = session.query(Factura).filter_by(uuid=f.get("uuid")).first()
            if existente:
                continue
            factura = Factura(
                uuid=f.get("uuid"),
                archivo=f.get("archivo"),
                serie=f.get("serie"),
                folio=f.get("folio"),
                fecha=f.get("fecha"),
                subtotal=f.get("subtotal"),
                total=f.get("total"),
                total_impuestos=f.get("total_impuestos"),
                tipo_comprobante=f.get("tipo_comprobante"),
                metodo_pago=f.get("metodo_pago"),
                forma_pago=f.get("forma_pago"),
                moneda=f.get("moneda"),
                emisor_rfc=f.get("emisor_rfc"),
                emisor_nombre=f.get("emisor_nombre"),
                emisor_regimen=f.get("emisor_regimen"),
                receptor_rfc=f.get("receptor_rfc"),
                receptor_nombre=f.get("receptor_nombre"),
                receptor_uso_cfdi=f.get("receptor_uso_cfdi"),
                concepto_descripcion=f.get("concepto_descripcion"),
                concepto_clave=f.get("concepto_clave"),
                concepto_cantidad=f.get("concepto_cantidad"),
                concepto_importe=f.get("concepto_importe"),
                fecha_timbrado=f.get("fecha_timbrado"),
                no_certificado_sat=f.get("no_certificado_sat"),
                es_valido=f.get("es_valido", True),
                errores_validacion=str(f.get("errores", [])),
            )
            session.add(factura)
            insertadas += 1
        session.commit()
        print(f"[DB] {insertadas} facturas insertadas en PostgreSQL")
        return insertadas
    except Exception as e:
        session.rollback()
        print(f"[DB] Error: {e}")
        return 0
    finally:
        session.close()

def query_facturas(limit: int = 100) -> list:
    session = SessionLocal()
    try:
        return session.query(Factura).limit(limit).all()
    finally:
        session.close()

def get_stats() -> dict:
    session = SessionLocal()
    try:
        total = session.query(Factura).count()
        validas = session.query(Factura).filter_by(es_valido=True).count()
        anomalias = session.query(Factura).filter_by(es_anomalia=True).count()
        resultado = session.execute(
            text("SELECT SUM(total) FROM facturas")
        ).scalar()
        total_mxn = float(resultado or 0)
        return {
            "total_facturas": total,
            "validas": validas,
            "invalidas": total - validas,
            "anomalias": anomalias,
            "total_mxn": round(total_mxn, 2)
        }
    finally:
        session.close()

if __name__ == "__main__":
    init_db()
    print("[DB] Base de datos lista")