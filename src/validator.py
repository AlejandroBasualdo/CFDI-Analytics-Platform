import re
from datetime import datetime

REGIMENES_FISCALES_VALIDOS = {
    "601", "603", "605", "606", "607", "608", "610", "611", "612",
    "614", "616", "620", "621", "622", "623", "624", "625", "626"
}

USOS_CFDI_VALIDOS = {
    "G01", "G02", "G03", "I01", "I02", "I03", "I04", "I05", "I06",
    "I07", "I08", "D01", "D02", "D03", "D04", "D05", "D06", "D07",
    "D08", "D09", "D10", "S01", "CP01", "CN01"
}

METODOS_PAGO_VALIDOS = {"PUE", "PPD"}

FORMAS_PAGO_VALIDAS = {
    "01", "02", "03", "04", "05", "06", "08", "12", "13", "14",
    "15", "17", "23", "24", "25", "26", "27", "28", "29", "30", "31", "99"
}

def validar_rfc(rfc: str) -> tuple:
    if not rfc:
        return False, "RFC vacío"
    rfc = rfc.strip().upper()
    patron_moral = r"^[A-ZÑ&]{3}\d{6}[A-Z0-9]{3}$"
    patron_fisica = r"^[A-ZÑ&]{4}\d{6}[A-Z0-9]{3}$"
    if re.match(patron_moral, rfc) or re.match(patron_fisica, rfc):
        return True, "RFC válido"
    return False, f"RFC con formato inválido: {rfc}"

def validar_fecha(fecha_str: str) -> tuple:
    if not fecha_str:
        return False, "Fecha vacía"
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%dT%H:%M:%S")
        ahora = datetime.now()
        if fecha > ahora:
            return False, f"Fecha futura no permitida: {fecha_str}"
        limite = datetime(2022, 1, 1)
        if fecha < limite:
            return False, f"Fecha fuera del periodo fiscal analizado: {fecha_str}"
        return True, "Fecha válida"
    except ValueError:
        return False, f"Formato de fecha inválido: {fecha_str}"

def validar_montos(subtotal: float, total: float, impuestos: float) -> tuple:
    if subtotal <= 0:
        return False, "Subtotal debe ser mayor a cero"
    if total <= 0:
        return False, "Total debe ser mayor a cero"
    iva_esperado = round(subtotal * 0.16, 2)
    total_esperado = round(subtotal + iva_esperado, 2)
    diferencia = abs(total - total_esperado)
    if diferencia > 1.0:
        return False, f"Total no cuadra: esperado {total_esperado}, recibido {total}"
    return True, "Montos válidos"

def validar_uso_cfdi(uso: str) -> tuple:
    if not uso:
        return False, "Uso CFDI vacío"
    if uso in USOS_CFDI_VALIDOS:
        return True, "Uso CFDI válido"
    return False, f"Uso CFDI no reconocido: {uso}"

def validar_regimen_fiscal(regimen: str) -> tuple:
    if not regimen:
        return False, "Régimen fiscal vacío"
    if regimen in REGIMENES_FISCALES_VALIDOS:
        return True, "Régimen fiscal válido"
    return False, f"Régimen fiscal no reconocido: {regimen}"

def validar_uuid(uuid: str) -> tuple:
    if not uuid:
        return False, "UUID vacío — factura sin timbre fiscal"
    patron = r"^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$"
    if re.match(patron, uuid.upper()):
        return True, "UUID válido"
    return False, f"UUID con formato inválido: {uuid}"

def validar_metodo_pago(metodo: str) -> tuple:
    if not metodo:
        return False, "Método de pago vacío"
    if metodo in METODOS_PAGO_VALIDOS:
        return True, "Método de pago válido"
    return False, f"Método de pago no reconocido: {metodo}"

def validar_forma_pago(forma: str) -> tuple:
    if not forma:
        return False, "Forma de pago vacía"
    if forma in FORMAS_PAGO_VALIDAS:
        return True, "Forma de pago válida"
    return False, f"Forma de pago no reconocida: {forma}"

def validar_cfdi(cfdi: dict) -> dict:
    resultados = []
    errores = []

    reglas = [
        ("RFC Emisor", validar_rfc(cfdi.get("emisor_rfc", ""))),
        ("RFC Receptor", validar_rfc(cfdi.get("receptor_rfc", ""))),
        ("Fecha emisión", validar_fecha(cfdi.get("fecha", ""))),
        ("Montos e IVA", validar_montos(
            cfdi.get("subtotal", 0),
            cfdi.get("total", 0),
            cfdi.get("total_impuestos", 0)
        )),
        ("Uso CFDI", validar_uso_cfdi(cfdi.get("receptor_uso_cfdi", ""))),
        ("Régimen fiscal", validar_regimen_fiscal(cfdi.get("emisor_regimen", ""))),
        ("UUID / Timbre", validar_uuid(cfdi.get("uuid", ""))),
        ("Método de pago", validar_metodo_pago(cfdi.get("metodo_pago", ""))),
        ("Forma de pago", validar_forma_pago(cfdi.get("forma_pago", ""))),
    ]

    for nombre, (valido, mensaje) in reglas:
        resultados.append({
            "regla": nombre,
            "valido": valido,
            "mensaje": mensaje
        })
        if not valido:
            errores.append(f"{nombre}: {mensaje}")

    es_valido = all(r["valido"] for r in resultados)

    return {
        "uuid": cfdi.get("uuid"),
        "archivo": cfdi.get("archivo"),
        "es_valido": es_valido,
        "total_reglas": len(reglas),
        "reglas_aprobadas": sum(1 for r in resultados if r["valido"]),
        "errores": errores,
        "detalle": resultados
    }

if __name__ == "__main__":
    from src.parser import parsear_directorio
    cfdis = parsear_directorio()
    validos = 0
    invalidos = 0
    for cfdi in cfdis[:10]:
        resultado = validar_cfdi(cfdi)
        status = "VÁLIDO" if resultado["es_valido"] else "INVÁLIDO"
        print(f"{status} — {resultado['archivo']} — Errores: {resultado['errores']}")
        if resultado["es_valido"]:
            validos += 1
        else:
            invalidos += 1
    print(f"\nResumen: {validos} válidos, {invalidos} inválidos de 10 revisados")