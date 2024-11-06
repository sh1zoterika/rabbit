import pika
from utils import serialize_message, deserialize_message

class CustomerAgent:
    def __init__(self, user_id, host='localhost'):
        self.user_id = user_id
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(host))
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue='response_queue')  # Объявляем очередь для ответов
            self.channel.queue_declare(queue='info_queue')      # Объявляем очередь для статусов
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Ошибка подключения к RabbitMQ: {e}")
            raise

    def send_request(self, task):
        try:
            # Пример отправки запроса на рендеринг
            self.channel.basic_publish(
                exchange='',
                routing_key='render_queue',
                properties=pika.BasicProperties(reply_to='response_queue'),
                body=serialize_message(task)
            )
            print(f"Запрос отправлен: {task}")
        except Exception as e:
            print(f"Ошибка при отправке запроса: {e}")

    def listen_for_responses(self):
        # Подписка на очередь ответов
        self.channel.basic_consume(queue='response_queue', on_message_callback=self.on_response)
        self.channel.basic_consume(queue='info_queue', on_message_callback=self.on_status_update)
        print("Начинаю прослушивание ответов и обновлений статуса...")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            print("Остановка прослушивания.")
            self.channel.stop_consuming()

    def on_response(self, ch, method, properties, body):
        response = deserialize_message(body)
        print(f"Ответ на запрос рендеринга: {response}")

    def on_status_update(self, ch, method, properties, body):
        status_update = deserialize_message(body)
        print(f"Статус обновления от {status_update['agent_id']}: {status_update['status']}")
        ch.basic_ack(delivery_tag=method.delivery_tag)  # Подтверждение получения сообщения

    def start(self):
        print(f"Пользователь {self.user_id} подключен.")
        try:
            self.send_request({'task_id': self.user_id})
            self.listen_for_responses()
            agent_info = {'agent_id': self.user_id, 'agent_type': 'C', 'message': 'new_agent'}
            self.channel.queue_declare(queue='allocator_info_queue')
            self.channel.basic_publish(exchange='', routing_key='allocator_info_queue',
                                       body=serialize_message(agent_info))
        except KeyboardInterrupt:
            print("Отключение пользователя.")
        finally:
            self.connection.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Использование: python customer_agent.py <user_id>")
        sys.exit(1)
    user_id = sys.argv[1]
    agent = CustomerAgent(user_id)
    agent.start()
