import json

def serialize_message(message):
    """Сериализация сообщения в JSON-формат."""
    return json.dumps(message)

def deserialize_message(message_bytes):
    """Десериализация сообщения из JSON-формата."""
    return json.loads(message_bytes)
