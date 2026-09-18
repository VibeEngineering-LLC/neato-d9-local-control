# Neato D9 (Gen4) — векторы подключения и доступа к системе

Дата разбора: 2026-09-18. Устройство: Neato D9 / D8 / D10 «Intelligent» (Gen4, Vorwerk/Neato),
Linux 5.4 (Yocto, «NXP i.MX Release Distro 5.4-zeus»), NXP i.MX, eMMC, вторичный контроллер LPC,
прошивка 1.7.0-2933, облако отключено 30.11.2025.

> Дисклеймер по источникам. Значительная часть предметной информации по Gen4 находится в закрытых
> зонах (Discord Vacuula, приватные заметки) и в собственном репозитории оператора
> `VibeEngineering-LLC/neato-d9-local-control`. Собственный репозиторий цитируется как «прежняя работа
> контура», а не как независимое подтверждение. Независимые внешние источники перечислены по каждому
> пункту. Где факта нет — написано «не нашёл».

> ⚠ Дисциплина поколений (критично для всего разбора). Под маркой «Neato D8/D-серия» в сети сосуществуют
> ДВА разных устройства: (1) старые **Botvac Connected D3/D4/D5/D7** и Botvac **D80/D85** — Gen2/Gen3, ARM,
> прошивки 3.x/4.x, открытый serial-API (`SetMotor`, `GetLdsScan`, `TestMode`, состояния `UIMGR_STATE_*`);
> (2) **D8/D9/D10 Intelligent** — Gen4, i.MX/Linux 5.4, прошивка 1.7.x, USB-C как MTP-гаджет,
> serial под паролём. Почти весь публичный «взлом Neato» (Giese/QNX, fang, OpenNeato, репозитории algaen /
> Philip2809 / RobertSundling) относится к Gen2/Gen3 и к Gen4 НЕ переносится напрямую. Это подтверждено
> прямыми формулировками мейнтейнеров (см. ниже).

---

## Таблица векторов

| # | Вектор | Вскрытие/пайка | Статус на 2026 | Ключевой источник |
|---|--------|----------------|----------------|-------------------|
| 1 | MTP: чтение `SW Update\version.txt` (штатно) | Нет | Работает, но даёт только version.txt | Проверено на роботе оператора (контекст задачи) |
| 2 | MTP vendor-операции (0x9xxx) сверх version.txt | Нет | **ПОДТВЕРЖДЕНО 18.09: 5 опкодов 0x95C1–0x95C5** (семантика неизвестна) — см. `mtp-vendor-opcodes.md` | Снято с робота, WPD-passthrough |
| 3 | USB re-enumeration в «download gadget» `0525:A4A5` | Нет (софтверный, но нужен триггер прошивки) | Не подтверждён на Gen4; `A4A5` = Linux mass-storage gadget | the-sz.com USB-ID, devicehunt.com |
| 4 | i.MX SDP (Serial Download, uuu/imx-usb-loader) | **Да** (BOOT_MODE пины/фьюзы на плате) | Не проверено; блокирует HAB secure boot | toradex/imx_loader, docs.foundries.io, NXP |
| 5 | Fake-cloud: DNS-подмена + TLS-MITM (порт 3443) | Нет | **Закрыто** — strict CA validation, alert `unknown_ca` | RobertSundling/neato-botvac Discussion #18 |
| 6 | BLE GATT — управление | Нет | Закрыто — только онбординг (WiFi + linking) | neato-d9-local-control (своя работа); карта снята |
| 7 | UART/serial консоль на плате | **Да** (пайка к debug-порту) | Закрыто — логин под паролём + secure boot | fang, OpenNeato (Gen4 «serial locked») |
| 8 | USB-host: выгрузка логов на флешку (`UIMGR_STATE_USB_LOGCOPY`) | Нет | **Gen3-механизм**; на Gen4 1.7.0 не подтверждён | algaen/neato-connected-D8 firmware.md |
| 9 | Прошивка `.swu` через папку `SW Update` | Нет | Принимает только подписанный пакет; утечки ключа не нашёл | Проверено оператором; аналог Gen3 — RobertSundling |
| 10 | Кастомный сервер fang / vacuula / OpenNeato | **Да** для Gen3 (ESP на serial) | Gen4 НЕ поддержан («другая плата/чип/прошивка») | vacuula/fang, renjfk/OpenNeato READMEs |
| 11 | Downgrade на прошивку с открытым serial | Нет | Не нашёл данных о rollback-защите; для Gen4 нет публичной старой версии | — (не найдено) |
| 12 | i.MX HAB-эксплойты (DCD/CSF-tampering, EMFI/glitch) | **Да** (доступ к плате/eMMC) | Теоретически; на конкретном i.MX Gen4 не проверено | NCC Group, Quarkslab, arXiv 2511.22340 |

