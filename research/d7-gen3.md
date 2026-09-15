# Neato D7 (Gen3) — лёгкий случай, решается готовым

D7 Connected — поколение **Gen3** (не Gen4, как D8/D9). Для Gen3 локальное управление в обход мёртвого
облака **уже решено** готовыми community-проектами — ничего разрабатывать/ждать не нужно.

## Почему D7 проще Gen4

- **Открытый serial-моторный API** напрямую (`SetMotor`, `GetLdsScan`, `GetDigitalSensors`, `GetAnalogSensors`,
  `TestMode`…) — без пароля. У Gen4 этот порт наружу не выведен. Источник: XV/Botvac Programmer's Manual.
- **Локальный HTTP-API** (порт 4443, TLS) в pairing-режиме — часть операций локально. У Gen4 нет.
- debug-порт и распиновка известны (`refs/neato-connected-D8/serial.md`: D3–D7 одинаковы; UART-пины за
  передним бампером).
- Secure boot у Gen3 не мешает локальному serial-управлению (в отличие от Gen4, где всё подписано).

## Готовые проекты для D7 (работают сегодня)

| Проект | Что даёт | Ссылка |
|---|---|---|
| **fang** (vacuula) | D7 = gen3, локальное управление + Home Assistant через ESP32 на debug-порт | https://github.com/vacuula/fang |
| **OpenNeato** (renjfk) | D3–D7: ESP32-мост к UART + локальный веб-UI, без облака | https://github.com/renjfk/OpenNeato |
| **neato-brainslug** (Philip2809) | D3–D7 поддержаны (Gen4 — «not yet») | https://github.com/Philip2809/neato-brainslug |
| **vacuula server v1** | «basic local control» для gen1–3 — релизнутая ветка (не «на подходе», как для gen4) | Discord `discord.gg/PAgwhWvyD8` |

## План для D7

1. Выбрать проект (рекомендация: **fang** или **OpenNeato** — оба зрелые, с HA-интеграцией).
2. Нужен **ESP32** (dev-board или esp32-cam) + провода/JST + паяльник.
3. Вскрыть D7, найти debug-порт (за передним бампером), подпаять ESP32 (RX на нестандартный GPIO — у OpenNeato
   был нюанс с RX-пином, использовал GPIO13). ⚠ Вскрытие/пайка — зона железа, согласовать с оператором.
4. Прошить ESP32 конфигом проекта, подключить к WiFi/Home Assistant.
5. Проверить команды (start/stop/dock), лидар, сенсоры.

## Отличие от D8/D9

D8/D9 (Gen4) этим путём НЕ заводятся (другая плата, порт под паролем, всё подписано) — им нужен vacuula
server (`community-vacuula-server.md`). D7 — можно начинать сразу.
