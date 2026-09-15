import asyncio
import json
import sys
import argparse
from bleak import BleakScanner, BleakClient
from bleak.uuids import uuid16_dict, uuid128_dict

# Переконфигурируем stdout/stderr в UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def get_uuid_description(uuid: str) -> str:
    """Получить описание UUID из стандартных словарей bleak."""
    uuid = uuid.lower()
    if uuid in uuid16_dict:
        return uuid16_dict[uuid]
    elif uuid in uuid128_dict:
        return uuid128_dict[uuid]
    else:
        return ""

def format_hex(data: bytes) -> str:
    """Форматирует байты в hex-строку с пробелами."""
    return ' '.join(f'{b:02x}' for b in data)

def format_ascii(data: bytes) -> str:
    """Форматирует байты как ASCII, непечатаемые заменяет на '.'."""
    return ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data)

async def scan_for_device(name_filter: str, timeout: float) -> tuple:
    """Сканирует устройства и возвращает найденное устройство или None."""
    devices = await BleakScanner.discover(timeout=timeout, return_adv=True)
    for address, (device, adv_data) in devices.items():
        if device.name and name_filter.lower() in device.name.lower():
            return device, adv_data
    return None, None

async def main(args):
    # 1. Сканирование
    print(f"Сканирование на {args.scan_timeout} секунд...", file=sys.stderr)
    device, adv_data = await scan_for_device(args.name_filter, args.scan_timeout)
    
    if not device:
        error_msg = {"ok": False, "error": "device not found"}
        print(json.dumps(error_msg), file=sys.stderr)
        sys.exit(2)

    # 2. Вывод информации о найденном устройстве
    print(f"Найдено устройство: {device.address}, имя: {device.name}, RSSI: {adv_data.rssi}", file=sys.stderr)
    print(f"Adv данные: service_uuids={adv_data.service_uuids}, manufacturer_data={adv_data.manufacturer_data}", file=sys.stderr)

    # 3. Подключение
    try:
        async with BleakClient(device.address, timeout=args.connect_timeout) as client:
            print("Подключено успешно.", file=sys.stderr)
            
            # 4. Перечисление GATT-сервисов и характеристик
            services = []
            for service in client.services:
                service_info = {
                    "uuid": service.uuid,
                    "description": get_uuid_description(service.uuid),
                    "characteristics": []
                }
                
                print(f"Сервис: {service.uuid} ({service_info['description']})", file=sys.stderr)
                
                for char in service.characteristics:
                    char_info = {
                        "uuid": char.uuid,
                        "description": get_uuid_description(char.uuid),
                        "properties": char.properties,
                        "descriptors": []
                    }
                    
                    print(f"  Характеристика: {char.uuid} props={char_info['properties']} ({char_info['description']})", file=sys.stderr)
                    
                    for descr in char.descriptors:
                        desc_info = {
                            "uuid": descr.uuid,
                            "handle": descr.handle
                        }
                        if descr.uuid.lower().startswith("00002901"):
                            try:
                                dv = await client.read_gatt_descriptor(descr.handle)
                                desc_info["user_description"] = format_ascii(dv)
                            except Exception as e:
                                desc_info["read_error"] = str(e)
                        char_info["descriptors"].append(desc_info)
                        print(f"    Дескриптор: {descr.uuid} handle={descr.handle}", file=sys.stderr)
                    
                    service_info["characteristics"].append(char_info)
                
                services.append(service_info)

            # 5. Чтение значений характеристик (если нужно)
            if not args.no_read:
                for svc in services:
                    for char in svc["characteristics"]:
                        if "read" in char["properties"]:
                            try:
                                value = await client.read_gatt_char(char["uuid"])
                                char["value_hex"] = format_hex(value)
                                char["value_ascii"] = format_ascii(value)
                            except Exception as e:
                                char["read_error"] = str(e)

            # 6. Формирование итогового JSON
            result = {
                "ok": True,
                "address": device.address,
                "name": device.name,
                "rssi": adv_data.rssi,
                "adv": {
                    "service_uuids": adv_data.service_uuids,
                    "manufacturer_data": {f"{cid:04x}": format_hex(data) for cid, data in adv_data.manufacturer_data.items()}
                },
                "services": services
            }

            # Подсчет количества сервисов и характеристик
            total_chars = sum(len(svc["characteristics"]) for svc in services)

            if args.out:
                with open(args.out, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(json.dumps({"ok": True, "out": args.out, "services": len(services), "chars": total_chars}), file=sys.stdout)
            else:
                print(json.dumps(result, ensure_ascii=False), file=sys.stdout)

    except Exception as e:
        error_msg = {"ok": False, "error": f"connect failed: {str(e)}"}
        print(json.dumps(error_msg), file=sys.stderr)
        sys.exit(3)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GATT-разведка BLE-устройства через bleak")
    parser.add_argument("--address", default="08:3A:88:XX:XX:XX", help="MAC BLE-устройства")
    parser.add_argument("--name-filter", default="Neato", help="Фильтр по имени устройства при сканировании")
    parser.add_argument("--scan-timeout", type=float, default=10.0, help="Таймаут сканирования")
    parser.add_argument("--connect-timeout", type=float, default=20.0, help="Таймаут подключения")
    parser.add_argument("--out", help="Путь для записи JSON-файла")
    parser.add_argument("--no-read", action="store_true", help="Не читать значения характеристик")

    args = parser.parse_args()
    
    # Проверка адреса устройства
    if not args.address:
        print("Ошибка: не указан адрес устройства.", file=sys.stderr)
        sys.exit(1)

    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        print("\nПрервано пользователем.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Неожиданная ошибка: {e}", file=sys.stderr)
        sys.exit(1)
