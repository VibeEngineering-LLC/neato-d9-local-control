"""Neato Gen4 MTP probe via WPD MTP-passthrough (read-only).
Queries the connected Neato robot for its vendor-extended MTP operation codes
(WPD_COMMAND_MTP_EXT_GET_SUPPORTED_VENDOR_OPCODES, id 11).
GUIDs verified against Windows SDK WpdMtpExtensions.h / PortableDevice.h (tpn/winsdk-10, 10.0.16299.0).
Read-only: sends only the query command; no writes to the device."""
import sys, ctypes
from ctypes import byref, c_ulong, c_wchar_p, POINTER, cast
import comtypes.client as cc
from comtypes import GUID

port = cc.GetModule("PortableDeviceApi.dll")
types = cc.GetModule("PortableDeviceTypes.dll")

CAT_VENDOR = "{4D545058-1A2E-4106-A357-771E0819FC56}"
CAT_COMMON = "{F0422A9C-5DC8-4440-B5BD-5DF28835658A}"

def pk(fmtid, pid):
    k = port._tagpropertykey(); k.fmtid = GUID(fmtid); k.pid = pid; return k

CMD_CATEGORY = pk(CAT_COMMON, 1001)
CMD_ID       = pk(CAT_COMMON, 1002)
CMD_HRESULT  = pk(CAT_COMMON, 1003)
VENDOR_CODES = pk(CAT_VENDOR, 1005)
ID_GET_VENDOR_OPCODES = 11

def pv_uint(pv):
    for name, _t in pv._fields_:
        if name.startswith("__MIDL"):
            return int(getattr(pv, name).ulVal)
    return None

def find_device():
    mgr = cc.CreateObject(port.PortableDeviceManager, interface=port.IPortableDeviceManager)
    mgr.RefreshDeviceList()
    arr = (c_wchar_p * 32)()
    r = mgr.GetDevices(cast(arr, POINTER(c_wchar_p)), 32)
    count = r[1] if isinstance(r, (list, tuple)) else 0
    for i in range(count):
        if arr[i] and "vid_1d6b&pid_0100" in arr[i].lower():
            return arr[i]
    return None

def main():
    devid = find_device()
    if not devid:
        print("Neato MTP device NOT found"); return
    print("SELECTED:", devid)
    dev = cc.CreateObject(port.PortableDevice, interface=port.IPortableDevice)
    info = cc.CreateObject(types.PortableDeviceValues, interface=port.IPortableDeviceValues)
    dev.Open(devid, info)
    params = cc.CreateObject(types.PortableDeviceValues, interface=port.IPortableDeviceValues)
    params.SetGuidValue(CMD_CATEGORY, GUID(CAT_VENDOR))
    params.SetUnsignedIntegerValue(CMD_ID, ID_GET_VENDOR_OPCODES)
    results = dev.SendCommand(0, params)
    hr = int(results.GetErrorValue(CMD_HRESULT)) & 0xFFFFFFFF
    print("command HRESULT = 0x%08X" % hr)
    coll = results.GetIPortableDevicePropVariantCollectionValue(VENDOR_CODES)
    cnt = c_ulong(0); coll.GetCount(byref(cnt))
    print("vendor opcode count =", cnt.value)
    codes = []
    for i in range(cnt.value):
        pv = port.tag_inner_PROPVARIANT()
        coll.GetAt(i, byref(pv))
        v = pv_uint(pv); codes.append(v)
        print("  vendor opcode[%d] = %s" % (i, ("0x%04X" % v) if v is not None else "vt=%d ?" % pv.vt))
    print("VENDOR_OPCODES =", ", ".join("0x%04X" % c for c in codes if c is not None))
    dev.Close()

if __name__ == "__main__":
    main()