---

## Детальный разбор

### Вектор 1–3. USB gadget: MTP, vendor-операции и re-enumeration

**Что штатно.** При подключении USB-C робот поднимается как единственный MTP-гаджет и отдаёт
`SW Update\version.txt`. Это проверено на роботе оператора (отправная точка задачи).

**MTP vendor-операции (Q2).** По спецификации MTP массив `OperationsSupported` из ответа `GetDeviceInfo`
обязан перечислять все поддерживаемые операции, включая вендорские расширения (0x9xxx)
(learn.microsoft.com [MS-DRMND], 2021-06; PTP DeviceInfo — github.com/…/remoteyourcam-usb). **Публичного
дампа `GetDeviceInfo`→`OperationsSupported` именно с Neato Gen4 я не нашёл.** Это дешёвый и невыполненный
шаг разведки: `libmtp`/`pyptp` даст полный список операций и, если Neato добавил вендор-опкоды (запись
логов/файлов, debug), это будет видно без вскрытия. Статус — **не проверено**.

**«USB download gadget» `USB\VID_0525&PID_A4A5` (Q1) — важная поправка.** Это НЕ i.MX SDP. VID `0525` —
Netchip/PLX, диапазон `A4Ax` — стандартные Linux USB-гаджеты; конкретно `0525:A4A5` = **«Linux-USB
File-backed Storage Gadget»** (the-sz.com/products/usbid ?v=0x0525; devicehunt.com — соседние `A4A7`
serial, `A4A8` printer, `A4A2` RNDIS). То есть «download gadget» — это mass-storage-гаджет,
сконструированный УЖЕ ЗАГРУЖЕННЫМ Linux робота (application-level), а не режим boot-ROM. Следствия:
- secure boot / HAB к попаданию в него отношения не имеют — барьер в том, ЧТОБЫ прошивка сама переключила
  USB-функцию в этот режим (recovery/update-стейт);
- если удастся его вызвать, он экспонирует блочное устройство/образ (потенциально раздел обновления) по
  USB mass-storage — это чтение/возможно запись сырого раздела, что богаче MTP.
- **Как в него попасть на Gen4 — я не нашёл** (кнопочных комбинаций для recovery в мануале D8/D9/D10 нет,
  см. ниже). Статус — **не проверено**; рекомендую мониторить PnP на смену VID/PID при разных
  условиях старта и спец-файлах на MTP.

**i.MX SDP через uuu / imx-usb-loader (Q1).** SDP — это recovery-режим boot-ROM i.MX: загрузка образа по
USB/UART (toradex/imx_loader; docs.foundries.io HABv4; imxdev.gitlab.io). Устройство в SDP публикуется
как HID recovery NXP (VID `15A2`/`1FC9`), а НЕ как `0525:A4A5`. Вход в SDP определяется состоянием
BOOT_MODE-пинов/фьюзов на плате — **это требует вскрытия и доступа к плате**. Даже войдя в SDP, на
устройстве с закрытым HAB (secure boot прожжён фьюзами) ROM выполнит HAB-проверку загружаемого образа и
откажет неподписанному (NXP/foundries). Статус для Gen4 — **не проверено, ожидаемо закрыто HAB**; вектор
не бескорпусный.

### Вектор 4 / 12. Boot-chain, HAB secure boot, известные i.MX-обходы (Q5)

Прямых публичных эксплойтов boot-chain **именно Neato Gen4** я не нашёл. Общие по платформе i.MX:
- **NCC Group** — обход secure boot через подмену DCD и CSF (nccgroup.com, «Shining new light on an old
  ROM vulnerability…»); применимо к устройствам с HAB < 4.3.7 либо при рантайм-использовании HABv4 API.
- **Quarkslab** — «Vulnerabilities in High Assurance Boot of NXP i.MX microprocessors» (blog.quarkslab.com).
- **arXiv 2511.22340** (2025-11) — «Keyless Entry: Breaking and Entering eMMC RPMB with EMFI» —
  фолт-инъекция по eMMC; на Gen4 стоит eMMC (Kingston EMMC04G по данным сообщества/своей работы).

