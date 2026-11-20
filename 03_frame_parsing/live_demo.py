"""Живой кадр: вручную делаем WebSocket-рукопожатие поверх TCP-сокета,
отправляем свой замаскированный кадр и разбираем ответ сервера.

Сначала запустите echo-сервер из задания 2.
"""
import base64
import hashlib
import os
import socket

from frame_parser import build_frame, parse_frame

HOST, PORT = "localhost", 8765
GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"  # константа из RFC 6455

key = base64.b64encode(os.urandom(16)).decode()
request = (
    "GET / HTTP/1.1\r\n"
    f"Host: {HOST}:{PORT}\r\n"
    "Upgrade: websocket\r\n"
    "Connection: Upgrade\r\n"
    f"Sec-WebSocket-Key: {key}\r\n"
    "Sec-WebSocket-Version: 13\r\n\r\n"
)

with socket.create_connection((HOST, PORT)) as sock:
    sock.sendall(request.encode())
    response = b""
    while b"\r\n\r\n" not in response:
        response += sock.recv(4096)
    head, _, rest = response.partition(b"\r\n\r\n")
    print(head.decode(), "\n")

    expected = base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()
    assert expected.encode() in head, "Sec-WebSocket-Accept не совпал"
    print("Рукопожатие OK, Sec-WebSocket-Accept совпал\n")

    # Клиент обязан маскировать кадры
    out = build_frame(0x1, "Привет!".encode(), mask=os.urandom(4))
    print("Отправляем:", out.hex(" "))
    print(parse_frame(out).describe(), "\n")
    sock.sendall(out)

    data = rest
    while len(data) < 2:
        data += sock.recv(4096)
    while True:
        try:
            frame = parse_frame(data)
            break
        except ValueError:
            data += sock.recv(4096)
    print("Получили:", data.hex(" "))
    print(frame.describe())

    sock.sendall(build_frame(0x8, b"\x03\xe8", mask=os.urandom(4)))  # close 1000
