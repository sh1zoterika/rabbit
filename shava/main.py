import threading
from allocator_agent import AllocatorAgent
from central_server import CentralServer
from customer_agent import CustomerAgent
from info_agent import InfoAgent
from renderer_agent import RendererAgent


def run_allocator(agent_id):
    agent = AllocatorAgent(agent_id)
    agent.start()


def run_central_server():
    server = CentralServer()
    server.start()


def run_customer(agent_id):
    agent = CustomerAgent(agent_id)
    agent.send_request()
    agent.start()


def run_info_agent(agent_id):
    agent = InfoAgent(agent_id)
    agent.start()


def run_renderer(agent_id):
    renderer = RendererAgent(agent_id)
    renderer.start()


if __name__ == "__main__":
    a_id = input('Введите ID агента-аллокатора: ')
    c_id = input('Введите ID агента-клиента: ')
    i_id = input('Введите ID инфоагента: ')
    r_id = input('Введите ID агента-рендерера: ')

    threads = [
        threading.Thread(target=run_central_server),
        threading.Thread(target=run_info_agent, args=(i_id,)),
        threading.Thread(target=run_renderer, args=(r_id,)),
        threading.Thread(target=run_allocator, args=(a_id,)),
        threading.Thread(target=run_customer, args=(c_id,))
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()
