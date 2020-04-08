#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports
from collections import deque


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)
        decoded = data.decode().rstrip()

        if self.login is not None:
            if len(self.server.history) == 10:
                self.server.history.popleft()
            self.server.history.append(f"{self.login}: {decoded}\n")

            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                active_users = [client.login for client in self.server.clients]

                self.login = decoded.replace("login:", "").rstrip()

                if self.login in active_users:
                    self.transport.write(f"Логин {self.login} занят, попробуйте другой.\n".encode())
                    self.transport.abort()

                self.transport.write(
                    f"Привет, {self.login}!\n".encode()
                )
                self.send_history()
            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"

        for user in self.server.clients:
            user.transport.write(message.encode())

    def send_history(self):
        for message in self.server.history:
            self.transport.write(message.encode())


class Server:
    clients: list
    history: deque

    def __init__(self):
        self.clients = []
        self.history = deque([])

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8000
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
