# Neato orbital — облачный протокол (снят перехватом MyNeato 1.5.5, 2026-09-19)

Метод: патченый MyNeato 1.5.5 (в APK встроен mitm-CA через network_security_config) + mitmproxy с
fake-orbital аддоном (`neato/scripts/mitm_neato_addon.py`). Приложение обмануто полностью: логин, профиль,
регистрация — всё прошло на локальном сервере. Реальные email/пароль оператора из тела логина НЕ приводятся.

## Хост и общие заголовки

- База: `https://orbital.neatocloud.com`
- Каждый запрос: `Accept: application/vnd.neato.orbital-http.v1+json`, `mobile-app-version: 1.5.5`,
  `x-neato-client-platform: Android`, `x-neato-client-build: 213`, `user-agent: okhttp/4.9.1`.
- После логина: `Authorization: Token <token>`.

## Снятые эндпоинты (реальные запросы приложения)

| Метод | Путь | Тело / примечание |
|---|---|---|
| POST | `/vendors/neato/sessions` | `application/x-www-form-urlencoded`: `email=<...>&password=<...>` → ответ `{"token": "..."}` |
| POST | `/mobile_devices` | JSON: `{app_version, device_id(uuid), locale, notification_token(FCM), platform:"android", version:"15"}` |
| GET | `/users/me` | профиль (id, email, first_name, last_name, country_code, locale) |
| GET | `/users/me/robots` | список роботов; **опрашивается каждые ~6 сек** (ключевой поллинг) |
| GET | `/users/me/app_notifications` | уведомления |
| GET | `/spotlight_messages?limit=10&language=<lang>` | промо-сообщения |
| POST | `/vendors/{vendor}/robots/{serial}/messages` | команда роботу; тело `{"ability":"<action>", ...}`. Снято `{"name":"dustbin","type":"timer","ability":"reminders.get"}`. Управление уборкой — тем же путём (`cleaning.start` и т.п.), но требует непустого списка роботов (не снято — робота в облаке нет). |

## Рабочий fake-orbital

`scripts/mitm_neato_addon.py` (mitmproxy addon): перехватывает `*neatocloud*`, отвечает подделками
(`/sessions`→token, `/users/me/robots`→[], `/users/me`→профиль, `/mobile_devices`→id, прочее→{}).
Запуск (обязательны `--set connection_strategy=lazy` — иначе mitm падает 502 на резолве мёртвого orbital —
и `--ignore-hosts '^(?!.*neatocloud).*$'` в ОДИНАРНЫХ кавычках — иначе Cronet-трафик Google рушит старт).
Итог: **приложение полностью живёт на локальном сервере** — это рабочий прототип клиентской половины vacuula.

## Экспериментальное подтверждение барьера (2026-09-19)

Пройден онбординг реального D9: приложение по BLE связалось с роботом, прочитало список его Wi-Fi-сетей
(`WIFI_NETWORK_SCANNER`), передало роботу пароль (RSA по BLE), робот подключился к Wi-Fi — **но
зарегистрироваться не смог**: при онбординге робот идёт на `orbital.neatocloud.com` САМ, по своему DNS
(мёртвый) и с cert-pinning, а fake-orbital стоит только на телефоне (через прокси) — роботу недоступен.
Приложение робота не дождалось → «не удалось подключиться».

**Вывод (теперь не гипотеза, а факт на железе):** клиентскую половину (приложение) можно обмануть целиком,
но робот при активации выходит в облако сам и не пробивается на подставной сервер. Барьер — cert-pinning
НА РОБОТЕ + резолв orbital. Чтобы его снять, нужно ОДНОВРЕМЕННО: (а) DNS-подмена `orbital.neatocloud.com`→
локальный сервер на уровне сети/роутера (зона MikroTik, §12 — писать промпт), и (б) обойти pinning робота
(через прошивку/serial = вскрытие, либо ждать vacuula server, который это решает своим способом).

## Артефакты сессии (НЕ публиковать сырьём)

- `scratchpad/mitm_neato_log.txt` — перехват, содержит реальные email/пароль оператора → приватно, не в git.
- `scratchpad/myneato_patched.apk` — патченый APK (проприетарный) → не в git.
- Патч: `res/xml/network_security_config.xml` (trust user + `@raw/mitmca`), CA в `res/raw/mitmca.pem`.

## Эксперимент по сети 2026-09-19 (малина <pi-lan-ip> + DNS-подмена на роутере)

