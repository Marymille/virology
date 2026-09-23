import pytest

from agent.agent import handle_command
from common.protocol import Message, validate_command


def test_message_round_trip() -> None:
	message = Message("result", "demo-agent", {"alive": True})
	assert Message.decode(message.encode()) == message


def test_only_demo_commands_are_allowed() -> None:
	assert validate_command("status")
	assert not validate_command("whoami")
	assert not validate_command("powershell")


def test_unknown_command_is_refused() -> None:
	response = handle_command("powershell")
	assert response.kind == "error"
