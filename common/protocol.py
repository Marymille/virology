from dataclasses import asdict, dataclass
import json

ALLOWED_COMMANDS = {"status", "heartbeat", "get_demo_log"}

@dataclass
class Message:
    kind: str
    agent_id: str
    payload: dict

    def encode(self) -> bytes:
        return (json.dumps(asdict(self)) + "\n").encode("utf-8")

    @classmethod
    def decode(cls, raw: bytes) -> "Message":
        data = json.loads(raw.decode("utf-8"))
        if not all(key in data for key in ("kind", "agent_id", "payload")):
            raise ValueError("message fields are incomplete")
        if not isinstance(data["payload"], dict):
            raise ValueError("payload must be an object")
        return cls(data["kind"], data["agent_id"], data["payload"])

def validate_command(command: str) -> bool:
    return command in ALLOWED_COMMANDS