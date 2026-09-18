# USB-C разведка D9 — этап 1 (только чтение), 2026-09-18

Робот: D9, подключён USB-C к HOST. Всё ниже — вывод команд, только чтение; в робот ничего не записывалось.

## Что Windows видит (Get-PnpDevice / Get-PnpDeviceProperty)

- Одно устройство, класс WPD, «Neato Robot», `USB\VID_1D6B&PID_0100\<серийник робота>` — серийник USB = S/N с шильдика.
- HardwareIds: `USB\VID_1D6B&PID_0100&REV_0504`; CompatibleIds: `USB\Class_06&SubClass_01&Prot_01` (Still Image / MTP).
- Manufacturer «Neato Robotics», драйвер `WUDFWpdMtp` (`wpdmtp.inf`). Детей нет — устройство **не составное** (нет `MI_xx`).

## Дескрипторы (`neato\scripts\usb_descriptors.py`, pyusb + libusb, без открытия устройства)

```
DEVICE 1d6b:0100 bcdUSB=0200 bcdDevice=0504 class=00/00/00 numConfigs=1
  CONFIG value=1 numIf=1 attr=80 maxPower=60
    IF 0 alt=0 class=06/01/01 eps=3
      EP 81 attr=02 maxPkt=512   (bulk IN)
      EP 01 attr=02 maxPkt=512   (bulk OUT)
      EP 82 attr=03 maxPkt=28    (interrupt IN, события MTP)
```
Строковые дескрипторы через libusb не читаются (устройство занято драйвером MTP) — их дал Windows выше.

**Вывод:** одна конфигурация, один интерфейс, только MTP. Скрытых последовательного/сетевого/ADB-интерфейсов
нет — утверждение с reddit («ADB/serial/SSH/RNDIS по USB выключены») **подтверждено на нашем D9**.
`VID 1D6B` = Linux Foundation, `bcdDevice 0x0504` — Linux USB gadget подставляет версию ядра: **ядро 5.4**
(совпадает с ранее известным «Yocto, ядро 5.4»).

## Содержимое MTP (Shell.Application, обход до глубины 6)

Только `SW Update\version.txt`. Проводник показывает размер 0 и дату 1899 — файл **генерируется на лету**
(реальный размер при копировании 112 байт):

```
Image version: 1.7.0-2933_10060147_cfae4f98
Firmware version: 1.7.0-2933_10060147_cfae4f98 LPC firmware started
```
- `cfae4f98` похоже на короткий git-хеш сборки; `10060147` — идентификатор сборки (смысл не установлен).
- «LPC firmware started» — в роботе есть второй контроллер (вероятно NXP LPC — моторы/датчики) рядом с i.MX;
  его прошивка — часть того же образа. Толкование «LPC = NXP LPC» — гипотеза по названию, не проверено.

## Не сделано / следующие шаги

- Список поддерживаемых MTP-операций (`GetDeviceInfo` → OperationsSupported, вендорские 0x9xxx) — не снят,
  нужен WPD/libmtp-клиент. Это последняя read-only поверхность USB-стороны.
- Этап 2 — флешка в робот (host-режим, `UIMGR_STATE_USB_LOGCOPY`): видено у автора `algaen/neato-connected-D8`
  на прошивке 3.2.0/4.3.5, на Gen4 1.7.0 не проверено. Нужны флешка FAT32 + OTG USB-C→USB-A.
