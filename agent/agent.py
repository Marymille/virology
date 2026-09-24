import argparse
import socket
import ssl

from common.protocol import Message, validate_command
from common.tls import create_lab_client_context, ensure_file

def handle_command(command: str) -> Message:
    if not validate_command(command):
        return Message("error", "demo-agent", {"reason": "command refused"})

    if command == "status":
        payload = {"state": "running", "mode": "simulation"}
    elif command == "heartbeat":
        payload = {"alive": True}
    else:
        payload = {"events": ["DEMO_CREDENTIAL_ACCESS", "DEMO_PERSISTENCE"]}

    return Message("result", "demo-agent", payload)


def run_agent(host: str, port: int, ca_file: str | None = None) -> None:
    raw_connection = socket.create_connection((host, port), timeout=10)
    context = create_lab_client_context(ca_file) if ca_file else None
    connection = context.wrap_socket(raw_connection, server_hostname="localhost") if context else raw_connection
    with connection:
        connection.sendall(Message("hello", "demo-agent", {"mode": "simulation"}).encode())
        connection.settimeout(None)
        reader = connection.makefile("rb")
        for raw_command in reader:
            command = raw_command.decode("utf-8").strip()
            if command:
                connection.sendall(handle_command(command).encode())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agent de démonstration sans shell arbitraire")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--tls", action="store_true", help="active TLS pour le laboratoire")
    parser.add_argument("--ca-file", default="certs/lab-cert.pem")
    args = parser.parse_args()
    if args.tls:
        ensure_file(args.ca_file)
    run_agent(args.host, args.port, args.ca_file if args.tls else None)