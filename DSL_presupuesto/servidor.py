import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from proye1 import compilar


BASE_DIR = Path(__file__).resolve().parent


class PresupuestoHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def do_POST(self):
        if self.path != "/compilar":
            self.send_error(404, "Ruta no encontrada")
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            programa = data.get("programa", "")
            analisis, tabla_simbolos = compilar(programa)
            self.enviar_json(self.formatear_respuesta(programa, analisis, tabla_simbolos))
        except Exception as exc:
            self.enviar_json({"error": str(exc)}, status=400)

    def formatear_respuesta(self, programa, analisis, tabla_simbolos):
        lineas_programa = [
            linea.strip()
            for linea in programa.strip().splitlines()
            if linea.strip()
        ]

        gastos = [
            {
                "nombre": nombre,
                "categoria": datos["categoria"],
                "valor": datos["valor"],
            }
            for nombre, datos in tabla_simbolos["GASTOS"].items()
        ]

        ingreso = tabla_simbolos["INGRESO_MENSUAL"] or 0
        total_gastos = tabla_simbolos["GASTO_TOTAL"] or sum(tabla_simbolos["TOTALES"].values())
        saldo = tabla_simbolos["SALDO_FINAL"]

        if saldo is None:
            saldo = ingreso - total_gastos

        return {
            "programa": lineas_programa,
            "analisis": analisis,
            "tabla_simbolos": tabla_simbolos,
            "gastos": gastos,
            "resumen": {
                "ingreso_mensual": ingreso,
                "total_gastos": total_gastos,
                "saldo_final": saldo,
                "estado": "ERROR" if any(item["estado"] == "ERROR" for item in analisis) else "OK",
            },
        }

    def enviar_json(self, data, status=200):
        contenido = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(contenido)))
        self.end_headers()
        self.wfile.write(contenido)


def main():
    puerto = 8000
    servidor = ThreadingHTTPServer(("localhost", puerto), PresupuestoHandler)
    print(f"Servidor iniciado en http://localhost:{puerto}")
    print("Presiona Ctrl+C para detenerlo.")
    servidor.serve_forever()


if __name__ == "__main__":
    main()
