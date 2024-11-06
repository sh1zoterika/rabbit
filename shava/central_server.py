import pika
from utils import serialize_message, deserialize_message

class CentralServer:
    def __init__(self, host='localhost'):
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(host))
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue='central_queue')
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(queue='central_queue', on_message_callback=self.on_request)
            print("Центральный сервер запущен и ожидает запросов.")
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Ошибка подключения к RabbitMQ: {e}")
            raise

    def on_request(self, ch, method, properties, body):
        message = deserialize_message(body)
        action = message.get('action')

        response = {}
        if action == 'connect':
            user_id = message.get('user_id')
            response = {
                'status': 'connected',
                'message': f'User {user_id} connected successfully'
            }
        elif action == 'disconnect':
            user_id = message.get('user_id')
            response = {'status': 'disconnected', 'message': f'User {user_id} disconnected successfully'}
        else:
            response = {'status': 'unknown_action', 'message': 'Unknown action received'}

        # Ответ на запрос отправляется обратно на очередь ответа
        ch.basic_publish(
            exchange='',
            routing_key=properties.reply_to,
            properties=pika.BasicProperties(correlation_id=properties.correlation_id),
            body=serialize_message(response)
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def start(self):
        self.channel.start_consuming()

if __name__ == "__main__":
    server = CentralServer()
    server.start()
