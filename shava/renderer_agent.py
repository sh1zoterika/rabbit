import pika
from utils import serialize_message, deserialize_message

class RendererAgent:
    def __init__(self, renderer_id, host='localhost'):
        self.renderer_id = renderer_id
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='renderer_queue')  # Очередь для получения задач от allocator
        self.channel.queue_declare(queue='allocator_response_queue')  # Очередь для отправки ответа в allocator

    def process_task(self, ch, method, properties, body):
        """Обработка задачи от allocator и отправка результата обратно"""
        task = deserialize_message(body)
        print(f"Renderer {self.renderer_id}: Обработка задачи {task['task_id']}")

        # Симуляция выполнения рендеринга
        result = f"Рендеринг {task['task_id']} завершен"

        # Отправляем результат обратно в allocator
        response = {
            'status': 'completed',
            'task_id': task['task_id'],
            'result': result
        }
        self.channel.basic_publish(
            exchange='',
            routing_key='allocator_response_queue',
            properties=pika.BasicProperties(reply_to='response_queue', correlation_id=task['task_id']),
            body=serialize_message(response)
        )

        ch.basic_ack(delivery_tag=method.delivery_tag)

    def start(self):
        """Запуск исполнителя для обработки задач"""
        self.channel.basic_consume(queue='renderer_queue', on_message_callback=self.process_task)
        print(f"Renderer {self.renderer_id} запущен и ожидает задачи.")
        self.channel.start_consuming()

if __name__ == "__main__":
    renderer = RendererAgent(renderer_id="renderer_1")
    renderer.start()
