import os
import random
from datetime import datetime, timedelta
from faker import Faker
from lxml import etree

fake = Faker("es_MX")

EMISOR = {
    "rfc": "ANO850312AB1",
    "nombre": "ACEROS DEL NORTE SA DE CV",
    "regimen": "601"
}

PROVEEDORES = [
    {"rfc": "FIN920315KL8", "nombre": "FERRETERIA INDUSTRIAL DEL NORTE SA DE CV"},
    {"rfc": "TMA011228PQ3", "nombre": "TRANSPORTES MARTINEZ SA DE CV"},
    {"rfc": "SME030610RS7", "nombre": "SUMINISTROS METALICOS DEL ESTE SA DE CV"},
    {"rfc": "LIN850101TU2", "nombre": "LOGISTICA INTEGRAL NORESTE SA DE CV"},
    {"rfc": "PRO760415VW9", "nombre": "PROVEEDORA REGIOMONTANA SA DE CV"},
    {"rfc": "IND991130XY4", "nombre": "INDUSTRIAS DEL NORESTE SA DE CV"},
    {"rfc": "COM880722ZA6", "nombre": "COMERCIALIZADORA MTY SA DE CV"},
    {"rfc": "SER950318BC1", "nombre": "SERVICIOS ESPECIALIZADOS SA DE CV"},
    {"rfc": "MAT010925DE5", "nombre": "MATERIALES Y CONSTRUCCION SA DE CV"},
    {"rfc": "TEC040817FG3", "nombre": "TECNOLOGIA INDUSTRIAL SA DE CV"},
]

CONCEPTOS = [
    {"desc": "Lámina de acero galvanizado calibre 20", "clave": "72154400", "precio_min": 5000, "precio_max": 80000},
    {"desc": "Servicio de mantenimiento industrial", "clave": "76111500", "precio_min": 2000, "precio_max": 50000},
    {"desc": "Materia prima aluminio extruido", "clave": "11101700", "precio_min": 10000, "precio_max": 150000},
    {"desc": "Transporte de carga terrestre", "clave": "78101800", "precio_min": 1500, "precio_max": 25000},
    {"desc": "Tornillería industrial especializada", "clave": "31161500", "precio_min": 500, "precio_max": 15000},
    {"desc": "Servicio de soldadura MIG/TIG", "clave": "72103200", "precio_min": 3000, "precio_max": 40000},
    {"desc": "Pintura epóxica industrial", "clave": "31201500", "precio_min": 2000, "precio_max": 30000},
    {"desc": "Consultoría en procesos industriales", "clave": "80101500", "precio_min": 5000, "precio_max": 100000},
]

USOS_CFDI = ["G01", "G03", "I01", "I03"]
METODOS_PAGO = ["PUE", "PPD"]
FORMAS_PAGO = ["01", "02", "03", "04", "28"]

def generar_uuid():
    import uuid
    return str(uuid.uuid4()).upper()

def generar_folio():
    return f"A-{random.randint(100000, 999999)}"

def generar_fecha(inicio="2022-01-01", fin="2025-12-31"):
    inicio_dt = datetime.strptime(inicio, "%Y-%m-%d")
    fin_dt = datetime.strptime(fin, "%Y-%m-%d")
    delta = fin_dt - inicio_dt
    dia_random = inicio_dt + timedelta(days=random.randint(0, delta.days))
    hora = random.randint(8, 18)
    minuto = random.randint(0, 59)
    return dia_random.replace(hour=hora, minute=minuto, second=0)

