"""Задание 1. Сериализуем одну структуру в JSON и protobuf и сравниваем размеры."""
import gzip
import json

import protobuf_lite as pb

user = {
    "id": 42,
    "name": "Анна Петрова",
    "email": "anna@example.com",
    "active": True,
    "scores": [10, 20, 30, 150, 300],
    "tags": ["admin", "python", "network"],
}

json_bytes = json.dumps(user, ensure_ascii=False).encode("utf-8")
json_compact = json.dumps(user, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
proto_bytes = pb.encode(user)

print("JSON:", json_bytes.decode())
print("protobuf (hex):", proto_bytes.hex(" "))
print()

rows = [
    ("JSON (обычный)", json_bytes),
    ("JSON (компактный)", json_compact),
    ("JSON + gzip", gzip.compress(json_compact)),
    ("protobuf", proto_bytes),
    ("protobuf + gzip", gzip.compress(proto_bytes)),
]
base = len(json_bytes)
print(f"{'Формат':<20}{'Байт':>6}{'От JSON':>10}")
for name, data in rows:
    print(f"{name:<20}{len(data):>6}{len(data) / base:>9.0%}")

# Проверка: из байтов получаем ту же структуру
assert pb.decode(proto_bytes) == user, "decode(encode(x)) != x"
print("\nДесериализация protobuf -> dict: OK")
