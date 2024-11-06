# central_server.py
import pika
import json
from role_manager import RoleManager
from utils import serialize_message, deserialize_message

class CentralServer:
    def __init__(self, host='localhost'):
        self.role_manager = RoleManager()
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='central_queue')

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue='central_queue', on_message_callback=self.on_request)

    def on_request(self, ch, method, properties, body):
        message = deserialize_message(body)
        action = message.get('action')

        response = {}
        if action == 'connect':
            user_id = message.get('user_id')
            # Назначение роли агента I или A
            # Простая логика для примера
            if len(self.role_manager.user_roles) < 5:
                role = 'I'
            else:
                role = 'A'
            try:
                self.role_manager.assign_role(user_id, role)
                response = {
                    'status': 'connected',
                    'role': role,
                    'info_agents': ['info_agent_1', 'info_agent_2']  # Пример адресов
                }
            except Exception as e:
                response = {'status': 'error', 'message': str(e)}
        elif action == 'disconnect':
            user_id = message.get('user_id')
            # Снятие всех ролей
            roles = list(self.role_manager.user_roles.get(user_id, []))
            for role in roles:
                self.role_manager.remove_role(user_id, role)
            response = {'status': 'disconnected'}
        elif action == 'get_status':
            print('принял')
            response = {'sys_status': 'feeling good man'}
        else:
            response = {'status': 'unknown_action'}

        print(f"Отправляем ответ в очередь: {properties.reply_to}")
        ch.basic_publish(
            exchange='',
            routing_key=properties.reply_to,
            properties=pika.BasicProperties(correlation_id=properties.correlation_id),
            body=serialize_message(response)
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def start(self):
        print("Центральный сервер запущен и ожидает подключений...")
        self.channel.start_consuming()

if __name__ == "__main__":
    server = CentralServer()
    server.start()
