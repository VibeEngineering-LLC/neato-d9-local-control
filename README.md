# Проект Neato D9 — управление роботом-пылесосом

**Цель:** получить локальное управление роботом-пылесосом Neato D9 по Bluetooth и WiFi после отключения
облака Neato. **Метод:** BLE-сниффинг (nRF52840) + `bleak` (GATT) + разбор доступных путей.

## Устройство

**Neato D9 Intelligent Robot Vacuum**, Part No. 905-0559, S/N <serial redacted>,
FCC ID N6C-SDPAC. Поколение Gen4 (D8/D9/D10, Vorwerk). Внутри — Linux на NXP i.MX (Yocto «Neato LEGO
Distro», ядро 5.4). Полные факты: [`device-facts.md`](device-facts.md).

В сети виден по WiFi как «Neato-Robot»; по BLE рекламируется как `Neato Robot Services` (OUI `08:3A:88`
= Neato Robotics).

## Статус путей управления (на 2026-09-15)

| Путь | Статус | Детали |
|---|---|---|
| Облако / приложение MyNeato (WiFi) | ✗ **мертво** | Серверы Neato отключены 30.11.2025 (Vorwerk свернул бренд) |
| Локальный WiFi-API | ✗ **отсутствует** | D9 только исходит в `orbital.neatocloud.com:3443`, cert pinning |
| Fake-cloud / MITM | ✗ **провалено** | Сообщество, 02.2026: cert pinning + secure boot |
| pybotvac / Home Assistant (myneato, pyneato) | ✗ **мертво** | `cloud_polling` через `orbital.neatocloud.com` — отключён. [`research/home-assistant-myneato.md`](research/home-assistant-myneato.md) |
| OpenNeato / fang (UART-мост ESP32) | ✗ **D9 не поддержан** | «D8/D9/D10 NOT supported — different board, password-locked serial port» |
| BLE-управление | ✗ **только онбординг** | GATT снят с робота: WiFi-настройка + Linking, команд уборки НЕТ. [`research/ble-vector.md`](research/ble-vector.md) |
| **Kobold/Vorwerk API v2** | **? живое облако** | Облако Kobold РАБОТАЕТ (команды есть); вопрос — примет ли D9. [`research/kobold-vr7.md`](research/kobold-vr7.md) |
| **Serial/UART (аппаратный)** | **? глубокий RE** | Linux i.MX, консоль под логином. Вскрытие + пайка. [`research/serial-hardware-vector.md`](research/serial-hardware-vector.md) |

**Краткий вывод:** штатные пути Neato (облако, локальный API, BLE-команды, community-мосты) — доказанные
тупики. BLE-карта снята с самого робота: там только онбординг (настройка WiFi + привязка), команд уборки нет.
Остаются два непроверенных вектора: (1) **живое облако Kobold/Vorwerk API v2** — примет ли оно Neato D9
(самый перспективный, неинвазивный); (2) аппаратный UART-доступ к Linux (перспективный по возможностям,
но требует вскрытия и обхода пароля консоли).

## Структура

- [`device-facts.md`](device-facts.md) — факты об устройстве (шильдик, сеть, версии).
- `research/` — разведка по каждому вектору с источниками.
- `scripts/` — инструменты (`neato_gatt_scan.py` — GATT-разведка по BLE через bleak, только чтение).
- `captures/` — где лежат BLE-захваты (см. `captures/README.md`; сами pcap — на C: из-за приватности).
- `audit/project-incidents.md` — журнал багов проекта (§32).

## Приватность

Это публичная, обезличенная версия проекта: серийный номер, конкретные MAC-адреса (оставлен только
публичный OUI `08:3A:88` Neato), топология домашней сети и BLE-дампы с ключами/SSID из неё удалены.
Если воспроизводите на своём роботе — подставьте свои значения в `scripts/`.
