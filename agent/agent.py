import argparse
import socket

from common.protocol import Message, validate_command

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


def run_agent(host: str, port: int) -> None:
    with socket.create_connection((host, port), timeout=10) as connection:
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
    args = parser.parse_args()
    run_agent(args.host, args.port)