Все эти классы требуют **физического доступа к плате** (пины, eMMC, инъекция сбоя) — не бескорпусные, и на
конкретном i.MX-ревизии Gen4 не проверены. Применимость NCC-обхода зависит от версии HAB в ROM робота,
которую я не нашёл.

### Вектор 5. Fake-cloud: DNS + TLS-MITM (Q3, часть 1) — ЗАКРЫТО

Самый предметный внешний источник по Gen4 — **RobertSundling/neato-botvac, Discussion #18: «Neato D8 local
fake cloud – progress log + TLS/CA roadblock on port 3443»**. Метод:
- DNS-хайджек: DNAT порта 53 → подмена `orbital.neatocloud.com` на локальный фейк-облако;
- целевое соединение — TCP **3443** (нестандартный HTTPS).

Результат: робот завершает TCP-хендшейк, но немедленно рвёт соединение TLS-алертом **`unknown_ca`** —
устройство применяет **строгую валидацию CA / вероятный cert pinning**. Цитата участника (в изложении):
«граница не преодолевается со стороны сети в одиночку». Самоподписанные сертификаты и MITM неэффективны;
`.bin`-контейнер обновления зашифрован и распаковывается только на устройстве; современный TLS с
эфемерным обменом ключей не даёт расшифровать трафик без ключей с устройства. **Расследование признано
неосуществимым сетевым путём и свёрнуто.** То есть чисто сетевой fake-cloud на Gen4 **закрыт cert
pinning / CA-валидацией**; обхода pinning без доступа к устройству никто не показал.

### Вектор 10. fang / Vacuula (ex-Brainslug) и OpenNeato (Q3, часть 2)

Вопреки распространённой формулировке «vacuula сделает сервер для Gen4», **репозитории vacuula и OpenNeato
прямо заявляют, что Gen4 НЕ поддержан**, и метод у них — не сетевой, а через ESP на serial:
- **vacuula/fang** (README, main): поддержаны Gen1/Gen2/Gen3 (XV…D7 Connected); Gen4 (D8/D9/D10
  Intelligent) — «Sadly not yet supported». Подключение — **ESP32/ESP32-S3/ESP32-C3, физически
  припаянный к serial/debug-порту** робота («we are parsing the data from the serial interface»). Про
  DNS/сертификаты/pinning механизм в README не раскрыт. Discussion #50 подтверждает: подключение «externally
  to the Debug-Bus», фокус на «gen3 robots».
- **Philip2809/neato-brainslug** (README): Gen4 «use a completely different board, chip and firmware, and
  we cannot interface with these directly»; для Gen4 предлагается лишь «wire an esp32 to the button» —
  физический старт/стоп.
- **renjfk/OpenNeato** (docs/user-guide.md): поддержаны только Botvac D3–D7; «D8/D9/D10 are **not**
  supported (different board, password-locked serial port)». Требует пайки ESP32-C3 к debug-порту (4
  провода RX/TX/3V3/GND). Метод чисто локально-сетевой (web-UI на ESP), НО ТОЛЬКО ПОСЛЕ пайки — не
  сетевой в обход робота.

**Про «responsible disclosure» (Q3).** Явной секции об ответственном раскрытии/о том, что именно они не
публикуют до релиза, в README fang/brainslug/OpenNeato я **не нашёл**. Формулировку «не раскрываем до
релиза» устно приписывают Discord-сообществу Vacuula (discord.gg/PAgwhWvyD8), но проверить через WebFetch
Discord нельзя — **нужен интерактивный Chrome/логин оператора**.

**Вывод по Q3:** на 2026 нет ни одного публично подтверждённого чисто-сетевого способа переключить Gen4
на кастомный сервер; сетевой fake-cloud уперся в cert pinning (Вектор 5), а рабочие OSS-решения (fang/
OpenNeato) для более старых поколений требуют пайки к serial. «Vacuula-сервер для Gen4» в их собственных
репозиториях как поддерживаемый НЕ подтверждён (расхождение с формулировкой в задаче/своём репозитории —
отмечаю честно).

### Вектор 8. USB-host: выгрузка логов на флешку `UIMGR_STATE_USB_LOGCOPY` (Q4)

