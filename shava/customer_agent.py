import pika
import json
import time

class CustomerAgent:
    def __init__(self, agent_name):
        self.agent_name = agent_name
        self.role = 'C'
        # Соединение с RabbitMQ
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()

        # Декларация очереди, в которую будет отправляться запрос
        self.channel.queue_declare(queue='task_queue', durable=True)

        # Декларация очереди для получения ответа
        self.channel.queue_declare(queue='response_queue', durable=True)

        # Переменная для хранения correlation_id
        self.corr_id = None

        self.send_status_update('active')

    def send_request(self):
        message = {
            'user_id': 'customer_1',
            'role': 'customer',
            'model_link': 'example_model_link',
            'render_config': {'quality': 'high'}
        }

        # Генерация уникального correlation_id для ответа
        self.corr_id = str(time.time())

        # Отправка сообщения в очередь 'task_queue'
        self.channel.basic_publish(
            exchange='',
            routing_key='task_queue',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                reply_to='response_queue',  # Указываем очередь для ответа
                correlation_id=self.corr_id,  # Уникальный идентификатор для связи запроса и ответа
                delivery_mode=2  # Сохраняем сообщение
            )
        )

        print("Запрос отправлен в Allocator:", message)

    def on_response(self, ch, method, properties, body):
        # Проверка, соответствует ли correlation_id
        if properties.correlation_id == self.corr_id:
            response = json.loads(body)
            print("Получен ответ:", response)

            # Завершение соединения после получения ответа
            self.connection.close()

    def start(self):
        # Ожидание ответа от Allocator
        print(f"Агент {self.agent_name} ожидает ответов.")
        self.channel.basic_consume(queue='response_queue', on_message_callback=self.on_response, auto_ack=True)
        self.channel.start_consuming()

    def send_status_update(self, status):
        """Отправка сигнала о статусе (подключение/отключение) на центральный сервер"""
        message = {
            'agent_name': self.agent_name,
            'status': status,
            'role': self.role,
            'type': "state_update"
        }
        self.channel.basic_publish(
            exchange='',
            routing_key='info_queue',
            body=json.dumps(message)
        )
        print(f"Сигнал {status} отправлен для агента {self.agent_name} с ролью {self.role} и user_id {self.agent_name}")


if __name__ == "__main__":
    # Создаем экземпляр CustomerAgent и отправляем запрос
    agent = CustomerAgent("customer_1")
    agent.send_request()
    agent.start()
