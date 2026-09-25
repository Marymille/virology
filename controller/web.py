import argparse
import json
import socket
import ssl
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from common.protocol import Message, validate_command
from common.tls import create_server_context, ensure_file

SIMULATED_CAPABILITIES = {
    "remote_shell": ("Shell distant", "T1059"),
    "credential_access": ("Accès aux identifiants", "T1003"),
    "persistence": ("Persistance", "T1547"),
    "av_evasion": ("Évasion antivirus", "T1027"),
    "keylogging": ("Keylogging", "T1056.001"),
    "rdp": ("Activation RDP", "T1021.001"),
    "phishing": ("Phishing", "T1566"),
    "lateral_movement": ("Propagation latérale", "T1021"),
    "privilege_escalation": ("Élévation de privilèges", "T1068"),
    "pass_the_hash": ("Pass-the-hash", "T1550.002"),
    "password_cracking": ("Cracking de mots de passe", "T1110"),
    "file_collection": ("Collecte de fichiers", "T1005"),
    "log_tampering": ("Modification de journaux", "T1070"),
    "syscall": ("Appel système", "T1106"),
    "whatever": ("Capacité créative de laboratoire", "LAB-CREATIVITY"),
}

WEB_PAGE = """<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>s0P0wn3d - laboratoire</title>
  <style>
    :root { color-scheme: light; font-family: Georgia, serif; background: #fff8f5; }
    body { max-width: 900px; margin: 40px auto; padding: 0 20px; color: #4f2942; background: #fff8f5; }
    h1 { margin-bottom: 4px; }
    h1, h2 { color: #a83d70; }
    .muted { color: #91617a; }
    .actions { display: flex; flex-wrap: wrap; gap: 10px; margin: 28px 0; }
    button { border: 1px solid #e5a9c5; border-radius: 999px; padding: 12px 16px; background: #f7c9dc; color: #662448; cursor: pointer; font: inherit; }
    button.danger { background: #d9789f; color: #fff8f5; }
    button:hover { background: #ee9fc0; }
    pre { min-height: 100px; padding: 16px; background: #fff0f5; border: 1px solid #edc4d5; border-radius: 14px; white-space: pre-wrap; }
    .command-tabs { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin: 18px 0 28px; }
    .command-tab { min-height: 52px; background: #fffaf0; border-color: #e7cda9; }
    .command-tab.active { background: #efacc8; box-shadow: 0 0 0 3px #f9dce8; }
    .simulation-note { padding: 14px 16px; background: #fffaf0; border-left: 4px solid #e5a9c5; border-radius: 8px; }
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
    <h2>Commandes du sujet</h2>
    <p class="simulation-note">Mode simulation : chaque onglet crée un événement synthétique et une alerte Blue Team. Aucune commande système n'est exécutée.</p>
    <div class="command-tabs" role="tablist" aria-label="Types de commandes">
        <button class="command-tab active" data-capability="keylogging">keylog</button>
        <button class="command-tab" data-capability="rdp">rdp</button>
        <button class="command-tab" data-capability="password_cracking">crack</button>
        <button class="command-tab" data-capability="pass_the_hash">pth</button>
        <button class="command-tab" data-capability="file_collection">loot</button>
        <button class="command-tab" data-capability="phishing">phish</button>
        <button class="command-tab" data-capability="lateral_movement">propagate</button>
        <button class="command-tab" data-capability="privilege_escalation">privesc</button>
        <button class="command-tab" data-capability="syscall">syscall</button>
        <button class="command-tab" data-capability="remote_shell">shell</button>
        <button class="command-tab" data-capability="whatever">whatever</button>
    </div>
    <button id="simulate-capability">Tester la commande sélectionnée</button>
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
        let selectedCapability = 'keylogging';
        document.querySelectorAll('.command-tab').forEach((tab) => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.command-tab').forEach((item) => item.classList.remove('active'));
                tab.classList.add('active');
                selectedCapability = tab.dataset.capability;
            });
        });
        document.querySelector('#simulate-capability').addEventListener('click', async () => {
            const capability = selectedCapability;
            const response = await fetch('/api/simulate?capability=' + encodeURIComponent(capability), { method: 'POST' });
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
        self.synthetic_alerts: list[dict[str, str]] = []
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
            alerts = [
                {"severity": "info", "rule": "LAB-C2-001", "message": "Agent de démonstration connecté"}
            ] if self.connection is not None else []
            return alerts + [dict(alert) for alert in self.synthetic_alerts]

    def simulate_capability(self, capability: str) -> dict[str, str]:
        if capability not in SIMULATED_CAPABILITIES:
            raise ValueError("capacité de simulation inconnue")
        with self.lock:
            if not self.enabled:
                self.record("simulation_blocked", capability)
                raise ConnectionError("laboratoire désactivé par le kill switch")
            label, technique = SIMULATED_CAPABILITIES[capability]
            self.record("synthetic_event", capability)
            alert = {
                "severity": "medium",
                "rule": f"LAB-SIM-{technique}",
                "message": f"Simulation : {label}",
                "technique": technique,
            }
            self.synthetic_alerts.append(alert)
            return {"capability": label, "technique": technique, "simulated": "true"}

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


def listen_for_agent(session: AgentSession, host: str, port: int, tls_context: ssl.SSLContext | None = None) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((host, port))
        listener.listen(5)
        print(f"Contrôleur agent en écoute sur {host}:{port}")
        while True:
            connection, _ = listener.accept()
            try:
                if tls_context is not None:
                    connection = tls_context.wrap_socket(connection, server_side=True)
                session.attach(connection)
            except (ConnectionError, OSError, ValueError, ssl.SSLError) as error:
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
            request = urlparse(self.path)
            if request.path == "/api/simulate":
                capability = parse_qs(request.query).get("capability", [""])[0]
                try:
                    body = json.dumps({"ok": True, "data": session.simulate_capability(capability)}).encode("utf-8")
                    self.send_response(200)
                except (ConnectionError, ValueError) as error:
                    body = json.dumps({"ok": False, "error": str(error)}).encode("utf-8")
                    self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if request.path != "/api/kill-switch":
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


def run_web_controller(
    agent_host: str,
    agent_port: int,
    web_host: str,
    web_port: int,
    cert_file: str | None = None,
    key_file: str | None = None,
) -> None:
    session = AgentSession()
    tls_context = create_server_context(cert_file, key_file) if cert_file and key_file else None
    listener = threading.Thread(
        target=listen_for_agent,
        args=(session, agent_host, agent_port, tls_context),
        daemon=True,
    )
    listener.start()
    server = ThreadingHTTPServer((web_host, web_port), make_handler(session))
    scheme = "http"
    if tls_context is not None:
        server.socket = tls_context.wrap_socket(server.socket, server_side=True)
        scheme = "https"
    print(f"Interface web disponible sur {scheme}://{web_host}:{web_port}")
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interface web locale du démonstrateur")
    parser.add_argument("--agent-host", default="127.0.0.1")
    parser.add_argument("--agent-port", type=int, default=8765)
    parser.add_argument("--web-host", default="127.0.0.1")
    parser.add_argument("--web-port", type=int, default=8080)
    parser.add_argument("--tls", action="store_true", help="active TLS pour l'agent et l'interface")
    parser.add_argument("--cert-file", default="certs/lab-cert.pem")
    parser.add_argument("--key-file", default="certs/lab-key.pem")
    args = parser.parse_args()
    if args.tls:
        ensure_file(args.cert_file)
        ensure_file(args.key_file)
    run_web_controller(
        args.agent_host,
        args.agent_port,
        args.web_host,
        args.web_port,
        args.cert_file if args.tls else None,
        args.key_file if args.tls else None,
    )