Это механизм **Gen3 Botvac Connected**, не Gen4:
- **algaen/neato-connected-D8, firmware.md**: на прошивках **3.2.0 / 4.3.5** при вставке USB-флешки робот
  переходит в `UIMGR_STATE_USB_LOGCOPY`, копирует логи, затем обновляет прошивку. Но это робот с
  Botvac-serial-API (`SetMotor`, `GetLdsScan`, `TestMode`) и прошивками 3.x/4.x — то есть **Gen3**, а не
  Gen4-1.7.0 (репозиторий назван «D8», но по прошивке и командам это Botvac D-серии Gen3).
- **RobertSundling/neato-botvac** и общие руководства (github README, robotreviews): на Botvac Connected
  обновление идёт с FAT32-флешки — папка `RobotData` c `.tgz`, робот сам создаёт `RobotLogs` и копирует
  туда логи/крэш-дампы перед обновлением.

**На Gen4 1.7.0 это не подтверждено:** USB-C у Gen4 работает как USB-**device** (MTP-гаджет), а не как
host для флешки; сообщество (fang/OpenNeato) относит Gen4 к «другой плате». Триггерится ли на Gen4
обновление/лог-копия с флешки и что в логах — **я не нашёл**, независимого подтверждения нет. Полезность
логов Gen3 для доступа: это диагностика (сенсоры/ошибки), не креды.

### Вектор 9 / 11. Подписанный firmware-канал, downgrade, rollback (Q6)

- Папка `SW Update` на Gen4 принимает только подписанный `.swu` (AES-зашифрован, ключ на устройстве) —
  отправная точка задачи. **Утечки ключа подписи Neato Gen4 я не нашёл.**
- Аналогия из Gen3 (**RobertSundling/neato-botvac**): там прошивка тоже подписана, и проблема была в
  **истёкшем сертификате подписи**; решение — «precertificate» (подмена истёкшего сертификата рабочим
  предсертификатом) + возможен фейковый NTP, чтобы дата прошла. Это Gen3-история и на Gen4 не переносится
  (другой корень доверия).
- **Downgrade/rollback (Q6):** данных о rollback-защите (монотонные счётчики версий) именно на Gen4 я не
  нашёл. Для Gen4 нет и публично доступной старой прошивки «с открытым serial», на которую можно было бы
  откатиться, — так что downgrade-вектор на сегодня беспредметен (нет ни образа, ни доказанной
  возможности отката). Общая теория downgrade/rollback — обзорные IoT-OTA-статьи (medium.com/iot-forge,
  yalantis.com), к Neato напрямую не привязаны.

### Публичные уязвимости Gen4 и Dennis Giese (Q5)

- **Dennis Giese / dontvacuum.me** специализируется на Roborock/Dreame/Ecovacs; его старая работа по Neato
  относится к **Botvac на QNX** (qnx.com/news pr_5901 — «Neato BotVac … QNX Neutrino»), т.е. к другому,
  более старому поколению. Content-разбор DEF CON 31 PDF извлечь как текст не удалось (бинарный PDF), но по
  индексам докладов **Neato Gen4 (i.MX/Linux) в его публичных материалах я не нашёл**.
- **CVE именно на Neato Gen4 — не нашёл.** Известного публичного обхода boot-chain/HAB для Gen4 — не нашёл.

---

## Ранжирование: что пробовать первым БЕЗ вскрытия

Приоритет — дешёвые, обратимые, чисто-USB/сетевые шаги, которые ещё НЕ сделаны:

1. **Дамп MTP `GetDeviceInfo` → `OperationsSupported` (Вектор 2).** `libmtp`/`pyptp`/`pymtp` по уже
   поднятому MTP-интерфейсу. Даёт полный список операций; вендор-опкоды 0x9xxx (если есть) — прямой путь к
   чтению/записи сверх version.txt. Обратимо, без риска. **Не сделано — сделать первым.**
2. **Провокация USB re-enumeration в `0525:A4A5` (Вектор 3).** Мониторить Windows PnP / `pyusb` на смену
   VID/PID при: (а) разных кнопочных комбинациях на старте (Play/Info — см. мануал: Info-long+Play =
   factory reset, поэтому осторожно), (б) спец-именах файлов/папок, положенных на MTP (по аналогии с
   Gen3 `RobotData`/`RobotLogs`), (в) состоянии «идёт/прервано обновление». Если появится mass-storage
   gadget — читать сырой раздел. Обратимо (кроме factory reset — его избегать).
