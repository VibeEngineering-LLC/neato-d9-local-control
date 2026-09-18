# MyNeato 1.6.2 — реверс-инжиниринг: путь к локальному управлению

**Приложение:** `com.neatorobotics.android_myneato` 1.6.2 (jadx-декомпилят), роботы Neato D8/D9/D10 (Gen4).
**Задача:** установить по коду, есть ли путь управлять роботом локально (LAN/BLE) после отключения облака Neato 30.11.2025. Легальный интероп-анализ собственного устройства.
**Дата анализа:** 2026-09-18.
**Корень исходников** (все пути `file:line` ниже — относительно него):
`<decompiled>/sources` (jadx-выгрузка base APK)

---

## BLE-протокол

### Таблица UUID (объявлены в `com/neatorobotics/android_myneato/bluetooth/RobotPeripheral.java:103-141`)

| Константа | UUID | Тип | Операция в приложении | Назначение |
|---|---|---|---|---|
| `ROBOT_INFORMATION_SERVICE_UUID` | `e49212ba-757f-4856-b504-6d21f138cc97` | service | — | GATT-сервис «информация робота» (контейнер для трёх характеристик ниже) |
| `CONNECTIVITY_STATE_UUID` | `2e5a6eb1-129c-487c-a989-7aff4a120811` | characteristic | **read** (`getRobotConnectivityState`, `BluetoothRobotLinkingService.java:131`) | статус Wi-Fi-подключения робота (int) |
| `PUBLIC_KEY_STRING_UUID` | `c5af26f1-fec7-404b-bc53-c22c82c8fe07` | characteristic | **read** (`getRobotPublicKey`, `BluetoothRobotLinkingService.java:111`) | RSA-публичный ключ робота (PEM) для шифрования Wi-Fi-пароля |
| `INFO_BUTTON_PRESSED_CHARACTERISTIC` | `85a58c74-db2c-43a3-99a0-f5098b348723` | characteristic | **read** (`getRobotInfoButtonState`, `BluetoothRobotLinkingService.java:152`) | состояние физической кнопки (подтверждение владения при онбординге) |
| `WIFI_MANAGER_SERVICE_UUID` | `f3327472-b16a-4fa1-a5f0-cf04955349d6` | service | — | GATT-сервис «Wi-Fi-менеджер» |
| `WIFI_NETWORK_SCANNER_UUID` | `729709f9-1713-4dd5-9d1b-e4b0e8c189b4` | characteristic | **write+read** (пейджинг, `getRobotVisibleWifiNetworks`, `BluetoothRobotLinkingService.java:221`) | список видимых роботом Wi-Fi-сетей (JSON, читается кусками) |
| `LINKING_MANAGER_SERVICE_UUID` | `708b61e9-86de-421b-b393-78eb7c7af5f6` | service | — | GATT-сервис «linking-менеджер» |
| `LINKING_UNCHUNKED_UUID` | `f5970d6f-5222-4763-8e67-a9abf67e55f9` | characteristic | **write+read** | приём linking-запроса одним куском + чтение linking-состояния |
| `LINKING_CHUNKED_UUID` | `f5970d6f-5222-4763-8e67-a9abf67e55f0` | characteristic | **write** (chunked, `BleCommunicationManager.java:293`) | приём linking-запроса по частям (splitter) |
| `DEVICE_INFORMATION_SERVICE_UUID` | `0000180a-…` (стандартный DIS) | service | — | стандартный Device Information |
| `SERIAL_UUID` | `00002a25-…` (стандартный Serial Number String) | characteristic | **read** (`getRobotSerialNumber`, `BluetoothRobotLinkingService.java:194`) | серийный номер робота |
| `OTA_SERVICE_UUID` | `030690ae-c3e9-4c93-9a14-ff6c9405b45f` | service | — | GATT-сервис OTA |
| `OTA_STATE_UUID` | `60e55ded-3b2a-4630-a739-55dde11ed429` | characteristic | **read** (`getOTAState`, `BluetoothRobotOTAService.java:30`) | текстовое состояние OTA (только чтение; сама прошивка по этому каналу НЕ передаётся) |

Обнаружение характеристик и жёсткое требование их наличия — `NeatoObservableBleManager.java:29-45` (`isRequiredServiceSupported`): при отсутствии любой из перечисленных характеристик подключение отклоняется. Другого набора характеристик приложение не знает.

