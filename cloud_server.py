import os
import json
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from http.server import SimpleHTTPRequestHandler, HTTPServer

PORT = int(os.environ.get("PORT", 10000))
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")

# CÓDIGO DE SEGURIDAD MILITAR PARA DESACTIVAR LA SIRENA
CLAVE_DESACTIVACION = "1928"

# Estado central de la alerta en la nube
state = {
    "alertActive": False,
    "alertLevel": "NONE",
    "alertMessage": "",
    "activatedBy": None,
    "activatedAt": None,
    "sector": None
}

# Historial / Libro de registro militar en memoria
historial_alertas = []

class CloudAlertHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        # 1. Consultar estado actual (llamado continuo por tablets/celulares)
        if path == '/api/state':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            data = {**state, "historial": historial_alertas[:15]}
            self.wfile.write(json.dumps(data).encode('utf-8'))
            return

        # 2. Disparar alerta con registro de operador
        elif path == '/api/trigger':
            operador = qs.get("operador", ["GUARDIA DE PREVENCION"])[0]
            sector = qs.get("sector", ["PERIMETRO NORTE"])[0]
            hora_actual = datetime.now().strftime("%H:%M:%S - %d/%m/%Y")

            state["alertActive"] = True
            state["alertLevel"] = "RED"
            state["alertMessage"] = f"¡AMENAZA DE DRON DETECTADA EN {sector}!"
            state["activatedBy"] = operador
            state["activatedAt"] = hora_actual
            state["sector"] = sector

            # Agregar al libro de registro militar
            registro = {
                "id": len(historial_alertas) + 1,
                "operador": operador,
                "sector": sector,
                "hora": hora_actual,
                "estado": "ACTIVA"
            }
            historial_alertas.insert(0, registro)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "state": state}).encode('utf-8'))
            return

        # 3. Desactivar alarma (EXIGE CÓDIGO MILITAR DE SEGURIDAD)
        elif path == '/api/clear':
            codigo_ingresado = qs.get("codigo", [""])[0]
            operador_cancela = qs.get("operador", ["OFICIAL DE GUARDIA"])[0]

            if codigo_ingresado != CLAVE_DESACTIVACION:
                self.send_response(403)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": "CÓDIGO DE DESACTIVACIÓN INCORRECTO"}).encode('utf-8'))
                return

            hora_despeje = datetime.now().strftime("%H:%M:%S - %d/%m/%Y")
            state["alertActive"] = False
            state["alertLevel"] = "NONE"
            state["alertMessage"] = ""
            state["activatedBy"] = None
            state["activatedAt"] = None
            state["sector"] = None

            if historial_alertas:
                historial_alertas[0]["estado"] = f"DESPEJADA ({hora_despeje}) por {operador_cancela}"

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "state": state}).encode('utf-8'))
            return

        # Redirigir la raíz a la pantalla táctica
        if path == '/' or path == '':
            self.send_response(302)
            self.send_header('Location', '/sismo_drones.html')
            self.end_headers()
            return

        super().do_GET()

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

if __name__ == '__main__':
    print(f"Servidor militar con clave táctica activo en puerto {PORT}...")
    server = HTTPServer(("0.0.0.0", PORT), CloudAlertHandler)
    server.serve_forever()