3. **Поведение firmware-канала на «пустой»/битый пакет (Вектор 9).** Положить в `SW Update` невалидный/
   переименованный файл и снять реакцию (логи, смена MTP-структуры, не появится ли лог-папка) — чисто для
   разведки формата и стейт-машины, без попытки подделать подпись. Обратимо.
4. **Снять сетевой профиль робота при живом WiFi (Вектор 5, для полноты).** Хотя fake-cloud закрыт CA,
   стоит один раз подтвердить на СВОЁМ роботе: DNS-запросы (какие хосты), порт 3443, TLS-алерт — чтобы
   зафиксировать факт pinning на конкретном экземпляре, а не только по Discussion #18. Пассивно/обратимо.

Всё, что ниже, требует вскрытия и/или упирается в secure boot: UART-консоль (пароль), i.MX SDP (BOOT_MODE
пины + HAB), HAB/eMMC-эксплойты, пайка ESP по методу fang/OpenNeato. Их — только если бескорпусные
исчерпаны и владелец пересмотрит готовность вскрывать.

---

## Не удалось проверить (нужны отдельные шаги/доступ)

- **Discord Vacuula** (discord.gg/PAgwhWvyD8) — WebFetch не открывает, философия «responsible disclosure» и
  реальный roadmap Gen4 там. **Нужен интерактивный Chrome с логином оператора.**
- **Дамп MTP-операций именно с Gen4** — публично отсутствует; проверяется только на самом роботе (см.
  ранжирование п.1).
- **Способ вызвать `0525:A4A5`/recovery на Gen4** — публичной инструкции не нашёл.
- **Версия HAB в ROM конкретного i.MX Gen4** — не нашёл; от неё зависит применимость NCC/Quarkslab-обходов.
- **Rollback-защита и старая прошивка Gen4 с открытым serial** — не нашёл ни образа, ни данных о защите.
- **Neato-специфичный контент DEF CON 31 PDF** — PDF не парсится как текст; можно пересмотреть слайды/видео
  (youtube AfMfYOUYZvc) вручную, но Gen4 там, по индексам, не ожидается.
- **`Philip2809/neato-connected/firmware.md`** — отдал 404 при выгрузке; читал форк `algaen/neato-connected-D8`.

---

## Источники

- vacuula/fang README — https://github.com/vacuula/fang (fetched 2026-09-18)
- Philip2809/neato-brainslug README — https://github.com/Philip2809/neato-brainslug (fetched 2026-09-18)
- renjfk/OpenNeato user-guide — https://github.com/renjfk/OpenNeato/blob/main/docs/user-guide.md (fetched 2026-09-18)
- RobertSundling/neato-botvac Discussion #18 (D8 fake cloud / TLS-CA 3443) — https://github.com/RobertSundling/neato-botvac/discussions/18 (fetched 2026-09-18)
- RobertSundling/neato-botvac precertificate-firmware README — https://github.com/RobertSundling/neato-botvac (fetched 2026-09-18)
- vacuula/fang Discussion #50 (D7 + ESP, Debug-Bus) — https://github.com/vacuula/fang/discussions/50 (fetched 2026-09-18)
- algaen/neato-connected-D8 (firmware.md, nmap-D8.md, command-experiments.md — Gen3-класс) — https://github.com/algaen/neato-connected-D8 (via gh api, 2026-09-18; nmap датирован 2025-11-30)
- USB-ID `0525:A4A5` = Linux File-backed Storage Gadget — https://the-sz.com/products/usbid/index.php?v=0x0525 ; https://devicehunt.com/view/type/usb/vendor/0525 (fetched 2026-09-18)
- i.MX SDP / imx_usb_loader — https://github.com/toradex/imx_loader ; https://imxdev.gitlab.io/tutorial/Using_the_imx_usb_loader_tool/ (fetched 2026-09-18)
- i.MX HAB secure boot (HABv4) — https://docs.foundries.io/95/reference-manual/security/secure-boot-imx-habv4.html (fetched 2026-09-18)
- NCC Group — secure boot bypass via DCD/CSF на NXP i.MX — https://www.nccgroup.com/research/shining-new-light-on-an-old-rom-vulnerability-secure-boot-bypass-via-dcd-and-csf-tampering-on-nxp-imx-devices/ (fetched 2026-09-18)
- Quarkslab — HAB vulnerabilities i.MX — https://blog.quarkslab.com/vulnerabilities-in-high-assurance-boot-of-nxp-imx-microprocessors.html (fetched 2026-09-18)
- arXiv 2511.22340 — eMMC RPMB EMFI — https://arxiv.org/pdf/2511.22340 (2025-11)
- MTP OperationsSupported / vendor extension — https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-drmnd/2995527e-53fb-4612-8615-bd1c3c444832 (2021)
- Dennis Giese — https://dontvacuum.me/ ; DEF CON 31 talk — https://media.defcon.org/DEF%20CON%2031/DEF%20CON%2031%20presentations/Dennis%20Giese%20-%20Vacuum%20robot%20security%20and%20privacy%20-%20prevent%20your%20robot%20from%20sucking%20your%20data.pdf (2023-08)
- Neato Botvac = QNX (старое поколение) — http://www.qnx.com/news/pr_5901_1.html
- Neato D8/D9/D10 мануал (кнопки, factory reset, нет recovery-режима) — https://www.manualslib.com/guide/3614030/neato-d8-d9-d10-manual.html (fetched 2026-09-18)
- Своя прежняя работа контура — https://github.com/VibeEngineering-LLC/neato-d9-local-control (fetched 2026-09-18)