Схема: сервер `orbital_local_server.py` на Raspberry Pi (<pi-lan-ip>, HTTPS 443+3443), MikroTik
заворачивает DNS `orbital.neatocloud.com`→малина точечно по MAC (перехват порта 53). Приложение —
патченый APK, серт малины подписан mitmca (тем, что зашит в APK, CN/SAN=orbital.neatocloud.com).

**ФАКТЫ ПРОТОКОЛА, снятые вживую:**
- **Порты:** приложение MyNeato ходит на **443**, РОБОТ (Gen4) — на **3443** (разные каналы; 3443 ≈ Nucleo/real-time).
- **Робот отвергает серт:** робот доходит до 3443, шлёт ClientHello (SNI orbital.neatocloud.com, обычный
  OpenSSL-клиент, без расширения certificate_authorities), получает серт и рвёт TLS `unknown_ca` (alert 48).
  Обойти серверно нельзя (нет доверенного роботу CA). Управление Gen4 через облако недостижимо без модификации робота.
- **Приложение ПОЛНОСТЬЮ работает на локальном сервере ПО СЕТИ** (не только через телефонный прокси): логин →
  `GET /users/me` → `GET /users/me/robots` (показывает робота) → `GET /users/me/app_notifications` [] →
  `GET /spotlight_messages?limit=10&language=ru` [] → далее команды.
- **Путь команд:** `POST /vendors/{vendor}/robots/{serial}/messages`, тело `{"ability":"<action>", ...}`.
  Вендор берётся из объекта робота в `/users/me/robots` — **без поля `vendor` путь получается `/vendors//robots/...`**
  (пустой сегмент). В fake-робота добавлено `"vendor":"neato"`.
- **Реальная последовательность ability при открытии робота** (снята из лога): `reminders.get`
  (тело `{"name":"dustbin","type":"timer","ability":"reminders.get"}`) → затем пачкой `info.robot`,
  `info.wifi`, `settings.cleaning_options`, `settings.robot_language`. Команда старта — `cleaning.start`
  (известна из статического реверса), но приложение **падает раньше**, на `info.*`/`settings.*`, если сервер
  отвечает `data:{}` — форматы этих ответов у реального orbital не реверснуты (эталона нет, облако мертво).
- **Поллинг:** приложение опрашивает `GET /users/me/robots` каждые ~6 c (ждёт состояние — traits/nucleo_url).
- **Онбординг/несколько имён:** приложение открывает соединения и к другим хостам `*neatocloud*` (кроме orbital),
  DNS-подмена их тоже заворачивает на малину, но серт выписан только на orbital → часть соединений даёт alert 46.

**Итог:** клиентская половина (приложение) воспроизводится на локальном сервере полностью до уровня команд;
дальнейшая доводка (чистый вызов cleaning.start без краха) требует реверса форматов ответов `info.*`/`settings.*`
из APK. Робот Gen4 (D8/D9) серверно не заводится — барьер `unknown_ca` на самом роботе.

## Уточнение по итогам утра 19.09 (реверс APK + живой съём)

**Форматы ответов (сняты из декомпиля MyNeato, дословно, обёртки `{result,data}` НЕТ — Retrofit парсит тело прямо в
модель, все non-null поля обязательны):**
- `info.robot` → `{"serial_number","firmware"}` (обе non-null String).
- `info.wifi` → `{"SSID","MAC","ip"}` (все non-null String).
- `settings.cleaning_options` → `{"force_floorplan": bool}`.
- `settings.robot_language` → `{"language":"en","available_languages":[...]}` (список — обязательно).
- `reminders.get` → `{"max_threshold","min_threshold","threshold"}` (int).
- `info.abilities` → `{"cleaning":"1.2.0","iec_test":null}` (`cleaning`=строка версии, сравнивается с "1.1.0").
- `state.show` → `StateShowResponse` (все nullable, но логика от них зависит): `{state, action, errors,
  available_commands:{start,stop,pause,resume,return_to_base,cancel,extract}, details:{base_type,charge,is_charging,
  is_docked,is_quickboost}, autonomy_states:{started_on_base}}`. **Ключ:** `getRobotState()` резолвит пару
  (state, action, is_docked, is_returning_to_charge) → enum `ROBOT_STATE`. `state:"idle" + action:"" + is_docked:false`
  = `IDLE_OFF_BASE`. **Play — ДВА независимых гейта:** (а) `isPlayEnabled` (`state != null` и robotState ∉ {OFFLINE,
  UNDEFINED}); (б) `play()` шлёт `cleaning.start` только при `available_commands.start == true`.
