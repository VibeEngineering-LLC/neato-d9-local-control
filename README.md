# Проект Neato D9 — управление роботом-пылесосом после отключения облака

**Цель:** восстановить локальное управление роботом-пылесосом Neato (Gen4) после того, как Vorwerk
отключил облако Neato 30.11.2025. Легальный интероп-анализ собственных устройств.
**Метод:** BLE-сниффинг (nRF52840) + `bleak` (GATT) + разбор USB-C/MTP + реверс приложения MyNeato + разбор всех путей.

**Обновлено: 2026-09-18.**

## Парк устройств

Три робота, ДВА разных поколения — путь к локальному управлению у них разный:

| Робот | Поколение | Локальное управление |
|---|---|---|
| **Neato D7 Connected** | **Gen3** | ✅ решается готовыми проектами (fang / OpenNeato / neato-brainslug): ESP32 на debug-порт, serial-API открыт |
| **Neato D8** | **Gen4** | ⏳ ждёт vacuula server; та же ситуация, что D9 |
| **Neato D9** Intelligent | **Gen4** | ⏳ штатные пути — тупики; ждёт vacuula server |

Основной объект разбора — **D9** (Gen4), D8 идентичен. D7 — отдельный лёгкий случай:
[`research/d7-gen3.md`](research/d7-gen3.md). Полные факты: [`device-facts.md`](device-facts.md).
Внутри Gen4 — Linux на NXP i.MX (Yocto, ядро 5.4). По BLE рекламируется как `Neato Robot Services`
(OUI `08:3A:88` = Neato Robotics).

## Статус путей управления

| Путь | Статус | Детали |
|---|---|---|
| Облако / приложение MyNeato (WiFi) | ✗ **мертво** | Серверы `orbital.neatocloud.com` отключены 30.11.2025 |
| Локальный WiFi-API | ✗ **отсутствует** | Робот только исходит в `orbital.neatocloud.com`, cert pinning на роботе |
| Fake-cloud / MITM | ✗ **робот пинит** | Приложение cert НЕ пинит, но робот рвёт TLS `unknown_ca`. [`research/activation-analysis.md`](research/activation-analysis.md) |
| BLE-управление | ✗ **только онбординг** | GATT снят: WiFi-настройка + Linking + OTA-статус, команд уборки НЕТ. [`research/ble-vector.md`](research/ble-vector.md) |
| **USB-C (MTP)** | ✗ **только прошивка/сервис** | Робот = MTP-гаджет; 5 вендор-опкодов `0x95C1–0x95C5` (семантика неизвестна), свойства-заглушки, команд нет. [`research/mtp-vendor-opcodes.md`](research/mtp-vendor-opcodes.md) |
| Реверс приложения MyNeato | ℹ **протокол снят** | Команды/активация — облачный REST (`/vendors/{vendor}/robots/{serial}/messages`); узкое место — протокол облако↔робот. [`research/myneato-apk-re.md`](research/myneato-apk-re.md) |
| Kobold/Vorwerk облако | ✗ **не примет D9** | Облако живо, но Neato не проходит валидацию как «genuine Kobold». [`research/kobold-vr7.md`](research/kobold-vr7.md) |
| Serial/UART к Linux | ✗ **залочен** | Signed firmware + secure boot + консоль под паролём. [`research/serial-hardware-vector.md`](research/serial-hardware-vector.md) |
| **Vacuula server (self-hosted облако)** | **⏳ задерживается** | Сообщество Vacuula (ex-Brainslug) делает замену облака с поддержкой Gen4; срок 18.09.2026 официально сорван, ориентир «несколько дней». [`research/community-vacuula-server.md`](research/community-vacuula-server.md) |
| Трюк reboot + play | ⚡ работает сейчас | Перезагрузка + сразу play → уборка в eco-режиме. Запуск без облака уже сегодня. |
| Brain-transplant (RPi+ROS2) | ⚙ большой проект | Заменить электронику, оставить механику/лидар. [`research/deep-research-summary.md`](research/deep-research-summary.md) |

## Главный вывод

Все штатные интерфейсы Gen4 — тупики: облако мертво, BLE только онбординг, USB даёт лишь прошивку и
5 недокументированных сервисных опкодов, serial залочен, Kobold не принимает. **Единственный барьер и для
активации, и для локального управления — cert-pinning НА САМОМ РОБОТЕ:** приложение MyNeato сертификат не
проверяет (fake-cloud для него тривиален), но робот отвергает чужой сервер. Обойти это без доступа к роботу
(root/serial) нельзя.

**Реалистичные пути вперёд:** (1) recovery-прошивка через USB-C — проверить, снимает ли требование активации
у нового робота ([`research/official-manual-firmware-update.md`](research/official-manual-firmware-update.md));
(2) дождаться vacuula server (он решает pinning робота); (3) для D7 (Gen3) — готовые ESP32-решения уже сегодня.

## Что делать, если у вас Neato Gen4 остался без облака

Не выбрасывайте. Разбор рынка замен (что покупать вместо, с локальным управлением) —
[`research/replacement-market-2026.md`](research/replacement-market-2026.md). Полная карта векторов доступа с
источниками — [`research/connection-vectors-2026.md`](research/connection-vectors-2026.md).

## Структура

- [`device-facts.md`](device-facts.md) — факты об устройстве.
- `research/` — разведка по каждому вектору с источниками (BLE, USB/MTP, активация, реверс APK, serial, облако, рынок замен).
- `scripts/` — инструменты (только чтение): `neato_gatt_scan.py` (GATT по BLE), `usb_descriptors.py` (USB-дескрипторы),
  `neato_mtp_probe.py` / `neato_mtp_deviceinfo.py` (MTP-разведка через WPD-passthrough), `wpd_probe.py`.
- `captures/` — где лежат BLE-захваты (сами pcap не публикуются — приватность).
- `audit/project-incidents.md` — журнал багов проекта.

## Приватность и легальность

Публичная **обезличенная** версия: серийный номер, конкретные MAC (оставлен публичный OUI `08:3A:88`),
GUID устройства, топология сети, имя хоста и BLE-дампы с ключами/SSID — удалены. Проприетарные файлы
(прошивка `.swu`, APK) в репозиторий не входят (`.gitignore`). Реверс выполнен для восстановления
функциональности собственных устройств после прекращения поддержки вендором.
