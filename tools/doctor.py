"""Read-only health check used by INSTALL.bat, REPAIR.bat and UPDATE.bat. Changes nothing.

    python tools\\doctor.py     prints one line per part and exits with a bit mask:
                               1 = Python packages missing or damaged
                               2 = VLC engine missing or not loadable
                               4 = Open with entry / file icons not in place for this folder
Run it with the .venv Python.
"""
import importlib.util
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def packages_ok() -> bool:
    for m in ("PySide6", "vlc"):
        if importlib.util.find_spec(m) is None:
            return False
    try:
        import PySide6.QtCore  # noqa: F401
        import PySide6.QtWidgets  # noqa: F401
    except Exception:
        return False
    return True


def vlc_state():
    """(loadable, version, bundled)"""
    bundled = os.path.isfile(os.path.join(ROOT, "vlc", "libvlc.dll")) and os.path.isdir(os.path.join(ROOT, "vlc", "plugins"))
    try:
        import app.engine as e
        v = e.vlc.libvlc_get_version().decode() if e.vlc else ""
    except BaseException:
        v = ""
    ver = ""
    if bundled:
        try:
            with open(os.path.join(ROOT, "vlc", "monocat-vlc-version.txt"), encoding="utf-8") as f:
                ver = f.read().strip()
        except OSError:
            pass
    return bool(v), (ver or v), bundled


def main() -> int:
    mask = 0
    if packages_ok():
        print("  [ok]      Python packages (PySide6, python-vlc)")
    else:
        print("  [missing] Python packages (PySide6, python-vlc)")
        mask |= 1
    if mask & 1:
        print("  [unknown] VLC engine (checked after the packages are installed)")
    else:
        ok, ver, bundled = vlc_state()
        if ok and bundled:
            print(f"  [ok]      VLC engine {ver} (bundled in the vlc folder)")
        elif ok:
            print("  [ok]      VLC engine (a VLC already on this PC will be used)")
        else:
            print("  [missing] VLC engine" + (" (the vlc folder is damaged)" if bundled else ""))
            mask |= 2
    if sys.platform == "win32":
        r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "assoc.py"), "status"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            print("  [ok]      Open with entry and file icon")
        else:
            print("  [missing] Open with entry and file icon")
            mask |= 4
    return mask


if __name__ == "__main__":
    sys.exit(main())
