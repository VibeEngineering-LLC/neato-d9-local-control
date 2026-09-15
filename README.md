# Проект Neato D9 — управление роботом-пылесосом

**Цель (оператор, 2026-09-15):** научиться управлять роботом-пылесосом Neato по Bluetooth и WiFi.
**Метод:** BLE-сниффинг (nRF52840) + `bleak` (GATT) + разбор доступных путей.

## Устройство

**Neato D9 Intelligent Robot Vacuum**, Part No. 905-0559, S/N <serial redacted>,
FCC ID N6C-SDPAC. Поколение Gen4 (D8/D9/D10, Vorwerk). Внутри — Linux на NXP i.MX (Yocto «Neato LEGO
Distro», ядро 5.4). Полные факты: [`device-facts.md`](device-facts.md).

В сети виден по WiFi как «Neato-Robot»; по BLE рекламируется как `Neato Robot Services` (OUI `08:3A:88` = Neato Robotics).

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
| Serial/UART к Linux | ✗ **вероятно тупик** | Signed firmware + secure boot + залоченная консоль (2 Gen4-эксперимента). Моторный API на Gen4 не выведен. [`research/serial-hardware-vector.md`](research/serial-hardware-vector.md) |
| Kobold/Vorwerk облако | ✗ **не примет D9** | Облако живо, но Neato не проходит валидацию как «genuine Kobold»; прошивку не залить (secure boot). [`research/kobold-vr7.md`](research/kobold-vr7.md) |
| **Vacuula server (self-hosted облако)** | **✅ на подходе, поддержит Gen4** | Сообщество Vacuula (ex-Brainslug) делает замену облака; релиз ~18.09.2026; D9 явно в списке. [`research/community-vacuula-server.md`](research/community-vacuula-server.md) |
| Трюк reboot + play | ⚡ работает сейчас | Перезагрузка + сразу play → уборка в eco-режиме (тонкий тайминг). Запуск без облака уже сегодня. |
| ESP32 на физ. кнопку | ✅ реалистично | Start/Stop из Home Assistant, без карт. |
| Brain-transplant (RPi+ROS2) | ⚙ большой проект | Заменить электронику, оставить механику/лидар. [`research/deep-research-summary.md`](research/deep-research-summary.md) |

**Краткий вывод:** штатных мозгов D9 (Linux/i.MX, signed, secure boot) в одиночку не вскрыть — все пути через
штатные интерфейсы Neato тупиковые (облако мертво, BLE только онбординг, Kobold не принимает Neato, serial
залочен, root по UART пока ни у кого). **НО управлять D9 всё же получится:** сообщество Vacuula (ex-Brainslug,
авторы `fang`) выпускает **self-hosted сервер-замену облака с поддержкой Gen4/D9**, релиз ожидался ~18.09.2026.
**План: дождаться релиза, следить за Discord #updates, поставить сервер по их инструкции** — неинвазивно.
Уже сейчас уборку можно запускать трюком reboot+play. Детали — [`research/community-vacuula-server.md`](research/community-vacuula-server.md).

## Структура

- [`device-facts.md`](device-facts.md) — факты об устройстве (шильдик, сеть, версии).
- `research/` — разведка по каждому вектору с источниками.
- `scripts/` — инструменты (`neato_gatt_scan.py` — GATT-разведка по BLE через bleak, только чтение).
- `captures/` — где лежат BLE-захваты (см. `captures/README.md`; сами pcap — на C: из-за приватности).
- `audit/project-incidents.md` — журнал багов проекта (§32).

## Приватность

Это публичная, обезличенная версия проекта: серийный номер, конкретные MAC-адреса (оставлен только
публичный OUI `08:3A:88` Neato), топология домашней сети и BLE-дампы с ключами/SSID удалены.
Если воспроизводите на своём роботе — подставьте свои значения в `scripts/`.
