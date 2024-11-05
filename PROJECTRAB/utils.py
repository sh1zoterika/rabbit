# utils.py
import json

def serialize_message(message):
    return json.dumps(message)

def deserialize_message(message):
    return json.loads(message)
