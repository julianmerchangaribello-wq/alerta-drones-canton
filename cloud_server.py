import os
import json
import base64
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from http.server import SimpleHTTPRequestHandler, HTTPServer

try:
    from pywebpush import webpush, WebPushException
    HAS_WEBPUSH = True
except ImportError:
    HAS_WEBPUSH = False

PORT = int(os.environ.get("PORT", 10000))
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
VAPID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vapid_keys.json")
SUBS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "push_subscriptions.json")

CLAVE_DESACTIVACION = "1928"

# Cargar claves VAPID
vapid_keys = {}
if os.path.exists(VAPID_FILE):
    with open(VAPID_FILE, "r") as f:
        vapid_keys = json.load(f)

# Cargar suscripciones de tablets/celulares registrados para despertar en bloqueo
push_subscriptions = []
if os.path.exists(SUBS_FILE):
    try:
        with open(SUBS_FILE, "r") as f:
            push_subscriptions = json.load(f)
    except Exception:
        pass

def save_subs():
    with open(SUBS_FILE, "w") as f:
        json.dump(push_subscriptions, f)

def notify_all_push_devices(title, body):
    if not HAS_WEBPUSH or not vapid_keys:
        return
    
    payload = json.dumps({
        "title": title,
        "body": body,
        "url": "/sismo_drones.html"
    })
    
    dead_subs = []
    for sub in push_subscriptions:
        try:
            webpush(
                subscription_info=sub,
                data=payload,
                vapid_private_key=vapid_keys["private_pem"],
                vapid_claims={"sub": "mailto:comandancia@cantonmilitar.ec"}
            )
        except WebPushException as ex:
            if ex.response and ex.response.status_code in (404, 410):
                dead_subs.append(sub)
        except Exception:
            pass
            
    if dead_subs:
        for ds in dead_subs:
            if ds in push_subscriptions:
                push_subscriptions.remove(ds)
        save_subs()

state = {
    "alertActive": False,
    "alertLevel": "NONE",
    "alertMessage": "",
    "activatedBy": None,
    "activatedAt": None,
    "sector": None
}

historial_alertas = []

class CloudAlertHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def log_message(self, format, *args):
        pass

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/subscribe_push':
            length = int(self.headers.get('content-length', 0))
            if length:
                body = self.rfile.read(length).decode('utf-8')
                try:
                    sub_data = json.loads(body)
                    if sub_data not in push_subscriptions:
                        push_subscriptions.append(sub_data)
                        save_subs()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({"ok": True}).encode('utf-8'))
                    return
                except Exception:
                    pass
        self.send_response(400)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == '/api/vapid_key':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"publicKey": vapid_keys.get("public_key", "")}).encode('utf-8'))
            return

        elif path == '/api/state':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            data = {**state, "historial": historial_alertas[:15]}
            self.wfile.write(json.dumps(data).encode('utf-8'))
            return

        elif path == '/api/trigger':
            operador = qs.get("operador", ["GUARDIA DE PREVENCIÓN"])[0]
            sector = qs.get("sector", ["PERÍMETRO GENERAL"])[0]
            hora_actual = datetime.now().strftime("%H:%M:%S - %d/%m/%Y")

            state["alertActive"] = True
            state["alertLevel"] = "RED"
            state["alertMessage"] = f"¡AMENAZA DE DRON DETECTADA EN {sector}!"
            state["activatedBy"] = operador
            state["activatedAt"] = hora_actual
            state["sector"] = sector

            registro = {
                "id": len(historial_alertas) + 1,
                "operador": operador,
                "sector": sector,
                "hora": hora_actual,
                "estado": "ACTIVA"
            }
            historial_alertas.insert(0, registro)

            # DISPARAR PUSH NOTIFICATION DE ALTA PRIORIDAD QUE DESPIERTA PANTALLA
            notify_all_push_devices(
                title=f"🚨 ¡ATAQUE DE DRON! - {operador}",
                body="¡BUSCAR CUBIERTA INMEDIATA! SIRENA MILITAR ACTIVA"
            )

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "state": state}).encode('utf-8'))
            return

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
    print(f"Servidor militar con WebPush 24/7 activo en puerto {PORT}...")
    server = HTTPServer(("0.0.0.0", PORT), CloudAlertHandler)
    server.serve_forever()
