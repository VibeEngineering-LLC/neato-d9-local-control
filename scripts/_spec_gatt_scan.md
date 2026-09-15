# Спека: neato_gatt_scan.py — GATT-разведка BLE-устройства через bleak

Назначение: подключиться к BLE-устройству (по умолчанию робот Neato) с локального BT-адаптера Windows,
снять полную GATT-карту (сервисы, характеристики, дескрипторы, свойства) и БЕЗОПАСНО прочитать значения
читаемых характеристик. Только чтение — НИКАКИХ write. Вывод машиночитаемый (JSON) + человекочитаемый лог.

## Окружение
- Python 3, Windows 11, библиотека `bleak` версии 3.0.2 (УЖЕ установлена). Стандартная библиотека + bleak.
- BT-адаптер: Intel Wireless Bluetooth (штатный Windows BLE).
- Кодировка: первым делом `sys.stdout.reconfigure(encoding='utf-8')` и `sys.stderr` тоже; файлы utf-8, JSON `ensure_ascii=False`.

## Важно про bleak 3.0.2 (новый API — НЕ устаревший)
- Сканирование: `await BleakScanner.discover(timeout=..., return_adv=True)` возвращает dict `{address: (BLEDevice, AdvertisementData)}`.
- Подключение: `async with BleakClient(address_or_device, timeout=...) as client:`.
- Сервисы: использовать свойство `client.services` (тип BleakGATTServiceCollection). НЕ вызывать устаревший `await client.get_services()`.
- Итерация: `for service in client.services:` → `service.uuid`, `service.description`; `service.characteristics` →
  у характеристики `char.uuid`, `char.description`, `char.properties` (список строк: 'read','write','notify','indicate',...),
  `char.descriptors` → `descr.uuid`, `descr.handle`.
- Чтение: `await client.read_gatt_char(char)` возвращает `bytearray`. Читать ТОЛЬКО если 'read' в `char.properties`.

## Аргументы (argparse)
- `--address` (по умолчанию `08:3A:88:XX:XX:XX`) — MAC BLE-устройства.
- `--name-filter` (по умолчанию `Neato`) — если `--address` не найден при скане, взять первое устройство, чьё имя содержит эту подстроку (регистр не важен).
- `--scan-timeout` (float, по умолчанию 10.0) — сколько сканировать перед подключением.
- `--connect-timeout` (float, по умолчанию 20.0).
- `--out` — путь для JSON (иначе только stdout последней строкой).
- `--no-read` — флаг: не читать значения характеристик, только перечислить структуру.

## Логика
1. Просканировать эфир (`--scan-timeout`). Найти целевое устройство: сперва по `--address` (регистронезависимо),
   иначе по `--name-filter`. Если не найдено — вывести JSON `{"ok":false,"error":"device not found",...}` в stderr одной строкой и exit 2.
2. Вывести человекочитаемо в stderr: найденный адрес, имя, RSSI, adv-данные (service_uuids, manufacturer_data в hex).
3. Подключиться. Если подключение не удалось — JSON `{"ok":false,"error":"connect failed: <текст>"}` в stderr, exit 3.
4. Перечислить GATT: список сервисов, в каждом — характеристики с их properties, дескрипторы.
   Человекочитаемо в stderr: дерево `service.uuid (описание)` → `  char.uuid props=[...] (описание)` → `    descr.uuid handle=N`.
5. Для каждой характеристики со свойством 'read' (если не задан `--no-read`): попытаться прочитать значение.
   Обернуть каждое чтение в try/except (частичный отказ не валит весь скан). В запись добавить `value_hex` (hex-строка через пробел),
   `value_ascii` (печатаемые ASCII, непечатаемые как '.'), либо `read_error` с текстом.
6. Итоговый JSON-объект: `{"ok":true,"address":...,"name":...,"rssi":...,"adv":{"service_uuids":[...],"manufacturer_data":{"<cid_hex>":"<hex>"}},
   "services":[{"uuid":...,"description":...,"characteristics":[{"uuid":...,"description":...,"properties":[...],
   "value_hex":...,"value_ascii":...,"read_error":...,"descriptors":[{"uuid":...,"handle":N}]}]}]}`.
   Если `--out` задан — записать этот объект в файл (utf-8, indent=2, ensure_ascii=False) и в stdout ОДНУ строку `{"ok":true,"out":"<путь>","services":N,"chars":M}`;
   иначе — весь объект одной строкой в stdout.
7. Всё асинхронное — через `asyncio.run(main())`. Коды выхода: 0 успех, 2 устройство не найдено, 3 ошибка подключения, 1 прочая ошибка.

## Приёмка (в комментарии-шапке не писать, это для исполнителя)
- Запуск: `PYTHONIOENCODING=utf-8 python neato_gatt_scan.py --scan-timeout 12 --out neato_gatt.json`
- Ожидается: устройство `Neato Robot Services` найдено, подключение, дерево GATT, JSON записан.