### Перечень ВСЕХ BLE-write операций

В пакете `bluetooth` есть ровно один примитив записи — `BleCommunicationManager.send()` (`BleCommunicationManager.java:269-303`, через `NeatoObservableBleManager.writeCharacteristic`). Его вызывают всего в двух местах:

1. **`BleCommunicationManager.getFromOffset` → `send` (`BleCommunicationManager.java:132`).** Пишет в характеристику **число-смещение** (`Data.from("$startIndex")`) — это механизм постраничного ЧТЕНИЯ длинного значения (используется для вычитывания JSON списка Wi-Fi-сетей из `WIFI_NETWORK_SCANNER`, `getNextPiece`/`getLongString`). Это не команда роботу, а служебный курсор чтения.
2. **`BluetoothRobotLinkingService.sendLinkingRequest` → `BleCommunicationManager.sendObject` (`BluetoothRobotLinkingService.java:400`).** Пишет в `LINKING_*`-характеристику JSON-объект `RobotLinkRequest` (Wi-Fi-креды, см. ниже).

Грепом подтверждено: во всём пакете `bluetooth` больше нет вызовов `send`/`sendObject`/`writeCharacteristic`, и нет ни одной строки-команды вида `cleaning.*` / `navigation.*` (эти литералы встречаются только в облачном слое `retrofit`, см. следующую секцию).

### ВЕРДИКТ по BLE: онбординг + чтение статуса, НЕ управление

BLE используется **исключительно для первичной настройки (онбординг/linking)**: приложение читает публичный ключ, серийник, статус кнопки и подключения, вычитывает список Wi-Fi-сетей и записывает единственный полезный объект — `RobotLinkRequest` с зашифрованным Wi-Fi-паролем. **Ни одной команды управления роботом (старт/стоп/пауза/док/зоны/поехать) по BLE не отправляется.** OTA-сервис по BLE только читает состояние; передачи прошивки по BLE в коде нет.

### `RobotLinkRequest` — единственная полезная BLE-запись

`com/neatorobotics/android_myneato/bluetooth/objects/RobotLinkRequest.java:14-49`. Поля (Gson, только `@Expose`):
- `ssid` — SSID домашней сети;
- `ssid_encrypted_password` (`encryptedPassword`) — Wi-Fi-пароль, зашифрованный RSA-ключом робота;
- `user_id` — id пользователя (привязка робота к облачному аккаунту);
- `environment` — окружение;
- `timezone` — таймзона.

Поле `password` (сырой пароль) помечено без `@Expose` и в JSON НЕ уходит — по BLE передаётся только зашифрованное значение (`sendObject` использует `excludeFieldsWithoutExposeAnnotation`, `BleCommunicationManager.java:428`).

Смысл `RobotLinkRequest`: сказать роботу, к какой Wi-Fi-сети подключиться и к какому облачному аккаунту (`user_id`) привязаться. Это — регистрация в облаке, а не управление.

### EncryptionService — RSA (не AES)

`com/neatorobotics/android_myneato/bluetooth/EncryptionService.java`:
- Криптография — **RSA**, преобразование `Cipher.getInstance("RSA/NONE/PKCS1Padding")`, `init(ENCRYPT_MODE, publicKey)` (`EncryptionService.java:20-24`).
- Ключ строится из PEM-строки: срезаются заголовки `-----BEGIN/END PUBLIC KEY-----` и переводы строк, `Base64.decode`, `KeyFactory.getInstance("RSA").generatePublic(X509EncodedKeySpec(...))` (`EncryptionService.java:26-28`).
- `encrypt(message, publicKeyString)`: шифрует UTF-8-байты сообщения RSA-ключом, результат — Base64 (`EncryptionService.java:31-43`).

**Что шифруется:** только Wi-Fi-пароль. В `sendLinkingRequest` (`BluetoothRobotLinkingService.java:387-390`) вызывается `encryptionService.encrypt(robotLinkRequest.getPassword(), robotPublicKey)`, результат кладётся в `encryptedPassword`. **Подписи (signing) нет — только шифрование.** AES в этом слое не используется.

**Зачем нужен `Robot_Public_RSA_Key`:** робот в режиме онбординга публикует свой RSA-public-key через `PUBLIC_KEY_STRING` characteristic; телефон читает его и шифрует Wi-Fi-пароль, чтобы пароль домашней сети не передавался по BLE открытым текстом. Приватный ключ остаётся в роботе — расшифровать пароль может только сам робот. Аутентификации робота перед телефоном (взаимной) это не даёт: подтверждение владения делается физической кнопкой (`INFO_BUTTON_PRESSED`).

