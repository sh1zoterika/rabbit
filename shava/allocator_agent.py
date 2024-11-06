from xml.sax.handler import property_lexical_handler

import pika
import json

class AllocatorAgent:
    def __init__(self, agent_name):
        self.agent_name = agent_name
        self.role = 'A'
        self.user_id = 'user_id'

        # Соединение с RabbitMQ
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()

        # Создаем новую очередь с нужными параметрами
        self.channel.queue_declare(queue='response_queue', durable=True)

        # Декларация очереди для получения запроса
        self.channel.queue_declare(queue='task_queue', durable=True)

        # Отправка сигнала подключения
        self.send_status_update("active")

        # Удаляем существующую очередь, если она есть
        '''try:
            self.channel.queue_delete(queue='response_queue')
            print("Очередь 'response_queue' была удалена.")
        except pika.exceptions.ChannelClosedByBroker:
            print("Очередь 'response_queue' не существует или уже удалена.")'''

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
        print(f"Сигнал {status} отправлен для агента {self.agent_name} с ролью {self.role} и user_id {self.user_id}")

    def on_request(self, ch, method, properties, body):
        print("Получен запрос:", body)
        task = json.loads(body)

        # Ответ на запрос
        response = {
            'user_id': task['user_id'],
            'status': 'successful',
            'render_config': task['render_config']
        }

        # Отправка ответа обратно в очередь 'response_queue'
        self.channel.basic_publish(
            exchange='',
            routing_key='response_queue',
            body=json.dumps(response),
            properties=pika.BasicProperties(
                reply_to=properties.reply_to,
                correlation_id=properties.correlation_id
            )
        )

        print("Ответ отправлен:", response)

    def start(self):
        # Ожидание запросов
        print(f"Агент {self.agent_name} запущен и ожидает задачи.")
        try:
            self.channel.basic_consume(queue='task_queue', on_message_callback=self.on_request, auto_ack=True)
            self.channel.start_consuming()
        except KeyboardInterrupt:
            # Отправка сигнала отключения
            self.send_status_update("disconnect")
            self.connection.close()
            print("Соединение закрыто")

if __name__ == "__main__":
    # Создаем экземпляр AllocatorAgent и начинаем ожидать задачи
    agent = AllocatorAgent("allocator_1")
    agent.start()
