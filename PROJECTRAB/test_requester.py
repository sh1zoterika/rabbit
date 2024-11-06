import pika
import json
import uuid
import sys

def serialize_message(message):
    return json.dumps(message)

def deserialize_message(message):
    return json.loads(message)

def send_request(agent_id, message):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='info_queue')

    correlation_id = str(uuid.uuid4())
    response_queue = channel.queue_declare(queue='', exclusive=True).method.queue

    def on_response(ch, method, properties, body):
        if properties.correlation_id == correlation_id:
            print(f"Ответ от агента {agent_id}: {body.decode()}")
            connection.close()

    channel.basic_consume(
        queue=response_queue,
        on_message_callback=on_response,
        auto_ack=True
    )

    request = {
        'message': message
    }

    channel.basic_publish(
        exchange='',
        routing_key='info_queue',
        properties=pika.BasicProperties(
            reply_to=response_queue,
            correlation_id=correlation_id
        ),
        body=serialize_message(request)
    )

    print(f"Запрос отправлен агенту {agent_id}. Ожидание ответа...")
    channel.start_consuming()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python test_agent.py <agent_id>")
        sys.exit(1)
    agent_id = sys.argv[1]

    while True:
        message = input("Введите сообщение для агента (или 'exit' для выхода): ")
        if message.lower() == 'exit':
            break
        send_request(agent_id, message)
