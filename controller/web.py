import argparse
import json
import socket
import threading
from datetime import datetime, timezone
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
    body { max-width: 900px; margin: 40px auto; padding: 0 20px; color: #17202a; }
    h1 { margin-bottom: 4px; }
    .muted { color: #5f6b76; }
    .actions { display: flex; flex-wrap: wrap; gap: 10px; margin: 28px 0; }
    button { border: 0; border-radius: 6px; padding: 12px 16px; background: #166534; color: white; cursor: pointer; }
    button.danger { background: #b91c1c; }
    button:hover { background: #14532d; }
    pre { min-height: 100px; padding: 16px; background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; white-space: pre-wrap; }
  </style>
</head>
<body>
  <h1>s0P0wn3d</h1>
    <p class="muted">Tableau de bord de simulation pour laboratoire local.</p>
    <p id="connection" class="muted">Agent : vérification...</p>
    <p id="lab-state" class="muted">Laboratoire : vérification...</p>
  <div class="actions">
    <button data-command="status">Etat</button>
    <button data-command="heartbeat">Heartbeat</button>
    <button data-command="get_demo_log">Journal de demo</button>
        <button class="danger" id="kill-switch">Désactivation globale</button>
  </div>
  <pre id="result">En attente d'une commande.</pre>
    <h2>Agents fictifs</h2>
    <pre id="agents">Chargement...</pre>
    <h2>Alertes synthétiques</h2>
    <pre id="alerts">Aucune alerte.</pre>
    <h2>Journal d'audit</h2>
    <pre id="audit">Aucun événement.</pre>
    <h2>Documentation</h2>
    <p class="muted">Ce laboratoire simule un contrôleur C2 sans exécuter de commande système, sans collecte de secrets et sans contact externe. Les agents fictifs et les alertes servent uniquement à l'analyse Blue Team.</p>
  <script>
    const result = document.querySelector('#result');
        const connection = document.querySelector('#connection');
        const labState = document.querySelector('#lab-state');
        const agents = document.querySelector('#agents');
        const alerts = document.querySelector('#alerts');
        const audit = document.querySelector('#audit');
        async function refreshState() {
            const [stateResponse, agentsResponse, alertsResponse, auditResponse] = await Promise.all([
                fetch('/api/state'), fetch('/api/agents'), fetch('/api/alerts'), fetch('/api/audit')
            ]);
            const state = await stateResponse.json();
            connection.textContent = 'Agent : ' + (state.connected ? 'connecté' : 'déconnecté');
            labState.textContent = 'Laboratoire : ' + (state.enabled ? 'actif' : 'désactivé');
            agents.textContent = JSON.stringify(await agentsResponse.json(), null, 2);
            alerts.textContent = JSON.stringify(await alertsResponse.json(), null, 2);
            audit.textContent = JSON.stringify(await auditResponse.json(), null, 2);
        }
    document.querySelectorAll('button').forEach((button) => {
            if (!button.dataset.command) return;
      button.addEventListener('click', async () => {
        result.textContent = 'Commande en cours...';
        const response = await fetch('/api/command?command=' + encodeURIComponent(button.dataset.command));
        result.textContent = JSON.stringify(await response.json(), null, 2);
                await refreshState();
      });
    });
        document.querySelector('#kill-switch').addEventListener('click', async () => {
            const response = await fetch('/api/kill-switch', { method: 'POST' });
            result.textContent = JSON.stringify(await response.json(), null, 2);
            await refreshState();
        });
        refreshState();
  </script>
</body>
</html>"""


class AgentSession:
    def __init__(self) -> None:
        self.connection: socket.socket | None = None
        self.reader = None
        self.lock = threading.Lock()
        self.history: list[dict[str, str]] = []
        self.audit_log: tuple[dict[str, str], ...] = ()
        self.enabled = True
        self.agents = [
            {"id": "demo-agent", "kind": "connected", "status": "offline"},
            {"id": "sim-agent-01", "kind": "synthetic", "status": "simulated"},
            {"id": "sim-agent-02", "kind": "synthetic", "status": "simulated"},
        ]

    def record(self, action: str, detail: str) -> None:
        event = {"time": datetime.now(timezone.utc).isoformat(), "action": action, "detail": detail}
        self.audit_log = self.audit_log + (event,)

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
            self.agents[0]["status"] = "online"
            self.record("agent_connected", hello.agent_id)
        print("Agent connecté pour le tableau de bord")

    def execute(self, command: str) -> dict:
        if not validate_command(command):
            raise ValueError("commande refusée")
        with self.lock:
            if not self.enabled:
                self.record("command_blocked", command)
                raise ConnectionError("laboratoire désactivé par le kill switch")
            if self.connection is None or self.reader is None:
                raise ConnectionError("aucun agent connecté")
            self.connection.sendall((command + "\n").encode("utf-8"))
            raw_response = self.reader.readline()
            if not raw_response:
                raise ConnectionError("agent déconnecté")
            payload = Message.decode(raw_response).payload
            self.history.append({"time": datetime.now(timezone.utc).isoformat(), "command": command})
            self.record("command_executed", command)
            return payload

    def state(self) -> dict[str, object]:
        with self.lock:
            return {"connected": self.connection is not None, "enabled": self.enabled, "history": list(self.history)}

    def get_agents(self) -> list[dict[str, str]]:
        with self.lock:
            return [dict(agent) for agent in self.agents]

    def get_alerts(self) -> list[dict[str, str]]:
        with self.lock:
            return [
                {"severity": "info", "rule": "LAB-C2-001", "message": "Agent de démonstration connecté"}
            ] if self.connection is not None else []

    def get_audit(self) -> list[dict[str, str]]:
        with self.lock:
            return [dict(event) for event in self.audit_log]

    def kill_switch(self) -> None:
        with self.lock:
            self.enabled = False
            if self.connection is not None:
                self.connection.close()
                self.connection = None
                self.reader = None
            self.agents[0]["status"] = "offline"
            self.record("kill_switch", "global laboratory shutdown")


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
            elif request.path == "/api/state":
                body = json.dumps(session.state()).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
            elif request.path == "/api/agents":
                body = json.dumps(session.get_agents()).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
            elif request.path == "/api/alerts":
                body = json.dumps(session.get_alerts()).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
            elif request.path == "/api/audit":
                body = json.dumps(session.get_audit()).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
            else:
                self.send_error(404)
                return
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:
            if urlparse(self.path).path != "/api/kill-switch":
                self.send_error(404)
                return
            session.kill_switch()
            body = json.dumps({"ok": True, "message": "laboratoire désactivé"}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
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