def generar_cfdi(anomalo=False, duplicado_de=None):
    proveedor = random.choice(PROVEEDORES)
    concepto = random.choice(CONCEPTOS)
    fecha = generar_fecha()
    subtotal = round(random.uniform(concepto["precio_min"], concepto["precio_max"]), 2)

    if anomalo:
        subtotal = subtotal * random.uniform(10, 50)

    iva = round(subtotal * 0.16, 2)
    total = round(subtotal + iva, 2)
    uuid = duplicado_de if duplicado_de else generar_uuid()
    folio = generar_folio()

    NS = "http://www.sat.gob.mx/cfd/4"
    TFD_NS = "http://www.sat.gob.mx/TimbreFiscalDigital"
    nsmap = {
        "cfdi": NS,
        "tfd": TFD_NS,
        "xsi": "http://www.w3.org/2001/XMLSchema-instance"
    }

    root = etree.Element(f"{{{NS}}}Comprobante", nsmap=nsmap)
    root.set("Version", "4.0")
    root.set("Serie", "A")
    root.set("Folio", folio)
    root.set("Fecha", fecha.strftime("%Y-%m-%dT%H:%M:%S"))
    root.set("SubTotal", str(subtotal))
    root.set("Total", str(total))
    root.set("TipoDeComprobante", "I")
    root.set("MetodoPago", random.choice(METODOS_PAGO))
    root.set("FormaPago", random.choice(FORMAS_PAGO))
    root.set("Moneda", "MXN")

    emisor = etree.SubElement(root, f"{{{NS}}}Emisor")
    emisor.set("Rfc", EMISOR["rfc"])
    emisor.set("Nombre", EMISOR["nombre"])
    emisor.set("RegimenFiscal", EMISOR["regimen"])

    receptor = etree.SubElement(root, f"{{{NS}}}Receptor")
    receptor.set("Rfc", proveedor["rfc"])
    receptor.set("Nombre", proveedor["nombre"])
    receptor.set("UsoCFDI", random.choice(USOS_CFDI))
    receptor.set("RegimenFiscalReceptor", "601")
    receptor.set("DomicilioFiscalReceptor", "64000")

    conceptos = etree.SubElement(root, f"{{{NS}}}Conceptos")
    concepto_elem = etree.SubElement(conceptos, f"{{{NS}}}Concepto")
    concepto_elem.set("ClaveProdServ", concepto["clave"])
    concepto_elem.set("Cantidad", str(random.randint(1, 100)))
    concepto_elem.set("ClaveUnidad", "H87")
    concepto_elem.set("Descripcion", concepto["desc"])
    concepto_elem.set("ValorUnitario", str(round(subtotal / random.randint(1, 10), 2)))
    concepto_elem.set("Importe", str(subtotal))

    impuestos = etree.SubElement(root, f"{{{NS}}}Impuestos")
    impuestos.set("TotalImpuestosTrasladados", str(iva))
    traslados = etree.SubElement(impuestos, f"{{{NS}}}Traslados")
    traslado = etree.SubElement(traslados, f"{{{NS}}}Traslado")
    traslado.set("Base", str(subtotal))
    traslado.set("Impuesto", "002")
    traslado.set("TipoFactor", "Tasa")
    traslado.set("TasaOCuota", "0.160000")
    traslado.set("Importe", str(iva))

    complemento = etree.SubElement(root, f"{{{NS}}}Complemento")
    tfd = etree.SubElement(complemento, f"{{{TFD_NS}}}TimbreFiscalDigital")
    tfd.set("Version", "1.1")
    tfd.set("UUID", uuid)
    tfd.set("FechaTimbrado", fecha.strftime("%Y-%m-%dT%H:%M:%S"))
    tfd.set("NoCertificadoSAT", "20001000000300022323")
    tfd.set("SelloCFD", "SIMULADO")
    tfd.set("SelloSAT", "SIMULADO")

    return root, uuid, fecha, proveedor, concepto, subtotal, total

def generar_dataset(n=500, output_dir="data/xml"):
    os.makedirs(output_dir, exist_ok=True)
    uuids_generados = []
    anomalias = 0
    duplicados = 0

    for i in range(n):
        es_anomalo = random.random() < 0.03
        es_duplicado = len(uuids_generados) > 10 and random.random() < 0.02
        uuid_dup = random.choice(uuids_generados) if es_duplicado else None

        root, uuid, fecha, proveedor, concepto, subtotal, total = generar_cfdi(
            anomalo=es_anomalo,
            duplicado_de=uuid_dup
        )

        if not es_duplicado:
            uuids_generados.append(uuid)
        if es_anomalo:
            anomalias += 1
        if es_duplicado:
            duplicados += 1

        filename = f"{output_dir}/cfdi_{i+1:05d}_{uuid[:8]}.xml"
        tree = etree.ElementTree(root)
        tree.write(filename, pretty_print=True, xml_declaration=True, encoding="UTF-8")

    print(f"[Generator] {n} CFDIs generados en {output_dir}/")
    print(f"[Generator] Anomalías: {anomalias} | Duplicados: {duplicados}")

if __name__ == "__main__":
    generar_dataset(n=10000)