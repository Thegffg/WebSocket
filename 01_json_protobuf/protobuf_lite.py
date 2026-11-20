"""Минимальная ручная реализация protobuf wire format для схемы User.

Нужна, чтобы увидеть, из чего реально состоят байты protobuf-сообщения.
Поддерживаются два wire type:
    0 — varint (int32, bool)
    2 — length-delimited (string, repeated-поля)
"""

VARINT, LEN = 0, 2

# имя поля -> (номер, тип)
SCHEMA = {
    "id":     (1, "int32"),
    "name":   (2, "string"),
    "email":  (3, "string"),
    "active": (4, "bool"),
    "scores": (5, "int32[]"),
    "tags":   (6, "string[]"),
}


def encode_varint(n: int) -> bytes:
    if n < 0:
        n += 1 << 64  # отрицательные int32 занимают 10 байт
    out = bytearray()
    while True:
        byte = n & 0x7F
        n >>= 7
        if n:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def decode_varint(data: bytes, pos: int) -> tuple[int, int]:
    result = shift = 0
    while True:
        b = data[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not b & 0x80:
            return result, pos
        shift += 7


def _tag(number: int, wire_type: int) -> bytes:
    return encode_varint((number << 3) | wire_type)


def _to_signed32(n: int) -> int:
    n &= 0xFFFFFFFF
    return n - (1 << 32) if n >= 1 << 31 else n


def encode(msg: dict) -> bytes:
    out = bytearray()
    for name, (num, typ) in SCHEMA.items():
        if name not in msg:
            continue
        value = msg[name]
        if typ in ("int32", "bool"):
            if value in (0, False):  # proto3 не пишет значения по умолчанию
                continue
            out += _tag(num, VARINT) + encode_varint(int(value))
        elif typ == "string":
            if value == "":
                continue
            raw = value.encode("utf-8")
            out += _tag(num, LEN) + encode_varint(len(raw)) + raw
        elif typ == "int32[]":  # packed encoding
            if not value:
                continue
            packed = b"".join(encode_varint(v) for v in value)
            out += _tag(num, LEN) + encode_varint(len(packed)) + packed
        elif typ == "string[]":  # каждый элемент — отдельная запись
            for item in value:
                raw = item.encode("utf-8")
                out += _tag(num, LEN) + encode_varint(len(raw)) + raw
    return bytes(out)


def decode(data: bytes) -> dict:
    by_num = {num: (name, typ) for name, (num, typ) in SCHEMA.items()}
    msg: dict = {"scores": [], "tags": []}
    pos = 0
    while pos < len(data):
        key, pos = decode_varint(data, pos)
        num, wire = key >> 3, key & 7
        name, typ = by_num[num]
        if wire == VARINT:
            v, pos = decode_varint(data, pos)
            msg[name] = bool(v) if typ == "bool" else _to_signed32(v)
        else:
            length, pos = decode_varint(data, pos)
            chunk = data[pos:pos + length]
            pos += length
            if typ == "string":
                msg[name] = chunk.decode("utf-8")
            elif typ == "string[]":
                msg[name].append(chunk.decode("utf-8"))
            elif typ == "int32[]":
                p = 0
                while p < len(chunk):
                    v, p = decode_varint(chunk, p)
                    msg[name].append(_to_signed32(v))
    return msg
