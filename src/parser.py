import os
from lxml import etree
from datetime import datetime

NS = "http://www.sat.gob.mx/cfd/4"
TFD_NS = "http://www.sat.gob.mx/TimbreFiscalDigital"

def parsear_cfdi(filepath: str) -> dict:
    try:
        tree = etree.parse(filepath)
        root = tree.getroot()

        comprobante = {
            "archivo": os.path.basename(filepath),
            "version": root.get("Version"),
            "serie": root.get("Serie"),
            "folio": root.get("Folio"),
            "fecha": root.get("Fecha"),
            "subtotal": float(root.get("SubTotal", 0)),
            "total": float(root.get("Total", 0)),
            "tipo_comprobante": root.get("TipoDeComprobante"),
            "metodo_pago": root.get("MetodoPago"),
            "forma_pago": root.get("FormaPago"),
            "moneda": root.get("Moneda", "MXN"),
        }

        emisor = root.find(f"{{{NS}}}Emisor")
        if emisor is not None:
            comprobante["emisor_rfc"] = emisor.get("Rfc")
            comprobante["emisor_nombre"] = emisor.get("Nombre")
            comprobante["emisor_regimen"] = emisor.get("RegimenFiscal")

        receptor = root.find(f"{{{NS}}}Receptor")
        if receptor is not None:
            comprobante["receptor_rfc"] = receptor.get("Rfc")
            comprobante["receptor_nombre"] = receptor.get("Nombre")
            comprobante["receptor_uso_cfdi"] = receptor.get("UsoCFDI")

        conceptos = root.findall(f"{{{NS}}}Conceptos/{{{NS}}}Concepto")
        if conceptos:
            primer_concepto = conceptos[0]
            comprobante["concepto_descripcion"] = primer_concepto.get("Descripcion")
            comprobante["concepto_clave"] = primer_concepto.get("ClaveProdServ")
            comprobante["concepto_cantidad"] = float(primer_concepto.get("Cantidad", 1))
            comprobante["concepto_importe"] = float(primer_concepto.get("Importe", 0))

        impuestos = root.find(f"{{{NS}}}Impuestos")
        if impuestos is not None:
            comprobante["total_impuestos"] = float(
                impuestos.get("TotalImpuestosTrasladados", 0)
            )

        complemento = root.find(f"{{{NS}}}Complemento")
        if complemento is not None:
            tfd = complemento.find(f"{{{TFD_NS}}}TimbreFiscalDigital")
            if tfd is not None:
                comprobante["uuid"] = tfd.get("UUID")
                comprobante["fecha_timbrado"] = tfd.get("FechaTimbrado")
                comprobante["no_certificado_sat"] = tfd.get("NoCertificadoSAT")

        return comprobante

    except Exception as e:
        print(f"[Parser] Error en {filepath}: {e}")
        return None

def parsear_directorio(directorio: str = "data/xml") -> list:
    resultados = []
    archivos = [f for f in os.listdir(directorio) if f.endswith(".xml")]
    
    for archivo in archivos:
        ruta = os.path.join(directorio, archivo)
        datos = parsear_cfdi(ruta)
        if datos:
            resultados.append(datos)

    print(f"[Parser] {len(resultados)} CFDIs parseados de {len(archivos)} archivos")
    return resultados

if __name__ == "__main__":
    datos = parsear_directorio()
    if datos:
        print("\nEjemplo del primer CFDI parseado:")
        for k, v in list(datos[0].items())[:8]:
            print(f"  {k}: {v}")