---

## Облачный API (Orbital REST)

### Базовый хост и транспорт

- Все Retrofit-клиенты строятся с `baseUrl = getResources().getString(R.string.orbital_endpoint)` — `com/neatorobotics/android_myneato/koin/RetrofitModuleKt.java:67,84,104,120,136,152,168,184`.
- **Точное значение хоста установить не удалось**: строка `R.string.orbital_endpoint` лежит в ресурсах (`res/values/strings.xml`), а в предоставленном декомпиляте присутствуют только Java-исходники (`sources/`), ресурсы не извлечены. В коде base-URL хардкодом не встречается (грепом по `sources` найдены только маркетинговые ссылки `neatorobotics.com`, не API-хост).
- TLS — только `ConnectionSpec.MODERN_TLS` (`OrbitalRetrofitAPI.java:93`); DNS-lookup кастомный (`OrbitalRetrofitAPI$build$client$1`), но по сути `Dns.SYSTEM`.

### Аутентификация и заголовки

Интерсептор `OrbitalRetrofitAPI$build$$inlined$addInterceptor$1.java` добавляет на каждый запрос:
- `Content-type: application/json`
- `Accept: application/vnd.neato.orbital-http.v1+json`
- `mobile-app-version: <BuildConfig.VERSION_NAME>`
- `X-NEATO-CLIENT-PLATFORM: Android`
- `X-NEATO-CLIENT-BUILD: 270`
- `Authorization: Token <token>` — добавляется только если токен непуст.

**Механизм — не OAuth, а простой сессионный токен** (`Authorization: Token …`). Токен получается логином: `POST /vendors/neato/sessions` c полями `email`, `password` → `LoginResponse{ token }` (`OrbitalAPI.java:55-56`; `LoginResponse.java:12-38`). Токен хранится в `UserRepository.getCurrentUserToken()` и читается интерсептором через `OrbitalRetrofitAPI.getAuthorizationToken()` (`OrbitalRetrofitAPI.java:99-101`).

### Ключевой паттерн: команды робота через единый эндпоинт «messages»

Все команды роботу (уборка, навигация, настройки, расписание, инфо, статус) идут одним HTTP-эндпоинтом:

```
POST /vendors/{vendor}/robots/{robotSerialNumber}/messages
Body (JSON): { "ability": "<имя_команды>", ...доп.поля }
```

Различаются только значение `ability` и тип тела. Базовое тело — `Command{ ability }` (`com/neatorobotics/android_myneato/retrofit/objects/request/Command.java:9-18`).

### Таблица эндпоинтов

**Команды/статус робота — `OrbitalRobotAPI.java`** (все `POST …/messages`, если не указано иное):

| Метод | ability / путь | Тело | Ответ | Назначение |
|---|---|---|---|---|
| `cleaningStart` | `cleaning.start` | `CleaningStartRequest` | `EmptyResponse` | старт уборки |
| `emptyResponseBaseCall` (pause) | `cleaning.pause` | `Command` | `EmptyResponse` | пауза (`RobotCleaningHTTPService.java:248`) |
| `emptyResponseBaseCall` (resume) | `cleaning.resume` | `Command` | `EmptyResponse` | продолжить (`:316`) |
| `emptyResponseBaseCall` (cancel) | `cleaning.cancel` | `Command` | `EmptyResponse` | стоп/отмена (`:97`) |
| `emptyResponseBaseCall` (return) | `navigation.return_to_base` | `Command` | `EmptyResponse` | вернуться на базу (`:384`) |
| `cleaningShow` | `cleaning.show` | `Command` | `CleaningShowResponse` | детали текущей уборки (`:176`) |
| `stateShow` | `state.show` | `Command` | `StateShowResponse` | полное состояние робота |
| `locate` | `utilities.find_me` | `Command` | `Unit` | «найти робота» (звук) |
| `infoRobot` | `info.robot` | `Command` | `InfoRobotResponse` | инфо о роботе |
| `infoWifi` | `info.wifi` | `Command` | `InfoWifiResponse` | инфо о Wi-Fi робота |
| `infoAbilities` | `info.abilities` | `Command` | `InfoAbilitiesResponse` | список поддерживаемых команд |
| `getCleaningOptions` / `saveCleaningOption` | `settings.cleaning_options` / `settings.set_cleaning_options` | `Command`/`CleaningOptionRequest` | — | опции уборки |
| `getRobotLanguage` / `setRobotLanguage` | `settings.robot_language` / `settings.set_robot_language` | `Command`/`SetRobotLanguageRequest` | — | язык |
| `lastState` (GET) | `GET /robots/{robotId}/last_state` | — | `LastStateResponse` | последнее известное состояние |
| `infoFeatures` (GET) | `GET /robots/{robotId}/features` | — | `RobotFeatures` | возможности |
| `getReminders`/`setReminderRead` | `GET/PUT /robots/{robotId}/reminders` | — | — | напоминания |

