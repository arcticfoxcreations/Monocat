# PyInstaller spec: builds dist\Monocat\Monocat.exe with Python, PySide6, the assets and the VLC engine inside.
# Run from the repository root AFTER `python tools/get_vlc.py --yes` has created the vlc folder:
#     pyinstaller --noconfirm installer/monocat.spec
import os
ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
datas = [(os.path.join(ROOT, "assets"), "assets"), (os.path.join(ROOT, "LICENSE"), ".")]
vlc_dir = os.path.join(ROOT, "vlc")
if os.path.isdir(vlc_dir):
    datas.append((vlc_dir, "vlc"))          # lands in _internal\vlc, where app/engine.py looks first
else:
    print("WARNING: no vlc folder, the build will rely on a VLC installed on the user's PC")

a = Analysis([os.path.join(ROOT, "main.py")], pathex=[ROOT], datas=datas,
             hiddenimports=["vlc", "PySide6.QtSvg", "PySide6.QtNetwork"],
             excludes=["tkinter", "unittest", "pydoc"], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Monocat", console=False,
          icon=os.path.join(ROOT, "assets", "monocat.ico"), upx=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="Monocat")
