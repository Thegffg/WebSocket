"""Задание 3. Разбор бинарного кадра WebSocket (RFC 6455, раздел 5.2).

     0                   1                   2                   3
     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-------+-+-------------+-------------------------------+
    |F|R|R|R| opcode|M| Payload len |    Extended payload length    |
    |I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
    |N|V|V|V|       |S|             |                               |
    | |1|2|3|       |K|             |                               |
    +-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
    |     Masking-key (0 или 4 байта, если MASK = 1)                |
    +---------------------------------------------------------------+
    |                          Payload Data                         |
    +---------------------------------------------------------------+
"""
import struct
from dataclasses import dataclass

OPCODES = {
    0x0: "continuation",
    0x1: "text",
    0x2: "binary",
    0x8: "close",
    0x9: "ping",
    0xA: "pong",
}


@dataclass
class Frame:
    fin: bool
    rsv: int
    opcode: int
    masked: bool
    length: int
    mask: bytes
    payload: bytes  # уже размаскированный
    size: int       # сколько байт кадр занял в потоке

    def describe(self) -> str:
        lines = [
            f"FIN     : {int(self.fin)}",
            f"RSV1-3  : {self.rsv:03b}",
            f"opcode  : 0x{self.opcode:X} ({OPCODES.get(self.opcode, '?')})",
            f"MASK    : {int(self.masked)}",
            f"length  : {self.length}",
            f"mask    : {self.mask.hex(' ') if self.masked else '—'}",
        ]
        if self.opcode == 0x1:
            text = self.payload.decode("utf-8", "replace")
            lines.append(f"payload : {text[:60]!r}{'...' if len(text) > 60 else ''}")
        elif self.opcode == 0x8 and len(self.payload) >= 2:
            code = struct.unpack("!H", self.payload[:2])[0]
            reason = self.payload[2:].decode("utf-8", "replace")
            lines.append(f"payload : код закрытия {code}, причина {reason!r}")
        else:
            lines.append(f"payload : {self.payload.hex(' ')}")
        return "\n".join(lines)


def parse_frame(data: bytes) -> Frame:
    """Разбирает первый кадр в data. Бросает ValueError, если байт не хватает."""
    if len(data) < 2:
        raise ValueError("нужно минимум 2 байта")

    b0, b1 = data[0], data[1]
    fin = bool(b0 & 0x80)
    rsv = (b0 >> 4) & 0x07
    opcode = b0 & 0x0F
    masked = bool(b1 & 0x80)
    length = b1 & 0x7F
    pos = 2

    if length == 126:                 # длина в следующих 2 байтах
        length = struct.unpack("!H", data[pos:pos + 2])[0]
        pos += 2
    elif length == 127:               # длина в следующих 8 байтах
        length = struct.unpack("!Q", data[pos:pos + 8])[0]
        pos += 8

    mask = b""
    if masked:
        mask = data[pos:pos + 4]
        pos += 4

    payload = data[pos:pos + length]
    if len(payload) < length:
        raise ValueError(f"неполный кадр: ожидалось {length} байт payload, есть {len(payload)}")

    if masked:                        # размаскирование: байт XOR mask[i % 4]
        payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))

    return Frame(fin, rsv, opcode, masked, length, mask, payload, pos + length)


def build_frame(opcode: int, payload: bytes, mask: bytes | None = None, fin: bool = True) -> bytes:
    """Собирает кадр. Если передан mask (4 байта) — кадр маскируется (как у клиента)."""
    out = bytearray([(0x80 if fin else 0) | opcode])
    mask_bit = 0x80 if mask else 0
    n = len(payload)
    if n < 126:
        out.append(mask_bit | n)
    elif n < 1 << 16:
        out.append(mask_bit | 126)
        out += struct.pack("!H", n)
    else:
        out.append(mask_bit | 127)
        out += struct.pack("!Q", n)
    if mask:
        out += mask
        payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    return bytes(out) + payload
