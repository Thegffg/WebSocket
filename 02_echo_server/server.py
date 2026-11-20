"""Задание 2. WebSocket echo-сервер: возвращает клиенту всё, что получил."""
import asyncio

from websockets.asyncio.server import serve

HOST, PORT = "localhost", 8765


async def echo(websocket):
    print(f"[+] подключился {websocket.remote_address}")
    async for message in websocket:  # цикл завершится при закрытии соединения
        print(f"    получено: {message!r}")
        await websocket.send(message)
    print(f"[-] отключился {websocket.remote_address}")


async def main():
    async with serve(echo, HOST, PORT):
        print(f"Echo-сервер запущен: ws://{HOST}:{PORT}")
        await asyncio.get_running_loop().create_future()  # работать вечно


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nСервер остановлен")
