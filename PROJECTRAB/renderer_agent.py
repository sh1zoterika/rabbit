import pika
import json
import time
import random
from utils import serialize_message, deserialize_message

class RendererAgent:
    def __init__(self, renderer_id, host='localhost'):
        self.renderer_id = renderer_id
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(host))
            self.channel = self.connection.channel()
            # Очередь для получения задач рендеринга
            self.channel.queue_declare(queue='render_queue')
            self.channel.queue_declare(queue='info_queue')
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Ошибка подключения к RabbitMQ: {e}")
            raise

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue='render_queue', on_message_callback=self.on_request)

    def on_request(self, ch, method, properties, body):
        try:
            task = deserialize_message(body)
            print(f"Исполнитель {self.renderer_id} получил задачу: {task}")

            # Симуляция рендеринга
            render_time = random.randint(2, 5)
            time.sleep(render_time)

            # Формирование результата
            result = {
                'task_id': task.get('task_id', 'unknown'),
                'status': 'completed',
                'renderer_id': self.renderer_id,
                'render_time': render_time
            }

            # Отправка результата обратно через reply_to
            ch.basic_publish(
                exchange='',
                routing_key=properties.reply_to,
                properties=pika.BasicProperties(correlation_id=properties.correlation_id),
                body=serialize_message(result)
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
            print(f"Исполнитель {self.renderer_id} завершил задачу: {task['task_id']}")
        except Exception as e:
            print(f"Ошибка обработки задачи {body}: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag)  # Не подтверждаем задачу, если произошла ошибка

    def send_status_update(self, status='active'):
        update = {
            'agent_id': self.renderer_id,
            'type': 'R',
            'status': status
        }
        self.channel.basic_publish(
            exchange='',
            routing_key='info_queue',
            body=serialize_message(update)
        )

    def start(self):
        print(f"Исполнитель {self.renderer_id} готов к получению задач.")
        self.send_status_update('active')
        agent_info = {'agent_id': self.user_id, 'agent_type': 'C', 'message': 'new_agent'}
        self.channel.queue_declare(queue='allocator_info_queue')
        self.channel.basic_publish(exchange='', routing_key='allocator_info_queue', body=serialize_message(agent_info))
        try:
            self.channel.start_consuming()
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Ошибка подключения к RabbitMQ во время ожидания задач: {e}")
        except KeyboardInterrupt:
            self.send_status_update('inactive')
            print("Остановка исполнителя.")
        finally:
            self.connection.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Использование: python renderer_agent.py <renderer_id>")
        sys.exit(1)
    renderer_id = sys.argv[1]
    try:
        agent = RendererAgent(renderer_id)
        agent.start()
    except Exception as e:
        print(f"Ошибка инициализации агента: {e}")
