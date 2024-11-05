import pika
import json
from utils import serialize_message, deserialize_message

class InfoAgent:
    def __init__(self, agent_id, host='localhost'):
        self.agent_id = agent_id
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(host))
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue='info_queue')
            print(f"InfoAgent {self.agent_id} запущен.")
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Ошибка подключения к RabbitMQ: {e}")
            raise

    def on_message(self, ch, method, properties, body):
        try:
            message = deserialize_message(body)
            print(f"InfoAgent {self.agent_id} получил сообщение: {message}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"Ошибка обработки сообщения {body}: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag)

    def start(self):
        try:
            self.channel.basic_consume(queue='info_queue', on_message_callback=self.on_message)
            print(f"InfoAgent {self.agent_id} готов к получению сообщений.")
            self.channel.start_consuming()
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Ошибка подключения к RabbitMQ во время ожидания сообщений: {e}")
        except KeyboardInterrupt:
            print("Остановка InfoAgent.")
        finally:
            self.connection.close()

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
