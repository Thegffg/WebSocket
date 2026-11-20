"""Консольный клиент чата.

Запуск:  python client.py Анна
Команды: /ping — измерить задержку (ping/pong), /quit — закрыть соединение.
"""
import asyncio
import sys
import time

from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed

URI = "ws://localhost:8766"


async def receive(websocket):
    try:
        async for message in websocket:
            print(f"\r{message}\n> ", end="", flush=True)
    except ConnectionClosed:
        pass
    print("\rСоединение закрыто сервером")


async def main():
    name = sys.argv[1] if len(sys.argv) > 1 else input("Ваше имя: ")
    loop = asyncio.get_running_loop()

    async with connect(URI) as websocket:
        await websocket.send(name)
        reader = asyncio.create_task(receive(websocket))

        while not reader.done():
            line = await loop.run_in_executor(None, lambda: input("> "))
            line = line.strip()
            if not line:
                continue
            if line == "/quit":
                await websocket.close(code=1000, reason="bye")  # Close-кадр
                break
            if line == "/ping":
                start = time.perf_counter()
                pong_waiter = await websocket.ping()           # Ping-кадр
                await pong_waiter                              # ждём Pong
                print(f"pong за {(time.perf_counter() - start) * 1000:.1f} мс")
                continue
            await websocket.send(line)

        await reader
    print(f"Закрыто, код {websocket.close_code}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, EOFError, ConnectionClosed):
        print("\nПока!")
