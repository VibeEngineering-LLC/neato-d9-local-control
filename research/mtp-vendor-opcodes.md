# Neato D9 (Gen4) — вендорские MTP-операции (снято с живого робота, 2026-09-18)

**Находка:** у Neato Gen4 через USB-C MTP есть **5 вендорских MTP-операций сверх чтения `version.txt`**.
Публичного дампа таких опкодов для Gen4 ранее не было (см. `connection-vectors-2026.md`, вектор №2 «не проверено»).

## Результат

```
SELECTED: \\?\usb#vid_1d6b&pid_0100#REDACTED-SN#{REDACTED-GUID}
command HRESULT = 0x00000000
vendor opcode count = 5
VENDOR_OPCODES = 0x95C1, 0x95C2, 0x95C3, 0x95C4, 0x95C5
```

- Диапазон 0x95xx — стандартный MTP vendor-extension (0x9000–0x9FFF).
- **Семантика опкодов пока НЕИЗВЕСТНА** — это только их номера. Что каждый делает (чтение/запись/сервис) — не установлено.

## Как снято

Скрипт `neato/scripts/neato_mtp_probe.py` (read-only): WPD MTP-passthrough,
команда `WPD_COMMAND_MTP_EXT_GET_SUPPORTED_VENDOR_OPCODES` (category
`{4D545058-1A2E-4106-A357-771E0819FC56}`, id 11) через `IPortableDevice::SendCommand`.
GUID выверены по Windows SDK `WpdMtpExtensions.h`/`PortableDevice.h` (tpn/winsdk-10, 10.0.16299.0) — не по памяти.
Драйвер `WUDFWpdMtp` держит устройство → libusb/pyusb напрямую невозможны, поэтому именно WPD-passthrough.

Технические заметки comtypes (чтобы не переоткрывать): `IPortableDeviceManager.GetDevices` — оба параметра
`[in,out]`, работает только с ПРЕДвыделенным массивом (`(c_wchar_p*32)()`, cast в `POINTER`), первый вызов с
NULL-массивом даёт count=0; значение VT_UI4 из `PROPVARIANT` лежит в union-поле
`__MIDL____MIDL_itf_PortableDeviceApi_0001_00000001.ulVal`.

## Проверка достоверности (#SA-3, негативный контроль)

| Запрос | HRESULT | vendor_codes |
|---|---|---|
| id=11 GET_SUPPORTED_VENDOR_OPCODES (валид) | 0x00000000 | **5** |
| id=9999 (несуществующая команда) | 0x80004001 E_NOTIMPL | нет коллекции |
| id=12 EXECUTE_WITHOUT_DATA_PHASE без opcode | 0x80070490 NOT_FOUND | нет коллекции |

Валидный и невалидные пути дают РАЗНЫЙ результат → 5 кодов приходят от драйвера/робота, а не зашиты в код.

## Следующие шаги (read-only, ещё не сделано)

1. `GetDeviceInfo` (MTP op 0x1001) через `WPD_COMMAND_MTP_EXT_EXECUTE_COMMAND_WITH_DATA_TO_READ` (id 13) +
   `READ_DATA` (id 15) + `END_DATA_TRANSFER` (id 17): даст полный `OperationsSupported`, `VendorExtensionID`
   и **`VendorExtensionDesc`** (строка — иногда содержит человекочитаемое имя расширения) и `DevicePropertiesSupported`.
2. `GetDevicePropDesc`/`GetDevicePropValue` для стандартных MTP-свойств (модель, серийник, состояние) — read-only.

## Полный MTP GetDeviceInfo (снят 2026-09-18, скрипт `neato_mtp_deviceinfo.py`, 269 байт датасета)

```
StandardVersion            100          (MTP 1.00)
VendorExtensionID          0x00000006   (= Microsoft MTP)
VendorExtensionDesc        microsoft.com: 1.0; android.com: 1.0;
FunctionalMode             0
Manufacturer               Neato Robotics
Model                      Neato Robot
DeviceVersion              Rev A
SerialNumber               01234567      (MTP-заглушка, не реальный S/N)
DevicePropertiesSupported  0x5001 (BatteryLevel), 0xD402 (DeviceFriendlyName)
EventsSupported            0x4002..0x400C стандартные + 0xC801 (вендорский эвент)
PlaybackFormats            0x3000 (Undefined), 0x3001 (Association/папка)
OperationsSupported (25):
  штатные MTP: 0x1001-0x101B (GetDeviceInfo, Open/CloseSession, Storage*, GetObjectHandles/Info/Object,
               DeleteObject, SendObjectInfo/SendObject, Get/SetDevicePropValue, GetPartialObject)
  MS-расширения: 0x9801-0x9805 (GetObjectPropsSupported/PropDesc/PropValue/SetPropValue/PropList)
  ВЕНДОРСКИЕ Neato: 0x95C1, 0x95C2, 0x95C3, 0x95C4, 0x95C5
```

**Толкование:**
- `VendorExtensionDesc` объявляет только `microsoft.com` и `android.com` — то есть база стека это **Android MTP
  gadget** (штатный для Linux). **Имена/семантику 0x95C1-0x95C5 Neato в DeviceInfo НЕ декларирует** — текстового
  описания вендор-расширения нет, только microsoft/android. Значит смысл пяти опкодов из устройства не вычитать;
  остаётся реверс приложения MyNeato/прошивки либо осторожный опрос (см. ниже).
- Наличие `SendObjectInfo`/`SendObject`/`DeleteObject` в списке — это механика загрузки файла в `SW Update`
  (приём подписанной прошивки), а не управление уборкой.
- `DevicePropertiesSupported` = **0x5001 BatteryLevel** (читается `GetDevicePropValue`, read-only, безопасно) и
  0xD402 DeviceFriendlyName. Команд движения/уборки среди device-properties нет.
- `0xC801` в EventsSupported — вендорский MTP-эвент (робот может асинхронно уведомлять); назначение не установлено.

**Промежуточный вывод по вектору №2:** канал вендор-команд реально есть (5 опкодов + 1 эвент), но **самоописания
робот не даёт**. Без знания формата параметров 0x95Cx управлять через них нельзя, а вызывать вслепую опасно.

### Проверка чтения свойств (2026-09-18, read-only)

Механизм `GetDevicePropDesc`/`GetDevicePropValue` (дата-фаза) работает — подтверждено на осмысленном значении:
- `0xD402 DeviceFriendlyName` → `"Neato Robot"` (декодер дата-фазы верен).
- `0x5001 BatteryLevel` → PropDesc: DataType `0x0004` (UINT16), GetSet=0 (read-only), factory/current в дескрипторе = 0;
  GetDevicePropValue вернул `00 80` = UINT16 `0x8000` (32768) — **не проценты, заглушка** (как SerialNumber `01234567`).
- Вывод: осмысленной телеметрии (заряд/статус/уборка) штатные MTP-свойства Neato НЕ отдают. Всё полезное, если есть,
  спрятано за вендор-опкодами 0x95C1–0x95C5 → нужен реверс приложения MyNeato для их семантики.

## ⚠ Безопасность

Опкоды 0x95C1–0x95C5 — **неизвестной семантики**. Любой из них МОЖЕТ быть записью/сбросом/сервисной операцией.
**Вслепую не вызывать.** Сначала — только чтение метаданных (GetDeviceInfo/VendorExtensionDesc, п.1) и анализ,
затем разбор каждого опкода отдельно, с согласия оператора и пониманием дата-фазы (нет/чтение/запись).
