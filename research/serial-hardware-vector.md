# Serial / аппаратный вектор Neato D9 (Gen4)

Источники (прочитаны лично 2026-09-15): `algaen/neato-connected-D8` (склонирован целиком в
`../refs/neato-connected-D8/`), discussion `RobertSundling/neato-botvac#18`, `dweng0/neat-pi`.

## Архитектура Gen4 (факты)

- Внутри — **Linux** «Neato LEGO Distro 1.7.0-2933» на **NXP i.MX** (Yocto, ядро 5.4), rootfs на чипе
  **Kingston eMMC04G**. UART-консоль `ttymxc1` под логином `Neato-Robot login:` (пароль неизвестен).
- Есть моторный serial-командный интерфейс (см. ниже). Два физических интерфейса (по `refs/.../serial.md`,
  проверено на D3): USB-порт под пылесборником (блокируется крышкой) и TTY-пятаки под пайку/jumper.

## Командный serial-API (из `refs/neato-connected-D8/command-experiments.md`)

Классический Neato serial API — команды, дающие ПОЛНЫЙ низкоуровневый контроль (движение + сенсоры + лидар):

| Команда | Действие |
|---|---|
| `SetMotor RWheelDist 3000 LWheelDist 3000 Speed 60` | ехать вперёд (дистанция мм, скорость) |
| `SetMotor LWheelDisable RWheelDisable` | стоп (для повторного движения — снова enable; или дистанция 1мм; 0 игнорируется) |
| `GetMotor` | RPM/нагрузка/пройденная дистанция колёс, щётка, вакуум |
| `GetLdsScan` | скан лидара (LDS); нужно вращать LDS |
| `GetDigitalSensors` | бампер (L/R side/front/lds bit), пылесборник, DC jack, поднятие колёс |
| `GetAnalogSensors` | батарея (mV/mA/mC), акселерометр XYZ, ток вакуума/щётки, mag/wall/drop-сенсоры |
| `GetErr` | ошибки |
| `TestMode` | режим `UIMGR_STATE_TESTMODE` (в нём GetState не нужен) |

Особенности: команду с пробелом в начале робот отвергает («Nice try, but I'm not falling for that one
again! :P»). Команды можно слать во время приёма данных, исполняются. Автор наметил цикл опроса
(GetErr → GetDigitalSensors → GetAnalogSensors → GetLdsScan) для ROS2/slam_toolbox уборки.

⚠ **Открытый вопрос (не додумывать):** репозиторий смешивает D3 и D8; на каком именно железе сняты эти
команды — надо проверять. Работают ли `SetMotor`/`GetLdsScan` на **D9** и доступен ли моторный интерфейс
БЕЗ пароля (отдельно от Linux-консоли `ttymxc1`) — не подтверждено. Это первый вопрос при физическом доступе.

## Сетевой скан (nmap)

`refs/.../nmap-D8.md`: D8 по WiFi — открыт только порт **53** (DNS, tcpwrapped). Управляющего порта по сети
нет — ещё раз подтверждает WiFi-тупик. (У старых Botvac Connected D3–D7 в pairing-режиме открыт 4443/8081
с TLS 1.0 API `/info`, `/wifi_networks`, `/robot/initialize` — `refs/.../setup-network.md`; к Gen4 неприменимо.)

## Пути получения доступа к ОС

1. **U-Boot по UART:** прервать загрузку, войти в single-user (`init=/bin/sh`) или сбросить пароль —
   ЕСЛИ U-Boot не залочен secure boot (открытый вопрос).
2. **Дамп eMMC** (Kingston eMMC04G) через testpoint/ISP или chip-off → `/etc/shadow`, изучение rootfs.
   Упомянуто в discussion#18 как следующий шаг.
3. **Моторный serial** (см. выше) — если доступен без пароля, даёт управление в обход Linux/облака.

## Научный источник (первого класса)

**Jiska Classen, PhD thesis «Security and Privacy for IoT Ecosystems» (TU Darmstadt, tuprints),
глава II.4 «Neato and Vorwerk Vacuum Cleaners», стр. 35–43** — детальный разбор secure boot, реализации
и векторов обхода защиты Neato, возможность сделать робота независимым от облака. Разбирается запущенным
научным research-агентом (2026-09-15). Указана в `RobertSundling/neato-botvac#18`.

## Оценка

Аппаратный путь даёт РЕАЛЬНОЕ управление (моторный API — полный низкоуровневый контроль), но требует:
вскрытия робота, поиска/пайки debug-порта (зона железа — согласовать с оператором), и, для доступа к ОС,
обхода secure boot / дампа eMMC (сложность зависит от того, залочен ли secure boot — ждём научный research).
Неинвазивные векторы (BLE — закрыт; Kobold-облако — проверяется) приоритетнее по стоимости.
