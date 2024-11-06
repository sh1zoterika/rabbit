import pickle

def serialize_message(message):
    """Сериализация сообщения в байты"""
    return pickle.dumps(message)

def deserialize_message(message_bytes):
    """Десериализация сообщения из байтов"""
    return pickle.loads(message_bytes)
