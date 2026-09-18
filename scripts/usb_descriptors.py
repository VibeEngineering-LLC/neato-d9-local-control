"""Read-only dump of USB descriptors (all configurations/interfaces/endpoints). Usage: usb_descriptors.py [VID PID] (hex)."""
import sys, usb.core, usb.util, libusb_package
vid, pid = (int(a, 16) for a in sys.argv[1:3]) if len(sys.argv) > 2 else (0x1D6B, 0x0100)
be = libusb_package.get_libusb1_backend()
for d in usb.core.find(find_all=True, idVendor=vid, idProduct=pid, backend=be):
    print(f"DEVICE {d.idVendor:04x}:{d.idProduct:04x} bcdUSB={d.bcdUSB:04x} bcdDevice={d.bcdDevice:04x} "
          f"class={d.bDeviceClass:02x}/{d.bDeviceSubClass:02x}/{d.bDeviceProtocol:02x} numConfigs={d.bNumConfigurations}")
    for s in ("iManufacturer", "iProduct", "iSerialNumber"):
        try: print(f"  {s}: {usb.util.get_string(d, getattr(d, s))}")
        except Exception as e: print(f"  {s}: <{type(e).__name__}>")
    for i in range(d.bNumConfigurations):
        try: c = d.configurations()[i]
        except Exception as e: print(f"  CONFIG[{i}] <{type(e).__name__}: {e}>"); continue
        print(f"  CONFIG value={c.bConfigurationValue} numIf={c.bNumInterfaces} attr={c.bmAttributes:02x} maxPower={c.bMaxPower}")
        for itf in c:
            print(f"    IF {itf.bInterfaceNumber} alt={itf.bAlternateSetting} class={itf.bInterfaceClass:02x}/"
                  f"{itf.bInterfaceSubClass:02x}/{itf.bInterfaceProtocol:02x} eps={itf.bNumEndpoints}")
            for ep in itf:
                print(f"      EP {ep.bEndpointAddress:02x} attr={ep.bmAttributes:02x} maxPkt={ep.wMaxPacketSize}")
