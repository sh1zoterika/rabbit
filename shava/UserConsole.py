import pika
import json
import threading


class UserConsole:
    def __init__(self, host='localhost'):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host))
        self.channel = self.connection.channel()

        # Декларация очереди отправки запросов
        self.channel.queue_declare(queue='info_queue')

        # Декларация очереди для получения ответов
        self.channel.queue_declare(queue='response_queue', durable=True)

    def send_request(self, message):
        """Отправка запроса в очередь info_queue"""
        test = {'type':"get_agents", 'agent_id':'I', 'state':'active'}
        self.channel.basic_publish(
            exchange='',
            routing_key='info_queue',
            body=json.dumps(test),
            properties=pika.BasicProperties(
                reply_to='response_queue',
                delivery_mode=2
            )
        )
        print("Запрос отправлен:", test)

    def on_response(self, ch, method, properties, body):
        """Обработка ответов из очереди response_queue"""
        response = json.loads(body)
        print("Получен ответ:", response)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def listen_for_responses(self):
        """Ожидание ответов в отдельном потоке"""
        self.channel.basic_consume(queue='response_queue', on_message_callback=self.on_response, auto_ack=False)
        print("Ожидание ответов...")
        self.channel.start_consuming()

    def start_console(self):
        """Основной цикл для отправки запросов с клавиатуры"""
        # Запуск потока для прослушивания ответов
        response_thread = threading.Thread(target=self.listen_for_responses)
        response_thread.start()

        try:
            while True:
                # Чтение ввода пользователя
                message = input("Введите запрос: ")

                # Преобразование запроса в словарь и отправка
                if message.lower() == "exit":
                    print("Завершение работы.")
                    break
                else:
                    # Пример структуры запроса
                    request = {"message": message}
                    self.send_request(request)
        except KeyboardInterrupt:
            print("Прервано пользователем.")
        finally:
            self.connection.close()


if __name__ == "__main__":
    console = UserConsole()
    console.start_console()