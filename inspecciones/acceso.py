"""Acceso de inspectores: conserva las cuentas de la aplicación de origen."""
import hashlib
import hmac

USUARIOS_SISTEMA = {'jnavarrete': {'rol': 'operador', 'nombre': 'jnavarrete (Agregar Datos)'}, 'jhernandez': {'rol': 'inspector', 'nombre': 'Jorge Hernández'}, 'hcastillo': {'rol': 'inspector', 'nombre': 'Harold Castillo'}, 'mchirinos': {'rol': 'inspector', 'nombre': 'Miguel Chirinos'}, 'asarmiento': {'rol': 'inspector', 'nombre': 'Arlem Sarmiento'}}
_HASHES = {'jnavarrete': {'salt': '08ea4d7999ae18b9fcf71c0a9f4c3663', 'digest': '4ad082ffc26b0079b2c34a6d0a2023483b4092a62d57428fe5bcb0afeedd771c'}, 'jhernandez': {'salt': 'b0c809e3f5cc0db97c8f46e0b70a5129', 'digest': '28df73b02ad5584a888c306e4fed5a60ae969dd2e017149570bed8814be44396'}, 'hcastillo': {'salt': '35409522acb6aa6bfb5b363de3efc02c', 'digest': '0f779999e5d8646820fe21fab730c64dc2b566ededc3cb80acbd00c29cffb6c8'}, 'mchirinos': {'salt': 'edbd78071a6692a97588505701ccbcb2', 'digest': '074706bff02f92658f056715931df7595e65eb01ef93447a91a5d95199bfdbc9'}, 'asarmiento': {'salt': '8fbd69070983352b0008b6f3153e843f', 'digest': '169bb050ad2749f8048fb7fda09285538249aa783f5618c9f79420acca6d0820'}}

def validar_usuario(usuario, password):
    entry = _HASHES.get(usuario)
    if entry is None:
        return False
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(entry['salt']), 600000).hex()
    return hmac.compare_digest(digest, entry['digest'])
