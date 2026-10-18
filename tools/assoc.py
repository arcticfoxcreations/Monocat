"""Windows integration for Monocat. Standard library only.

    python assoc.py apply      swap the VLC cone for assets\\monocat.ico on the types in EXTS and
                               list Monocat under "Open with" and in Default apps (your default
                               player is NOT changed)
    python assoc.py restore    undo everything apply did, using assoc_backup.json
    python assoc.py status     read only: exit 0 if the Open with entry and icons are in place for THIS
                               folder, 1 if something is missing (for example after the folder was moved)

Everything is written under HKEY_CURRENT_USER (no admin rights). Each value that is
overwritten is saved first, so `restore` puts the original icon back exactly as it was.
"""
import ctypes
import json
import os
import subprocess
import sys

if sys.platform != "win32":
    sys.exit("This tool only works on Windows.")
import winreg  # noqa: E402

# File types whose icon is replaced. Add more here, e.g. ".mp4", ".avi", ".webm".
EXTS = [".mkv", ".mov"]
# File types Monocat is offered for under "Open with".
OPEN_WITH = [".3gp", ".avi", ".flv", ".m2ts", ".m4v", ".mkv", ".mov", ".mp4", ".mpeg", ".mpg",
             ".mts", ".ogv", ".ts", ".vob", ".webm", ".wmv", ".aac", ".flac", ".m4a", ".mp3",
             ".ogg", ".opus", ".wav"]
APP = "Monocat"
PROGID = "Monocat.Media"
EXE_NAME = "Monocat.exe"
LEGACY_PROGIDS = ["MonoPlayer.Media"]           # names used by an earlier test build
LEGACY_APPS = ["MonoPlayer.exe"]
OUR_ICON_NAMES = ("monocat.ico", "video.ico")    # an icon value naming one of these is ours, not the original

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON = os.path.join(ROOT, "assets", "monocat.ico")
EXE = os.path.join(ROOT, EXE_NAME)
BACKUP = os.path.join(ROOT, "assoc_backup.json")
CLASSES = r"Software\Classes"
HKCU = winreg.HKEY_CURRENT_USER


def read_default(root, path):
    try:
        with winreg.OpenKey(root, path) as k:
            return winreg.QueryValueEx(k, "")[0]
    except OSError:
        return None


def current_progid(ext):
    """The handler Windows really uses for this extension (the user's choice wins)."""
    pid = None
    try:
        with winreg.OpenKey(HKCU, rf"Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\{ext}\UserChoice") as k:
            pid = winreg.QueryValueEx(k, "ProgId")[0]
    except OSError:
        pass
    return pid or read_default(winreg.HKEY_CLASSES_ROOT, ext)


def set_value(path, name, value, kind=winreg.REG_SZ):
    with winreg.CreateKey(HKCU, path) as k:
        winreg.SetValueEx(k, name, 0, kind, value)


def set_default(path, value):
    set_value(path, "", value)


def delete_tree(root, path):
    try:
        with winreg.OpenKey(root, path, 0, winreg.KEY_ALL_ACCESS) as k:
            while True:
                try:
                    sub = winreg.EnumKey(k, 0)
                except OSError:
                    break
                delete_tree(root, path + "\\" + sub)
        winreg.DeleteKey(root, path)
    except OSError:
        pass


def delete_value(path, name):
    try:
        with winreg.OpenKey(HKCU, path, 0, winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, name)
    except OSError:
        pass


def prune(path, stop):
    """Delete this key if it is completely empty, then try its parent, and so on up to (not including) stop."""
    while path and path.lower() != stop.lower():
        try:
            with winreg.OpenKey(HKCU, path) as k:
                subkeys, values, _ = winreg.QueryInfoKey(k)
        except OSError:
            return
        if subkeys or values:
            return
        try:
            winreg.DeleteKey(HKCU, path)
        except OSError:
            return
        path = path.rsplit("\\", 1)[0] if "\\" in path else ""


def notify():
    try:
        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)   # SHCNE_ASSOCCHANGED
    except Exception:
        pass
    for args in (["ie4uinit.exe", "-ClearIconCache"], ["ie4uinit.exe", "-show"]):
        try:
            subprocess.run(args, timeout=20, capture_output=True)
        except Exception:
            pass


def load_backup():
    try:
        with open(BACKUP, encoding="utf-8") as f:
            data = json.load(f)
            data.setdefault("icons", {})
            return data
    except (OSError, ValueError):
        return {"icons": {}}


def remove_registration(progids, apps):
    for pid in progids:
        delete_tree(HKCU, rf"{CLASSES}\{pid}")
    for app in apps:
        delete_tree(HKCU, rf"{CLASSES}\Applications\{app}")
    for ext in OPEN_WITH:
        for pid in progids:
            delete_value(rf"{CLASSES}\{ext}\OpenWithProgids", pid)
        for app in apps:
            delete_tree(HKCU, rf"{CLASSES}\{ext}\OpenWithList\{app}")


