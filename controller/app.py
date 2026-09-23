import argparse
import socket

from common.protocol import Message, validate_command


def run_controller(command: str, host: str, port: int) -> None:
	if not validate_command(command):
		raise ValueError(f"Commande refusée: {command}")

	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
		server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		server.bind((host, port))
		server.listen(1)
		print(f"Contrôleur en écoute sur {host}:{port}")
		connection, address = server.accept()
		with connection:
			print(f"Agent connecté: {address[0]}:{address[1]}")
			reader = connection.makefile("rb")
			raw_hello = reader.readline()
			if not raw_hello:
				raise ConnectionError("l'agent a fermé la connexion sans message d'accueil")
			hello = Message.decode(raw_hello)
			if hello.kind != "hello":
				raise ValueError("message d'accueil inattendu")
			connection.sendall((command + "\n").encode("utf-8"))
			raw_response = reader.readline()
			if not raw_response:
				raise ConnectionError("l'agent a fermé la connexion sans réponse")
			response = Message.decode(raw_response)
			print(response.payload)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Contrôleur local de démonstration")
	parser.add_argument("command", choices=("status", "heartbeat", "get_demo_log"))
	parser.add_argument("--host", default="127.0.0.1")
	parser.add_argument("--port", type=int, default=8765)
	args = parser.parse_args()
	run_controller(args.command, args.host, args.port)
