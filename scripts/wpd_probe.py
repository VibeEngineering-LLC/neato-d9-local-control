"""Probe: does comtypes expose WPD typelibs and MTP-ext PROPERTYKEY constants? Read-only, no device I/O."""
import comtypes.client as cc
mods = []
for dll in ("PortableDeviceApi.dll", "PortableDeviceTypes.dll"):
    try:
        m = cc.GetModule(dll); mods.append(m); print("OK  ", dll, "->", m.__name__)
    except Exception as e:
        print("FAIL", dll, type(e).__name__, e)
hits = []
for m in mods:
    for name in dir(m):
        if "MTP_EXT" in name or "VENDOR_OP" in name or name.startswith("WPD_COMMAND"):
            hits.append(m.__name__ + "." + name)
print("WPD_COMMAND/MTP_EXT constants found:", len(hits))
for h in hits[:40]:
    print("  ", h)