- `cleaning.start` → `EmptyResponse` (пустой объект `{}`).

**Живой эксперимент (телефон <phone-lan-ip>, орb.server v5 e54d43a на малине):**
- Приложение полностью пришло на локальный сервер (DNS перехвачен по MAC телефона, серт leaf от mitmca).
- После плоских ответов info./settings./state.show приложение **НЕ крашится** и корректно рисует робота: имя
  "Local D9", "Off base", 95%, кнопка Play — активна (чёрная).
- Тап Play → приложение играет ВИДЕО-подсказку "Remove small objects and loose cords before starting a clean"
  (проверено logcat: MediaCodec активен). **`cleaning.start` при этом на сервер не уходит** (лог RasPi5).
  Значит между Play и отправкой команды — внутренняя валидация/UX (метод `startCleaningWithErrorCheck` или ветвь
  "первый запуск робота" — не реверснуто). Ценность: сама команда `{"ability":"cleaning.start"}` уже известна
  из статического реверса APK (`CleaningStartRequest.java:30`, ability по умолчанию), дальнейший съём живьём
  ничего не добавляет к спецификации протокола.

**Артефакты сессии:** сервер `orbital_local_server.py` (мультипорт 443/3443, TLS-handshake логируется, разбор ability),
`neato/DECISIONS.md` (обход cert-pinning робота исчерпан, факт unknown_ca). Публикация обезличенной части — по решению
оператора.

## Онбординг нового робота: линковка идёт МИМО orbital-сервера (эксперимент 19.09 13:23–13:27)

Схема эксперимента: `NEATO_FAKE_ROBOT` убран → `/users/me/robots` возвращает `[]`; приложение → «+» → мастер онбординга
(«Press info button 3s» → BLE-контакт → Wi-Fi credentials HomeNet → Next в 13:25:56); финал — экран
«Your robot couldn't reach our servers» (13:27:25).

**Что снято на orbital-сервере (RasPi5, лог + pcap за окно 13:23:00–13:27:30):**
- От телефона `.148` — **46 GET-запросов и НИ ОДНОГО POST/PUT/DELETE**:
  - `GET /users/me/robots` × 44 (опрос каждые ~6 с, ответ `[]`);
  - `GET /users/me` × 2. Ни `/mobile_devices`, ни `/vendors/*/robots`, ни `messages`.
  - Опрос — по одному keep-alive-соединению (за окно 0 SYN и 0 ClientHello от телефона).
- От робота `.172` — **8 попыток на порт 3443** (SNI `orbital.neatocloud.com`), все `Alert unknown_ca` → RST
  (13:23:19, 13:23:54, затем серия сразу после Next: 13:25:57, :26:00, :05, :14, :33, 13:27:05). Handshake OK — 0.

**Вывод по факту:**
1. Приложение при добавлении нового робота на orbital-сервер **не шлёт команду регистрации**. Линковка идёт
   ПО BLE между приложением и роботом (Wi-Fi credentials + URL облака + secret) + **сам робот регистрируется
   в облаке**. Приложение только ждёт, пока `/users/me/robots` не пополнится новым объектом.
2. Робот регистрацию не завершает — упирается в тот же `unknown_ca` при обращении к orbital на 3443, что и
   при управлении. Приложение по таймауту показывает ошибку.
3. **Серверная сторона (наш orbital) регистрацию нового робота ЗА робота подделать не может** — она приходит
   со стороны робота, а робот не проходит cert-check. Барьер `unknown_ca` виден и с этого угла: без модификации
   робота (свой CA в его trust-store либо отключение verify) новый Gen4 в наше «облако» не завести.
4. Реверс BLE-протокола онбординга (что именно приложение передаёт роботу: URL, secret, serial) — возможен через
   декомпиль APK и/или BLE-снифер (nrf-ble-sniffer), но не решит регистрацию, т.к. упрётся в тот же барьер робота.
5. Косвенное: 6 обрывов handshake от телефона `.148` с alert `certificate unknown` — соединения к другим именам
   `*neatocloud`, которые DNS-подмена не завернула; куда именно (какие хосты) — из наблюдений малины не видно.
