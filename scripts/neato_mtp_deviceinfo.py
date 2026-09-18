"""Neato Gen4: read full MTP GetDeviceInfo (op 0x1001) via WPD MTP-passthrough (read-only).
Prints VendorExtensionID/Desc, OperationsSupported, DevicePropertiesSupported and identity strings.
GUIDs verified vs Windows SDK WpdMtpExtensions.h / PortableDevice.h. Read-only: only GetDeviceInfo, no writes.
READ_DATA requires a caller-allocated TRANSFER_DATA buffer in the INPUT params (VT_VECTOR|VT_UI1)."""
import sys, ctypes, struct
from ctypes import byref, c_ulong, c_ubyte, c_wchar_p, POINTER, cast
import comtypes.client as cc
from comtypes import GUID

port = cc.GetModule("PortableDeviceApi.dll")
types = cc.GetModule("PortableDeviceTypes.dll")
CV = "{4D545058-1A2E-4106-A357-771E0819FC56}"; CC = "{F0422A9C-5DC8-4440-B5BD-5DF28835658A}"
def pk(f, p):
    k = port._tagpropertykey(); k.fmtid = GUID(f); k.pid = p; return k

def dev_open():
    mgr = cc.CreateObject(port.PortableDeviceManager, interface=port.IPortableDeviceManager); mgr.RefreshDeviceList()
    arr = (c_wchar_p * 32)(); r = mgr.GetDevices(cast(arr, POINTER(c_wchar_p)), 32)
    did = next(arr[i] for i in range(r[1]) if arr[i] and "vid_1d6b" in arr[i].lower())
    dev = cc.CreateObject(port.PortableDevice, interface=port.IPortableDevice)
    dev.Open(did, cc.CreateObject(types.PortableDeviceValues, interface=port.IPortableDeviceValues))
    return dev

def vals():
    return cc.CreateObject(types.PortableDeviceValues, interface=port.IPortableDeviceValues)

def get_device_info(dev, opcode=0x1001):
    p = vals()
    empty = cc.CreateObject(types.PortableDevicePropVariantCollection, interface=port.IPortableDevicePropVariantCollection)
    p.SetGuidValue(pk(CC, 1001), GUID(CV)); p.SetUnsignedIntegerValue(pk(CC, 1002), 13)  # WITH_DATA_TO_READ
    p.SetUnsignedIntegerValue(pk(CV, 1001), opcode)
    p.SetIPortableDevicePropVariantCollectionValue(pk(CV, 1002), empty)
    res = dev.SendCommand(0, p)
    total = res.GetUnsignedIntegerValue(pk(CV, 1007))
    ctx = res.GetStringValue(pk(CV, 1006))
    data = b""
    try:
        while len(data) < total:
            want = total - len(data)
            buf = (c_ubyte * want)()
            rq = vals()
            rq.SetGuidValue(pk(CC, 1001), GUID(CV)); rq.SetUnsignedIntegerValue(pk(CC, 1002), 15)  # READ_DATA
            rq.SetStringValue(pk(CV, 1006), ctx)
            rq.SetUnsignedIntegerValue(pk(CV, 1008), want)
            rq.SetBufferValue(pk(CV, 1012), cast(buf, POINTER(c_ubyte)), want)  # input TRANSFER_DATA buffer
            rr = dev.SendCommand(0, rq)
            nread = rr.GetUnsignedIntegerValue(pk(CV, 1009))
            bufptr, size = rr.GetBufferValue(pk(CV, 1012))
            data += ctypes.string_at(bufptr, size if size else nread)
            if not nread:
                break
    finally:
        fin = vals()
        fin.SetGuidValue(pk(CC, 1001), GUID(CV)); fin.SetUnsignedIntegerValue(pk(CC, 1002), 17)  # END_DATA_TRANSFER
        fin.SetStringValue(pk(CV, 1006), ctx)
        try: dev.SendCommand(0, fin)
        except Exception: pass
    return data

class R:
    def __init__(s, b): s.b = b; s.o = 0
    def u16(s): v = struct.unpack_from("<H", s.b, s.o)[0]; s.o += 2; return v
    def u32(s): v = struct.unpack_from("<I", s.b, s.o)[0]; s.o += 4; return v
    def mstr(s):
        n = s.b[s.o]; s.o += 1
        if n == 0: return ""
        raw = s.b[s.o:s.o + n * 2]; s.o += n * 2
        return raw.decode("utf-16-le").rstrip("\x00")
    def au16(s):
        c = s.u32(); return [s.u16() for _ in range(c)]

def parse(data):
    r = R(data); i = {}
    i["StandardVersion"] = r.u16()
    i["VendorExtensionID"] = "0x%08X" % r.u32()
    i["VendorExtensionVersion"] = r.u16()
    i["VendorExtensionDesc"] = r.mstr()
    i["FunctionalMode"] = r.u16()
    i["OperationsSupported"] = ["0x%04X" % x for x in r.au16()]
    i["EventsSupported"] = ["0x%04X" % x for x in r.au16()]
    i["DevicePropertiesSupported"] = ["0x%04X" % x for x in r.au16()]
    i["CaptureFormats"] = ["0x%04X" % x for x in r.au16()]
    i["PlaybackFormats"] = ["0x%04X" % x for x in r.au16()]
    i["Manufacturer"] = r.mstr()
    i["Model"] = r.mstr()
    i["DeviceVersion"] = r.mstr()
    i["SerialNumber"] = r.mstr()
    return i

def main():
    dev = dev_open()
    data = get_device_info(dev)
    print("raw dataset bytes:", len(data))
    for k, v in parse(data).items():
        print("%-26s %s" % (k, v))
    dev.Close()

if __name__ == "__main__":
    main()
