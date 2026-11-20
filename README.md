# WebSocket Practice — форматы данных и WebSocket

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Практика по курсу **«Сетевое программирование. Модуль 2. Высокоуровневые протоколы»**
(пара 06 — *Форматы данных и WebSocket*).

Четыре небольших задания: от сравнения форматов сериализации до группового чата
на WebSocket. Всё написано на Python, код снабжён комментариями.

## Содержание

| # | Задание | Что делаем | Папка |
|---|---------|-----------|-------|
| 01 | JSON и protobuf | Сериализуем структуру, сравниваем размеры | [`01_json_protobuf`](01_json_protobuf) |
| 02 | Echo-сервер | WebSocket-сервер и клиент, отправка и получение сообщения | [`02_echo_server`](02_echo_server) |
| 03 | Разбор кадра | Разбираем бинарную структуру кадра: opcode, mask, payload | [`03_frame_parsing`](03_frame_parsing) |
| 04 | Чат | Переписка двух клиентов через сервер; ping/pong и закрытие | [`04_chat`](04_chat) |

## Быстрый старт

```bash
git clone https://github.com/<your-username>/websocket-practice.git
cd websocket-practice

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Нужен Python 3.10+. Задания 01 и 03 работают на одной стандартной библиотеке;
`websockets` нужна только для заданий 02 и 04.

---

## Задание 01. JSON и protobuf

```bash
cd 01_json_protobuf
python compare.py
```

Одна и та же структура `User` кодируется в JSON и в protobuf. Кодировщик protobuf
написан вручную ([`protobuf_lite.py`](01_json_protobuf/protobuf_lite.py)),
чтобы было видно, как устроены байты: `tag = (номер_поля << 3) | wire_type`,
числа — varint, строки — длина + UTF-8.

Типичный результат:

| Формат | Байт | От JSON |
|--------|-----:|--------:|
| JSON (обычный) | 164 | 100% |
| JSON (компактный) | 147 | 90% |
| JSON + gzip | 156 | 95% |
| protobuf | 80 | 49% |
| protobuf + gzip | 101 | 62% |

**Вывод:** protobuf примерно вдвое компактнее JSON, потому что не хранит имена
полей (только номера) и кодирует числа переменной длиной. На маленьких
сообщениях gzip не помогает — заголовок сжатия съедает выигрыш.
Цена protobuf — нечитаемые байты и необходимость общей схемы
([`message.proto`](01_json_protobuf/message.proto)).

## Задание 02. Echo-сервер

Два терминала:

```bash
cd 02_echo_server
python server.py                 # терминал 1
python client.py "Привет!"       # терминал 2
```

```
отправлено: 'Привет!'
получено:   'Привет!'
```

Сервер в цикле `async for message in websocket` возвращает каждое сообщение
отправителю. Цикл сам завершается, когда соединение закрыто.

## Задание 03. Разбор кадра

```bash
cd 03_frame_parsing
python examples.py                           # набор примеров
python examples.py 81 05 48 65 6c 6c 6f      # свой кадр в hex
python live_demo.py                           # реальный обмен (нужен сервер из задания 02)
```

Структура кадра (RFC 6455, §5.2):

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |    Extended payload length    |
|I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
|N|V|V|V|       |S|             |                               |
+-+-+-+-+-------+-+-------------+-------------------------------+
|     Masking-key (4 байта, если MASK = 1)                      |
+---------------------------------------------------------------+
|                          Payload Data                         |
+---------------------------------------------------------------+
```

| Поле | Значение |
|------|----------|
| FIN | 1 — последний кадр сообщения |
| opcode | `0x1` text, `0x2` binary, `0x8` close, `0x9` ping, `0xA` pong, `0x0` continuation |
| MASK | клиент → сервер всегда 1, сервер → клиент всегда 0 |
| Payload len | 0–125 — длина сама; 126 — длина в следующих 2 байтах; 127 — в следующих 8 |
| Masking-key | `payload[i] ^= key[i % 4]` |

Разбор примера из RFC — `81 85 37 fa 21 3d 7f 9f 4d 51 58`:

- `81` → FIN=1, opcode=1 (text)
- `85` → MASK=1, длина 5
- `37 fa 21 3d` → ключ маски
- `7f 9f 4d 51 58` → после XOR с ключом получается `Hello`

[`live_demo.py`](03_frame_parsing/live_demo.py) делает рукопожатие вручную
(HTTP Upgrade + проверка `Sec-WebSocket-Accept`), отправляет собственный
замаскированный кадр по «голому» TCP-сокету и разбирает ответ сервера.

## Задание 04. Чат

Сервер и два клиента, каждый в своём терминале:

```bash
cd 04_chat
python server.py
python client.py Анна
python client.py Борис
```

```
> Привет, Борис!
Анна: Привет, Борис!
Борис: Привет, Анна!
```

Команды клиента: `/ping` — измерить задержку, `/quit` — корректно закрыть соединение.

- **Рассылка.** Сервер хранит словарь подключённых клиентов и через
  `broadcast` отправляет каждое сообщение всем.
- **Ping/pong.** Сервер сам шлёт ping каждые 10 с и закрывает «мёртвые»
  соединения, не ответившие pong. Клиентская команда `/ping` показывает
  время круга ping → pong.
- **Закрытие.** `/quit` отправляет Close-кадр с кодом 1000; сервер ловит
  закрытие и сообщает остальным, что пользователь вышел.

## Структура проекта

```
websocket-practice/
├── 01_json_protobuf/
│   ├── compare.py
│   ├── protobuf_lite.py
│   └── message.proto
├── 02_echo_server/
│   ├── server.py
│   └── client.py
├── 03_frame_parsing/
│   ├── frame_parser.py
│   ├── examples.py
│   └── live_demo.py
├── 04_chat/
│   ├── server.py
│   └── client.py
├── requirements.txt
├── LICENSE
└── README.md
```

## Полезные ссылки

- [RFC 6455 — The WebSocket Protocol](https://datatracker.ietf.org/doc/html/rfc6455)
- [Protocol Buffers: Encoding](https://protobuf.dev/programming-guides/encoding/)
- [Документация библиотеки websockets](https://websockets.readthedocs.io/)

## Лицензия

[MIT](LICENSE)
