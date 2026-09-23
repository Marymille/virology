import argparse
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from common.protocol import Message, validate_command

WEB_PAGE = """<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>s0P0wn3d - laboratoire</title>
  <style>
    :root { color-scheme: light; font-family: system-ui, sans-serif; }
    body { max-width: 760px; margin: 40px auto; padding: 0 20px; color: #17202a; }
    h1 { margin-bottom: 4px; }
    .muted { color: #5f6b76; }
    .actions { display: flex; flex-wrap: wrap; gap: 10px; margin: 28px 0; }
    button { border: 0; border-radius: 6px; padding: 12px 16px; background: #166534; color: white; cursor: pointer; }
    button:hover { background: #14532d; }
    pre { min-height: 100px; padding: 16px; background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; white-space: pre-wrap; }
  </style>
</head>
<body>
  <h1>s0P0wn3d</h1>
  <p class="muted">Tableau de bord de simulation pour laboratoire local.</p>
  <div class="actions">
    <button data-command="status">Etat</button>
    <button data-command="heartbeat">Heartbeat</button>
    <button data-command="get_demo_log">Journal de demo</button>
  </div>
  <pre id="result">En attente d'une commande.</pre>
  <script>
    const result = document.querySelector('#result');
    document.querySelectorAll('button').forEach((button) => {
      button.addEventListener('click', async () => {
        result.textContent = 'Commande en cours...';
        const response = await fetch('/api/command?command=' + encodeURIComponent(button.dataset.command));
        result.textContent = JSON.stringify(await response.json(), null, 2);
      });
    });
  </script>
</body>
</html>"""


class AgentSession:
    def __init__(self) -> None:
        self.connection: socket.socket | None = None
        self.reader = None
        self.lock = threading.Lock()

    def attach(self, connection: socket.socket) -> None:
        reader = connection.makefile("rb")
        raw_hello = reader.readline()
        hello = Message.decode(raw_hello)
        if hello.kind != "hello":
            reader.close()
            connection.close()
            raise ValueError("message d'accueil inattendu")
        with self.lock:
            if self.connection is not None:
                self.connection.close()
            self.connection = connection
            self.reader = reader
        print("Agent connecté pour le tableau de bord")

    def execute(self, command: str) -> dict:
        if not validate_command(command):
            raise ValueError("commande refusée")
        with self.lock:
            if self.connection is None or self.reader is None:
                raise ConnectionError("aucun agent connecté")
            self.connection.sendall((command + "\n").encode("utf-8"))
            raw_response = self.reader.readline()
            if not raw_response:
                raise ConnectionError("agent déconnecté")
            return Message.decode(raw_response).payload


def listen_for_agent(session: AgentSession, host: str, port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((host, port))
        listener.listen(5)
        print(f"Contrôleur agent en écoute sur {host}:{port}")
        while True:
            connection, _ = listener.accept()
            try:
                session.attach(connection)
            except (ConnectionError, OSError, ValueError) as error:
                print(f"Connexion refusée: {error}")


def make_handler(session: AgentSession) -> type[BaseHTTPRequestHandler]:
    class DashboardHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            request = urlparse(self.path)
            if request.path == "/":
                body = WEB_PAGE.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
            elif request.path == "/api/command":
                command = parse_qs(request.query).get("command", [""])[0]
                try:
                    body = json.dumps({"ok": True, "data": session.execute(command)}).encode("utf-8")
                    self.send_response(200)
                except (ConnectionError, ValueError) as error:
                    body = json.dumps({"ok": False, "error": str(error)}).encode("utf-8")
                    self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
            else:
                self.send_error(404)
                return
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    return DashboardHandler


def run_web_controller(agent_host: str, agent_port: int, web_host: str, web_port: int) -> None:
    session = AgentSession()
    listener = threading.Thread(target=listen_for_agent, args=(session, agent_host, agent_port), daemon=True)
    listener.start()
    server = ThreadingHTTPServer((web_host, web_port), make_handler(session))
    print(f"Interface web disponible sur http://{web_host}:{web_port}")
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interface web locale du démonstrateur")
    parser.add_argument("--agent-port", type=int, default=8765)
    parser.add_argument("--web-port", type=int, default=8080)
    args = parser.parse_args()
    run_web_controller("127.0.0.1", args.agent_port, "127.0.0.1", args.web_port)