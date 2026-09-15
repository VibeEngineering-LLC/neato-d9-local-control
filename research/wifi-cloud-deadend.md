# WiFi / облако — доказанный тупик для Neato D9

Разведка 2026-09-15 (research-субагент + личная сверка первоисточников). Каждый пункт — с источником.

## 1. Облако Neato/Vorwerk отключено

Vorwerk закрыл бренд Neato Robotics в 2023 (при покупке в 2017 обещали 5 лет облака). 06.10.2025 — офиц.
объявление о сворачивании облачных сервисов. Вторичные СМИ единодушно называют **30.11.2025** датой полного
отключения и удаления MyNeato из сторов. Затрагивает все модели, включая D8/D9/D10. После отключения —
только ручной запуск кнопкой; расписание, карты, no-go зоны, OTA мертвы.

- https://support.neatorobotics.com/support/solutions/articles/204000073686-announcement-6th-oct-2025 (офиц.)
- https://www.heise.de/en/news/Vorwerk-subsidiary-Neato-shuts-down-cloud-server-hoovers-lose-functions-10748987.html
- https://vacuumwars.com/neato-ending-cloud-services/
- https://roboselector.com/insights/neato-robot-vacuums-lose-smart-features-cloud-shutdown (дата 30.11.2025)

## 2. Локального WiFi-API у D8/D9/D10 нет

В отличие от старых Botvac Connected (локальный HTTPS на порту 4443 + облачный Nucleo API с клиентским
сертификатом), Gen4 при работе устанавливает только ИСХОДЯЩЕЕ TLS-соединение к `orbital.neatocloud.com`
на **TCP-порту 3443** и не слушает локальных команд. Прослушиваемого порта локального управления нет.

- https://github.com/RobertSundling/neato-botvac/discussions/18 (порт 3443, orbital.neatocloud.com, cert pinning; лог до 08.02.2026)

## 3. pybotvac / Home Assistant — мертвы вместе с облаком

pybotvac (`stianaske/pybotvac`) поддерживает `Neato()` / `Vorwerk()`, аутентификация через OAuth/OTP —
всё через облако. HA-интеграция `benjaminpaap/home-assistant-myneato` для Gen4 — тоже облачная. После
отключения серверов не работает; Neato Developer Network закрыт, новые установки официальной интеграции
невозможны.

- https://github.com/stianaske/pybotvac
- https://github.com/benjaminpaap/home-assistant-myneato
- https://www.home-assistant.io/integrations/neato/

## 4. Fake-cloud / MITM — доказанно нереализуем

MITM Wi-Fi-трафика D8 (RobertSundling, discussion #18): DNS-спуфинг + DNAT редирект
`orbital.neatocloud.com`. Робот отвергает RFC1918, но принимает публичные адреса через DNAT; однако на TLS
ClientHello сразу закрывает соединение с `tls alert unknown_ca` — строгая проверка CA / pinning. Вывод
автора (08.02.2026): подделать облако на сетевом уровне невозможно без модификации устройства; secure boot
и защита прошивки не дают реалистично поменять trust store на роботе.

- https://github.com/RobertSundling/neato-botvac/discussions/18

## 5. Community-мосты (UART) — Gen4 не поддерживают

- **renjfk/OpenNeato** — ESP32-мост к UART debug-порту + локальный веб-UI, без облака. README дословно
  (прочитано лично 2026-09-15): «D8/D9/D10 are NOT supported (different board, password-locked serial port)».
  Только D3–D7. https://github.com/renjfk/OpenNeato
- **vacuula/fang** — ESP32 на serial, локальное управление + HA. Поддержаны Gen1–3 (Botvac D70–D85,
  Connected non-DX, D3–D7 Connected). Наш **Neato D9 `905-0559`** явно перечислен в Gen4, а «Generation 4 —
  Sadly not yet supported» (прочитано лично 2026-09-15; part number совпал с шильдиком). «not yet» =
  в планах, сейчас нет. https://github.com/vacuula/fang
- **94-psy/OpenNeato** — форк с заменой платы на SBC, снова только D3–D7.

## Итог

По WiFi/сети управлять D9 в 2026 нечем. Все пути через штатные и сетевые интерфейсы — доказанные тупики.
Аппаратный путь (UART) для Gen4 существует, но упирается в пароль консоли — см. `serial-hardware-vector.md`.
