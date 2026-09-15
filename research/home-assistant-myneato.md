# home-assistant-myneato — HA-интеграция для D8/D9/D10 (облачная)

Источник: `BenjaminPaap/home-assistant-myneato` (прочитаны README + исходники через `gh api`, 2026-09-15).
Прислан оператором «в базу».

## Суть

HA-интеграция «Neato MyNeato App» для роботов **D8 и выше** через приложение MyNeato. Для старых
роботов — встроенная интеграция HA. Тестировалась только на **D10**; D8 проверил один контрибьютор;
**D9 официально не тестировалась**.

## Технические факты (из исходников `custom_components/myneato/`)

- `manifest.json`: `"iot_class": "cloud_polling"`, `"requirements": ["pyneato==0.0.8"]`, версия 0.0.7.
- Построена на библиотеке **`pyneato`** (НЕ pybotvac). Классы: `Neato`, `OrbitalPasswordSession`.
- Аутентификация: `OrbitalPasswordSession(email, password, token, vendor=Neato())` — email+пароль+токен.
  «Orbital» = облако `orbital.neatocloud.com` (тот же эндпоинт из сетевого анализа, порт 3443).
- Команды/сущности (`vacuum.py`, `services.yaml`): `StateVacuumEntity` (start/stop/return-to-base/pause),
  `CleaningModeEnum`, зональная уборка (`Zone Cleaning`), `myneato_custom_cleaning`, планы этажей
  (floorplans). То есть полный набор команд — НО через облако.

## Вывод для проекта

Подтверждает вектор WiFi как тупик: интеграция функциональна, но `cloud_polling` через
`orbital.neatocloud.com` — а это облако отключено 30.11.2025 (`wifi-cloud-deadend.md`). После отключения
аутентификация и опрос не работают. Локального режима у интеграции нет.

## Чем всё же ценно

**`pyneato`** — наиболее детальная открытая реализация протокола облака MyNeato/Orbital (эндпоинты,
формат запросов, OAuth/Orbital-сессия, команды). Если когда-нибудь понадобится:
- понять протокол облака (для эмуляции/локального сервера при наличии сертификата робота),
- проверить, не жив ли отдельный сегмент облака Vorwerk/Kobold (MyNeato ≠ старое облако Neato Beehive),
— начинать надо с чтения `pyneato`, а не этой интеграции (она лишь тонкая обёртка).

- Репозиторий: https://github.com/BenjaminPaap/home-assistant-myneato
- Библиотека протокола: pyneato (PyPI `pyneato==0.0.8`) — TODO: найти репозиторий-исходник, если понадобится RE протокола облака.

## Открытый вопрос (не проверено)

MyNeato (Vorwerk/Kobold) и старое облако Neato — одна инфраструктура или разные? Если облако Vorwerk для
линейки Kobold живо, а `orbital.neatocloud.com` — общий эндпоинт, теоретически часть функций могла
пережить отключение «Neato». Research 2026-09-15 считал всё облако мёртвым; отдельно сегмент Vorwerk не
проверялся. Проверять, только если BLE- и serial-векторы окажутся тупиковыми.