def apply():
    for p in (ICON, EXE):
        if not os.path.isfile(p):
            sys.exit(f"File not found: {p}")
    icon_val = f"{ICON},0"
    cmd = f'"{EXE}" "%1"'
    backup = load_backup()

    remove_registration(LEGACY_PROGIDS, LEGACY_APPS)      # tidy up an earlier test build

    # 1. replace the icon of whatever program currently owns each type (usually VLC)
    for ext in EXTS:
        pid = current_progid(ext)
        if not pid:
            print(f"  {ext}: no program is associated, skipped")
            continue
        path = rf"{CLASSES}\{pid}\DefaultIcon"
        if pid not in backup["icons"]:          # keep the ORIGINAL on repeated runs
            old = read_default(HKCU, path)
            if old and any(n in old.lower() for n in OUR_ICON_NAMES):
                old = None                      # left by an earlier Monocat run, not an original
            backup["icons"][pid] = {"existed": old is not None, "value": old}
        set_default(path, icon_val)
        print(f"  {ext}: icon changed ({pid})")

    # 2. register Monocat so it shows under "Open with" and in Default apps.
    #    Windows matches the entry to the executable name, so it points at Monocat.exe.
    set_default(rf"{CLASSES}\{PROGID}", "Media file")
    set_default(rf"{CLASSES}\{PROGID}\DefaultIcon", icon_val)
    set_default(rf"{CLASSES}\{PROGID}\shell", "open")
    set_value(rf"{CLASSES}\{PROGID}\shell\open", "FriendlyAppName", APP)
    set_default(rf"{CLASSES}\{PROGID}\shell\open\command", cmd)

    app_key = rf"{CLASSES}\Applications\{EXE_NAME}"
    set_value(app_key, "FriendlyAppName", APP)
    set_default(rf"{app_key}\DefaultIcon", icon_val)
    set_value(rf"{app_key}\shell\open", "FriendlyAppName", APP)
    set_default(rf"{app_key}\shell\open\command", cmd)

    caps = rf"Software\{APP}\Capabilities"
    set_value(caps, "ApplicationName", APP)
    set_value(caps, "ApplicationDescription", "Monocat media player (VLC engine)")
    set_value(caps, "ApplicationIcon", icon_val)
    set_value(r"Software\RegisteredApplications", APP, rf"Software\{APP}\Capabilities")

    for ext in OPEN_WITH:
        set_value(rf"{CLASSES}\{ext}\OpenWithProgids", PROGID, b"", winreg.REG_NONE)
        set_default(rf"{CLASSES}\{ext}\OpenWithList\{EXE_NAME}", "")
        set_value(rf"{app_key}\SupportedTypes", ext, "")
        set_value(rf"{caps}\FileAssociations", ext, PROGID)

    with open(BACKUP, "w", encoding="utf-8") as f:
        json.dump(backup, f, indent=2)
    notify()
    print("Done. Monocat is now listed under Open with.")
    print("If a file still shows the old icon, restart Explorer or sign out and in once.")


def restore():
    backup = load_backup()
    for pid, st in backup.get("icons", {}).items():
        path = rf"{CLASSES}\{pid}\DefaultIcon"
        if st.get("existed") and st.get("value") is not None:
            set_default(path, st["value"])
            print(f"  {pid}: original icon restored")
        else:
            delete_tree(HKCU, path)
            prune(rf"{CLASSES}\{pid}", CLASSES)                  # only removed if nothing else is left in it
            print(f"  {pid}: back to the default icon")
    remove_registration([PROGID] + LEGACY_PROGIDS, [EXE_NAME] + LEGACY_APPS)
    delete_tree(HKCU, rf"Software\{APP}")
    delete_value(r"Software\RegisteredApplications", APP)
    for ext in OPEN_WITH:                                          # tidy up keys that are now empty
        prune(rf"{CLASSES}\{ext}\OpenWithProgids", CLASSES)
        prune(rf"{CLASSES}\{ext}\OpenWithList", CLASSES)
    prune(rf"{CLASSES}\Applications", CLASSES)
    prune(r"Software\RegisteredApplications", "Software")
    try:
        os.remove(BACKUP)
    except OSError:
        pass
    notify()
    print("Restored.")


def status() -> int:
    cmd = read_default(HKCU, rf"{CLASSES}\Applications\{EXE_NAME}\shell\open\command") or ""
    if EXE.lower() not in cmd.lower():
        print("  The Open with entry is missing, or it points to another folder.")
        return 1
    for ext in EXTS:
        pid = current_progid(ext)
        if not pid:
            continue
        ic = read_default(HKCU, rf"{CLASSES}\{pid}\DefaultIcon") or ""
        if ICON.lower() not in ic.lower():
            print(f"  The {ext} icon is not the Monocat icon.")
            return 1
    return 0


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action == "status":
        sys.exit(status())
    elif action == "apply":
        apply()
    elif action == "restore":
        restore()
    else:
        sys.exit(__doc__)