---

## LESSONS

- Ожидал, что `USB\VID_0525&PID_A4A5` — это i.MX SDP/download-режим boot-ROM → оказалось, что `0525` —
  Netchip/PLX, а `A4A5` = штатный Linux **mass-storage-гаджет** (application-level, конструируется уже
  загруженным Linux) → обход: не искать вход через HAB/BOOT_MODE, а искать firmware-триггер (recovery/
  update-стейт) и мониторить смену VID/PID; i.MX SDP — это отдельный вектор с VID `15A2`/`1FC9` и пайкой.
- Ожидал, что «vacuula/fang сделают сетевой сервер для Gen4» → оказалось, что fang/OpenNeato прямо пишут
  «Gen4 не поддержан, другая плата, serial под паролём», а единственная сетевая попытка на Gen4
  (Discussion #18) уперлась в cert pinning `unknown_ca` → обход: чисто-сетевого пути на сегодня нет;
  различать поколения по прошивке (1.7.x = Gen4 i.MX vs 3.x/4.x = Gen3 Botvac), иначе Gen3-механизмы
  (USB_LOGCOPY, открытый serial-API) ошибочно приписываются Gen4.

---

## Проверка среды на HOST (2026-09-18, контур Программист)

Попытка выполнить вектор №2 (снять MTP `OperationsSupported` / vendor-opcodes) на живом D9:
- Робот подключён (`Get-PnpDevice` → «Neato Robot», OK), USB read-only снят (см. `usb-mtp-recon.md`).
- На Windows MTP-устройство держит драйвер `WUDFWpdMtp` → `libusb`/`pyusb` claim интерфейса невозможен
  без замены драйвера (Zadig/WinUSB), а это меняет систему и ломает штатный MTP. Не делал.
- Штатный путь — WPD MTP-passthrough (`IPortableDevice::SendCommand` + `WPD_COMMAND_MTP_EXT_GET_SUPPORTED_VENDOR_OPCODES`
  и `..._EXECUTE_COMMAND_WITH_DATA_TO_READ` для `GetDeviceInfo`; источник: learn.microsoft.com «Supporting MTP Extensions»).
- `comtypes.GetModule` для `PortableDeviceApi.dll`/`PortableDeviceTypes.dll` — OK, но PROPERTYKEY-константы
  MTP-расширений в TLB **не экспортируются** (`wpd_probe.py` → «WPD_COMMAND/MTP_EXT constants found: 0»).
  Их fmtid/pid лежат в заголовке `WpdMtpExtensions.h` (Windows SDK). **Гадать GUID нельзя (#AH).**
- **Вывод:** вектор №2 реализуем, но требует WPD-клиента с GUID, выверенными по `WpdMtpExtensions.h`/`PortableDevice.h`
  из Windows SDK, + маршалинг `IPortableDevicePropVariantCollection`. Отдельная инженерная задача, не «пара
  минут». Ожидаемый выхлоп низкий (публичного свидетельства о вендор-опкодах у Gen4 нет), запуск — за оператором.
