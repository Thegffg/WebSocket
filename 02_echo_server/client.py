"""Клиент для echo-сервера: отправляет сообщение и печатает ответ."""
import asyncio
import sys

from websockets.asyncio.client import connect

URI = "ws://localhost:8765"


async def main():
    text = " ".join(sys.argv[1:]) or "Привет, WebSocket!"
    async with connect(URI) as websocket:
        await websocket.send(text)
        print(f"отправлено: {text!r}")
        reply = await websocket.recv()
        print(f"получено:   {reply!r}")


if __name__ == "__main__":
    asyncio.run(main())
