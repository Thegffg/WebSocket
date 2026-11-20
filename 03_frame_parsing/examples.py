"""Разбираем несколько кадров: от простого к сложному."""
import struct
import sys

from frame_parser import build_frame, parse_frame


def show(title: str, raw: bytes) -> None:
    print(f"=== {title} ===")
    print(f"байты ({len(raw)}): {raw[:24].hex(' ')}{' ...' if len(raw) > 24 else ''}")
    print(parse_frame(raw).describe())
    print()


if __name__ == "__main__":
    # Можно передать свой кадр в hex: python examples.py 81 05 48 65 6c 6c 6f
    if len(sys.argv) > 1:
        show("кадр из аргументов", bytes.fromhex("".join(sys.argv[1:])))
        raise SystemExit

    # 1. Пример из RFC 6455: сервер -> клиент, без маски
    show("text 'Hello', без маски (сервер)", bytes([0x81, 0x05, 0x48, 0x65, 0x6C, 0x6C, 0x6F]))

    # 2. Пример из RFC 6455: клиент -> сервер, с маской
    show(
        "text 'Hello', с маской (клиент)",
        bytes([0x81, 0x85, 0x37, 0xFA, 0x21, 0x3D, 0x7F, 0x9F, 0x4D, 0x51, 0x58]),
    )

    # 3. Длина 300 байт -> используется расширенное поле 16 бит (код 126)
    show("text, 300 байт (extended 16 bit)", build_frame(0x1, b"A" * 300))

    # 4. Ping / Pong
    show("ping", build_frame(0x9, b"hi"))
    show("pong", build_frame(0xA, b"hi"))

    # 5. Close с кодом 1000 (нормальное закрытие)
    show("close 1000", build_frame(0x8, struct.pack("!H", 1000) + "bye".encode()))

    # 6. Фрагментация: сообщение, разбитое на 2 кадра
    show("фрагмент 1 (FIN=0, opcode text)", build_frame(0x1, b"Hel", fin=False))
    show("фрагмент 2 (FIN=1, opcode continuation)", build_frame(0x0, b"lo"))
