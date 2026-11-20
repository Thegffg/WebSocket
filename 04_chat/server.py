"""Задание 4. Чат-сервер: переписка нескольких клиентов через сервер.

* первое сообщение клиента — его имя;
* остальные сообщения рассылаются всем подключённым;
* ping/pong: сервер сам шлёт ping каждые 10 секунд и закрывает
  соединение, если pong не пришёл за 10 секунд (параметры библиотеки);
* закрытие: корректный Close-кадр обрабатывается, остальных уведомляем.
"""
import asyncio

from websockets.asyncio.server import broadcast, serve
from websockets.exceptions import ConnectionClosed

HOST, PORT = "localhost", 8766
CLIENTS: dict = {}  # websocket -> имя


async def chat(websocket):
    name = None
    try:
        name = str(await websocket.recv()).strip() or f"user{len(CLIENTS) + 1}"
        CLIENTS[websocket] = name
        print(f"[+] {name} вошёл ({len(CLIENTS)} онлайн)")
        broadcast(CLIENTS.keys(), f"* {name} присоединился к чату")

        async for message in websocket:
            print(f"    {name}: {message}")
            broadcast(CLIENTS.keys(), f"{name}: {message}")
    except ConnectionClosed:
        pass
    finally:
        CLIENTS.pop(websocket, None)
        if name:
            print(f"[-] {name} вышел (код {websocket.close_code})")
            broadcast(CLIENTS.keys(), f"* {name} покинул чат")


async def main():
    async with serve(chat, HOST, PORT, ping_interval=10, ping_timeout=10):
        print(f"Чат-сервер запущен: ws://{HOST}:{PORT}")
        await asyncio.get_running_loop().create_future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nСервер остановлен")
