# allocator_agent.py
import pika
import json
import uuid
import threading
from utils import serialize_message, deserialize_message

class AllocatorAgent:
    def __init__(self, allocator_id, host='localhost'):
        self.allocator_id = allocator_id
        self.active_renderers = []  # Список доступных исполнителей
        self.render_jobs = {}  # {task_id: renderer_id}
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host))
        self.channel = self.connection.channel()

        # Очередь для получения задач рендеринга
        self.channel.queue_declare(queue='allocator_queue')
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue='allocator_queue', on_message_callback=self.on_request)

    def on_request(self, ch, method, properties, body):
        task = deserialize_message(body)
        user_id = task.get('user_id')
        model_link = task.get('model_link')
        render_config = task.get('render_config')

        task_id = str(uuid.uuid4())
        print(f"Allocator {self.allocator_id}: Получена задача {task_id} от пользователя {user_id}")

        # Выбор доступного исполнителя
        if not self.active_renderers:
            response = {'status': 'error', 'message': 'Нет доступных исполнителей.'}
        else:
            renderer_id = self.active_renderers.pop(0)  # Пример выбора
            self.render_jobs[task_id] = renderer_id
            # Отправка задачи исполнителю
            render_task = {
                'task_id': task_id,
                'model_link': model_link,
                'render_config': render_config
            }
            self.channel.basic_publish(
                exchange='',
                routing_key='render_queue',
                properties=pika.BasicProperties(
                    reply_to='allocator_response_queue',
                    correlation_id=task_id,
                ),
                body=serialize_message(render_task)
            )
            response = {'status': 'assigned', 'task_id': task_id, 'renderer_id': renderer_id}

        # Отправка ответа пользователю
        ch.basic_publish(
            exchange='',
            routing_key=properties.reply_to,
            properties=pika.BasicProperties(correlation_id=properties.correlation_id),
            body=serialize_message(response)
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def register_renderer(self, renderer_id):
        self.active_renderers.append(renderer_id)
        print(f"Allocator {self.allocator_id}: Зарегистрирован исполнитель {renderer_id}")

    def unregister_renderer(self, renderer_id):
        if renderer_id in self.active_renderers:
            self.active_renderers.remove(renderer_id)
            print(f"Allocator {self.allocator_id}: Отменена регистрация исполнителя {renderer_id}")

    def start(self):
        print(f"Allocator {self.allocator_id} запущен и ожидает задач.")
        self.channel.start_consuming()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Использование: python allocator_agent.py <allocator_id>")
        sys.exit(1)
    allocator_id = sys.argv[1]
    agent = AllocatorAgent(allocator_id)
    agent.start()