**Уборка (start) — тело `CleaningStartRequest`** (`request/CleaningStartRequest.java:13-29`):
```json
{ "ability": "cleaning.start",     // дефолт, ctor: (i&4)!=0 ? "cleaning.start"
  "force_floorplan": false,
  "runs": [ CleaningRun, ... ] }
```
`CleaningRun` (`request/CleaningRun.java`): `{ settings: CleaningSettings, map: CleaningMap }`.
`CleaningSettings` (`request/CleaningSettings.java:15-18`): `{ "mode": CleaningMode, "navigation_mode": NavigationMode }`.
`CleaningMap` (`request/CleaningMap.java:16-22`): поля с `@SerializedName` `rank_id`, `track_id`, `nogo_enabled` (id карты/зоны и флаг no-go).

**Остальные Orbital-интерфейсы:**
- `OrbitalCleanCenterAPI.java` — `settings.set_autoextract` (`AutoExtractionRequest`), `extraction.start` (`ExtractionHTTPService`) — авто-опустошение базы Clean Center.
- `OrbitalRoutineAPI.java` — `scheduling.add/delete/show/update` (`CommandRoutine`) — расписания.
- `OrbitalReminderAPI.java` — таймер-напоминания через `…/messages`.
- `OrbitalIECModeAPI.java` — `settings.set_iec_test_params` + тестовый режим (сервисный).
- `OrbitalMapAPI.java` — карты/зоны/этажи, работают по **другим** REST-путям (не через `messages`): `GET/POST/PUT/DELETE /maps/floorplans/…`, `GET /robots/{robotId}/cleaningmaps…`, `GET /robots/{robot_id}/floorplans`. Отдают/правят floorplan'ы, зоны, историю уборок и карты.
- `OrbitalSpotlightAPI.java` — маркетинговые сообщения (`/spotlight_messages`).
- `OrbitalAPI.java` — аккаунт: `login`, `register`, `usersMe`, `meRobots` (`GET /users/me/robots`), `updateRobot`, `removeRobot` (unlink), нотификации, смена пароля/почты.

### Опрос состояния — из облака

`polling/PollingServiceImpl.java`: `POLL_TIME = 6000` мс (`:9`), каждые 6 с вызывает `robotRepository.syncRobots` → `RobotRemoteDataSourceImpl` (`utils/configuration/RobotRemoteDataSourceImpl.java:267-270` — `state.show`; `:200` — `lastState`). То есть статус робота и карты приложение тянет **из облака по REST**, локального канала статуса нет.

---

## Вывод для локального управления

**(а) Локального (LAN/BLE) пути команд в приложении НЕТ.** Установлено фактами:
- Все команды робота (`cleaning.start/pause/resume/cancel`, `navigation.return_to_base`, `state.show`, `utilities.find_me`, `settings.*`, `scheduling.*`) отправляются **только** облачным REST-эндпоинтом `POST /vendors/{vendor}/robots/{serial}/messages` (`OrbitalRobotAPI.java:49-101`, `RobotCleaningHTTPService.java`).
- BLE в приложении реализует только онбординг (передача Wi-Fi-кредов, чтение публичного ключа/серийника/статуса) и чтение OTA-состояния; ни одной управляющей записи по BLE нет (см. «ВЕРДИКТ по BLE»).
- Статус и карты тоже идут через облако (polling `state.show`/`last_state` каждые 6 с).

Следовательно, робот D8/D9/D10 в штатной прошивке принимает команды по HTTPS от облака Neato (Nucleo/Orbital), а телефон общается только с облаком. С отключением облака 30.11.2025 штатное приложение управлять роботом не может, и **обойти это только средствами данного APK нельзя** — в нём нет клиента для прямого соединения с роботом по LAN.

