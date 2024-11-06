import pika
import json
from utils import serialize_message, deserialize_message
from role_manager import RoleManager
import uuid
import queue
import time

class InfoAgent:
    def __init__(self, agent_id, host='localhost'):
        self.sys_status = 'ok'
        self.agent_id = agent_id
        role_manager = RoleManager()
        self.user_roles = role_manager.user_roles
        self.response_queue = queue.Queue()
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(host))
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue='info_queue')
            self.channel.queue_declare(queue='response_queue')
            print(f"InfoAgent {self.agent_id} запущен.")
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Ошибка подключения к RabbitMQ: {e}")
            raise

    def on_message(self, ch, method, properties, body):
        try:
            message = deserialize_message(body)
            text = message.get('message')
            print(f"InfoAgent {self.agent_id} получил сообщение: {message}")
            if text == 'get_agents':
                ch.basic_publish(
                    exchange='',
                    routing_key=properties.reply_to,
                    properties=pika.BasicProperties(correlation_id=properties.correlation_id),
                    body=serialize_message(self.user_roles)
                )
            elif text == 'get_sys_info':
                correlation_id = str(uuid.uuid4())

                request = {
                    'action': 'get_status',
                    'correlation_id': correlation_id
                }

                # Отправляем запрос в очередь central_queue
                ch.basic_publish(
                    exchange='',
                    routing_key='central_queue',
                    properties=pika.BasicProperties(
                        reply_to='response_queue',  # Очередь для получения ответа
                        correlation_id=correlation_id
                    ),
                    body=serialize_message(request)
                )

                # Ждём ответ от центральной очереди
                response = {'sys_status': 'feeling good man'}
                if response:
                    try:
                        ch.basic_publish(
                            exchange='',
                            routing_key=properties.reply_to,
                            properties=pika.BasicProperties(correlation_id=correlation_id),
                            body=serialize_message(response)
                        )
                    except Exception as e:
                        print('Ошибка отправки отклика')

        except Exception as e:
            print(f"Ошибка обработки сообщения {body}: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag)

    def start(self):
        try:
            self.channel.basic_consume(queue='info_queue', on_message_callback=self.on_message)
            print(f"InfoAgent {self.agent_id} готов к получению сообщений.")
            self.channel.start_consuming()
            agent_info = {'agent_id': self.user_id, 'agent_type': 'C', 'message': 'new_agent'}
            self.channel.queue_declare(queue='allocator_info_queue')
            self.channel.basic_publish(exchange='', routing_key='allocator_info_queue',
                                       body=serialize_message(agent_info))
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Ошибка подключения к RabbitMQ во время ожидания сообщений: {e}")
        except KeyboardInterrupt:
            print("Остановка InfoAgent.")
            self.channel.basic_publish(exchange='', routing_key='info_queue', body=f'Агент {agent_id} отключен')
        finally:
            self.connection.close()

    def wait_for_response(self, correlation_id):
        def on_response(ch, method, properties, body):
            message = deserialize_message(body)
            return message

        self.channel.basic_consume(
            queue='response_queue',
            on_message_callback=on_response
        )
        self.channel.basic_qos(prefetch_count=1)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Использование: python info_agent.py <agent_id>")
        sys.exit(1)
    agent_id = sys.argv[1]
    try:
        info_agent = InfoAgent(agent_id)
        info_agent.start()
    except Exception as e:
        print(f"Ошибка инициализации агента информации: {e}")