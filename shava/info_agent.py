import json

import pika
from utils import serialize_message, deserialize_message

class InfoAgent:
    def __init__(self, agent_id, host='localhost'):
        self.agent_id = agent_id
        self.state = {}  # Хранение состояния системы
        self.agents = {}  # Хранение информации об агентах
        self.sys_status = 'ok'
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(host))
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue='info_queue')
            print(f"InfoAgent {self.agent_id} запущен.")
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Ошибка подключения к RabbitMQ: {e}")
            raise

    def on_message(self, ch, method, properties, body):
        """Обработка входящих сообщений от других агентов"""
        try:
            message = json.loads(body)
            print(f"InfoAgent {self.agent_id} получил сообщение: {message}")

            # Обработка типов сообщений и обновление состояния
            if message.get("type") == "state_update":
                self.update_state(message)
            elif message.get("type") == "activity_check":
                self.check_activity(message)
            elif message.get("type") == "role_change":
                self.change_role(message)
            elif message.get('type') == 'get_sys_info':
                self.sys_info()
            elif message.get('type') == 'get_agents':
                self.agents_info()

            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"Ошибка обработки сообщения {body}: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag)

    def update_state(self, message):
        """Обновление состояния системы на основе сообщения от агентов"""
        agent_id = message["agent_id"]
        state = message["state"]
        role = message.get('role'),
        user_id = message.get('user_id')
        self.agents[agent_id] = {
            'state': state,
            'role': role,
            'user_id': user_id
        }
        print(f"Состояние агента {agent_id} обновлено: {state}, роль: {role}, user_id: {user_id}")

        # Уведомление других агентов об изменении состояния
        self.notify_agents({"type": "state_update", "agent_id": agent_id, "state": state})

    def check_activity(self, message):
        """Периодическая проверка активности агентов"""
        agent_id = message["agent_id"]
        if agent_id not in self.agents or self.agents[agent_id] != "active":
            print(f"Агент {agent_id} не активен, уведомляем центральный сервер.")
            self.notify_server({"type": "agent_inactive", "agent_id": agent_id})

    def change_role(self, message):
        """Изменение ролей агента"""
        agent_id = message["agent_id"]
        new_role = message["new_role"]
        self.agents[agent_id] = new_role
        print(f"Роль агента {agent_id} изменена на {new_role}")
        self.notify_agents({"type": "role_changed", "agent_id": agent_id, "new_role": new_role})

    def notify_agents(self, message):
        """Уведомление других агентов"""
        for agent in self.agents:
            self.channel.basic_publish(
                exchange='',
                routing_key=agent,
                body=serialize_message(message)
            )

    def notify_server(self, message):
        """Уведомление центрального сервера"""
        self.channel.basic_publish(
            exchange='',
            routing_key='central_queue',
            body=serialize_message(message)
        )

    def sys_info(self):
        print(f'Состояние системы:{self.sys_status}')

    def agents_info(self):
        print(self.agents)

    def start(self):
        self.channel.basic_consume(queue='info_queue', on_message_callback=self.on_message)
        print("InfoAgent ожидает сообщений.")
        self.channel.start_consuming()


if __name__ == "__main__":
    agent = InfoAgent(agent_id="info_agent_1")
    agent.start()