**(б) Что обязан реализовать сервер-замена облака** (подход Vacuula — DNS/hosts-подмена хоста `orbital_endpoint` на свой сервер + собственный TLS-сертификат, которому доверяет робот; здесь речь о том, что сервер должен отвечать телефону — управление роботом со стороны сервера в этом APK не видно):

Минимально, чтобы штатное приложение заработало против своего сервера, тот должен реализовать:
1. **Аутентификация:** `POST /vendors/neato/sessions {email,password}` → `{ "token": "…" }`; далее принимать заголовок `Authorization: Token <token>`. Заголовки `Accept: application/vnd.neato.orbital-http.v1+json`, `X-NEATO-CLIENT-PLATFORM/BUILD` — приложение шлёт их само, серверу достаточно не отвергать.
2. **Список роботов:** `GET /users/me/robots` → `UserRobotListResponse` (serial, vendor, имя, features).
3. **Состояние:** `POST /vendors/{vendor}/robots/{serial}/messages` с `{"ability":"state.show"}` → `StateShowResponse`; `GET /robots/{robotId}/last_state` → `LastStateResponse`; `GET /robots/{robotId}/features` → `RobotFeatures`.
4. **Команды уборки:** тот же `…/messages` с `ability` = `cleaning.start` (тело `CleaningStartRequest{runs,force_floorplan}`), `cleaning.pause`, `cleaning.resume`, `cleaning.cancel`, `navigation.return_to_base`, `cleaning.show`.
5. **Прочее по потребности:** `utilities.find_me`, `info.robot/wifi/abilities`, `settings.*` (опции/язык/autoextract), `scheduling.*`, карты `/maps/floorplans/…` и `/robots/{id}/cleaningmaps`.
6. **Аккаунт/онбординг:** `register`, `usersMe`, нотификации — если нужен полный флоу.

**Критично (не решается этим APK):** сервер-замена лишь удовлетворяет ТЕЛЕФОН. Чтобы РОБОТ реально выполнял команды, он должен, в свою очередь, установить исходящее соединение с этим же сервером (робот сам ходит в облако, а `…/messages` — это, по имени `messages` и паттерну, постановка сообщения в очередь для робота). Протокол «сервер ↔ робот» в клиентском APK отсутствует и **из данного декомпилята не выводится** — его нужно снимать отдельно (трафик самого робота / его прошивка), либо полагаться на наработки сообщества. Подмена хоста возможна потому, что base-URL берётся из ресурса и TLS-pinning в коде не обнаружен (только `MODERN_TLS`, кастомный `Dns` без pinning), но это требует, чтобы робот доверял серверному сертификату — что тоже вне зоны APK.

---

## Не удалось установить

- **Точный облачный хост** (`R.string.orbital_endpoint`): значение в `res/values/strings.xml`, ресурсы в декомпилят не попали (есть только `sources/`). В коде хардкодом хоста нет. Нужно извлечь ресурсы APK (`apktool`/`aapt dump strings`) для точного домена.
- **Протокол «сервер ↔ робот»** (как облако доставляет `…/messages` роботу, транспорт, формат): в клиентском APK не представлен; выводить из клиента нельзя.
- **Наличие/отсутствие TLS-pinning на стороне робота:** в APK телефона pinning не найден (только `ConnectionSpec.MODERN_TLS`), но поведение робота по проверке сертификата сервера по клиенту не определяется.
- **Точное соответствие полей `CleaningMap`** (`rank_id`/`track_id` ↔ конструкторные `mapId`/`zoneId`): порядок присваивания из декомпилята однозначно не читается; подтверждены сами `@SerializedName` (`rank_id`, `track_id`, `nogo_enabled`).

---

## LESSONS

1. Ожидал, что base-URL — строковый литерал в коде; оказалось — `R.string.orbital_endpoint` из ресурсов. Обход: при RE Android для хостов сразу извлекать `res/values/strings.xml` (`apktool`), а не только jadx-`sources`.
2. Ожидал по-эндпоинтную REST-схему команд; оказалось — единый `POST …/messages` с дискриминатором `ability`. Обход: искать не пути, а строковые литералы команд (`grep "\"[a-z]+\.[a-z_]+\""`) и тела `@Body`.
