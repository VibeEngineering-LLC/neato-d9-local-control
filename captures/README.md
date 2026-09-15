# Захваты BLE

Сами pcap-файлы лежат НЕ здесь, а на `C:\Users\1\AppData\Local\nrf-ble-sniffer\captures\` — по умолчанию
скилл `nrf-ble-sniffer` пишет туда, чтобы MAC-адреса чужих устройств (соседи) не попадали в Google Drive.

## Реестр захватов по Neato (2026-09-15)

| Файл (на C:) | Что | Ключевое |
|---|---|---|
| `ble_20260915_180032_neato_baseline.pcap` | эфир, пылесос спит на базе | Neato по BLE не рекламируется |
| `ble_20260915_180710_neato_awake.pcap` | эфир, пылесос разбужен | `08:3a:88:XX:XX:XX` «Neato Robot Services», connectable, RSSI −46 |

Разбор: `PYTHONIOENCODING=utf-8 python C:\Users\1\.claude\skills\nrf-ble-sniffer\scripts\ble_decode.py <pcap> --mode summary`.

Если понадобится сохранить конкретный захват в проект надолго — копировать сюда только после
обезличивания чужих адресов, либо хранить с пометкой «не публиковать».
