import os
import json
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, HTTPServer

PORT = int(os.environ.get("PORT", 10000))
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")

# Estado global en memoria para la alerta en la nube
state = {
    "alertActive": False,
    "alertLevel": "NONE",
    "alertMessage": "",
    "activatedBy": None,
    "activatedAt": None
}

class CloudAlertHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def log_message(self, format, *args):
        # Silenciar logs ruidosos de polling
        pass

    def do_GET(self):
        # 1. Endpoint para consultar el estado (llamado cada 600ms por tablets/celulares)
        if self.path == '/api/state':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            self.wfile.write(json.dumps(state).encode('utf-8'))
            return

        # 2. Endpoint para activar la alarma (cuando alguien presiona el botón rojo)
        elif self.path.startswith('/api/trigger'):
            state["alertActive"] = True
            state["alertLevel"] = "RED"
            state["alertMessage"] = "¡AMENAZA DE DRON DETECTADA EN EL CANTÓN!"
            state["activatedBy"] = "MY. JULIAN CAMILO MERCHAN GARIBELLO"
            state["activatedAt"] = datetime.now().isoformat()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "state": state}).encode('utf-8'))
            return

        # 3. Endpoint para cancelar la alarma (silenciar en todos los dispositivos)
        elif self.path.startswith('/api/clear'):
            state["alertActive"] = False
            state["alertLevel"] = "NONE"
            state["alertMessage"] = ""
            state["activatedBy"] = None
            state["activatedAt"] = None
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "state": state}).encode('utf-8'))
            return

        # Redirigir la raíz a la pantalla de sismo/drones
        if self.path == '/' or self.path == '':
            self.send_response(302)
            self.send_header('Location', '/sismo_drones.html')
            self.end_headers()
            return

        # Servir archivos estáticos normales (HTML, JS, CSS)
        super().do_GET()

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

if __name__ == '__main__':
    print(f"Iniciando servidor de nube en puerto {PORT}...")
    server = HTTPServer(("0.0.0.0", PORT), CloudAlertHandler)
    server.serve_forever()
