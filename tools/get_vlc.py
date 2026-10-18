"""Bundle VLC's engine inside Monocat so users do not have to install VLC. Standard library only.

    python tools/get_vlc.py                       install the default engine version (DEFAULT_VERSION below)
    python tools/get_vlc.py latest                find the newest VLC 3.x on videolan.org and install it
    python tools/get_vlc.py 3.0.21                install that exact version
    python tools/get_vlc.py --zip vlc-3.0.21-win64.zip     use a VLC win64 zip you already downloaded
    python tools/get_vlc.py --check               report only: exit 0 = up to date, 10 = newer or first engine available, 1 = could not check
    add --yes to skip the confirmation question, --force to reinstall the same version

Result: a folder named  vlc\\  next to main.py holding libvlc.dll, libvlccore.dll, plugins\\ and VLC's
licence files. Monocat looks in vlc\\ first, then falls back to an installed VLC.

Only the engine is copied (no vlc.exe, no skins, no VLC interface). The download comes only from
get.videolan.org and its SHA-256 file is checked before anything is unpacked.
INSTALL.bat runs this for you; UPDATE.bat runs it with "latest". The installed version is written to
vlc\\monocat-vlc-version.txt so an update is skipped when you already have the newest one.
"""
import hashlib
import io
import os
import re
import shutil
import sys
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(ROOT, "vlc")
BASE = "https://get.videolan.org/vlc/{v}/win64/vlc-{v}-win64.zip"
INDEX = "https://get.videolan.org/vlc/"
DEFAULT_VERSION = "3.0.21"      # a VLC 3.x release; "latest" looks up the newest one
VERSION_FILE = "monocat-vlc-version.txt"
KEEP_FILES = {"libvlc.dll", "libvlccore.dll", "copying.txt", "news.txt", "authors.txt", "readme.txt", "thanks.txt"}
KEEP_DIRS = {"plugins"}


def fetch(url: str) -> bytes:
    print(f"Downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Monocat-build"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.read()
    except Exception as e:
        sys.exit(f"Download failed: {e}")


def installed_version() -> str:
    try:
        with open(os.path.join(DEST, VERSION_FILE), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def vtuple(v: str):
    return tuple(int(x) for x in v.split("."))


def latest_version() -> str:
    """The newest VLC 3.x folder listed on get.videolan.org that has a win64 zip."""
    html = fetch(INDEX).decode("utf-8", "replace")
    found = sorted({m for m in re.findall(r'href="(3\.\d+\.\d+)/"', html)}, key=vtuple, reverse=True)
    for v in found[:6]:
        url = BASE.format(v=v)
        try:
            req = urllib.request.Request(url + ".sha256", headers={"User-Agent": "Monocat-build"})
            with urllib.request.urlopen(req, timeout=30):
                return v
        except Exception:
            continue
    sys.exit("Could not find a VLC 3.x win64 release on videolan.org. Try again later or give a version.")


def verify(data: bytes, url: str) -> None:
    try:
        text = fetch(url + ".sha256").decode("ascii", "replace")
    except SystemExit:
        sys.exit("Could not fetch the SHA-256 file, so the download cannot be verified. Nothing was unpacked.")
    m = re.search(r"\b([0-9a-fA-F]{64})\b", text)
    if not m:
        sys.exit("The SHA-256 file was not in the expected format. Nothing was unpacked.")
    if hashlib.sha256(data).hexdigest().lower() != m.group(1).lower():
        sys.exit("SHA-256 mismatch: the download is damaged or was tampered with. Nothing was unpacked.")
    print("SHA-256 matches.")


def clean_leftovers() -> None:
    """Remove temporary folders an earlier, interrupted run may have left behind."""
    for extra in (DEST + ".tmp", DEST + ".old"):
        if os.path.isdir(extra):
            shutil.rmtree(extra, ignore_errors=True)


def swap_in(tmp: str) -> None:
    """Replace the vlc folder with the freshly unpacked one, then delete the old engine so old
    versions never pile up. If the current folder is in use (Monocat running) nothing is changed.
    If the swap fails half way the previous engine is put back."""
    old = DEST + ".old"
    shutil.rmtree(old, ignore_errors=True)
    if os.path.isdir(DEST):
        try:
            os.replace(DEST, old)
        except OSError:
            shutil.rmtree(tmp, ignore_errors=True)
            sys.exit("The current vlc folder is in use. Close Monocat and try again. Nothing was changed.")
    try:
        os.replace(tmp, DEST)
    except OSError as e:
        if os.path.isdir(old) and not os.path.isdir(DEST):
            os.replace(old, DEST)
        shutil.rmtree(tmp, ignore_errors=True)
        sys.exit(f"Could not put the new engine in place ({e}). The previous engine was kept.")
    if os.path.isdir(old):
        shutil.rmtree(old, ignore_errors=True)
        if os.path.isdir(old):
            print(f"Note: could not delete the old engine in {old}. You can delete that folder yourself.")
        else:
            print("Removed the previous engine files.")


def check_space(need_mb: int = 400) -> None:
    try:
        free = shutil.disk_usage(ROOT).free
    except OSError:
        return
    if free < need_mb * 1024 * 1024:
        sys.exit(f"Not enough free disk space: about {need_mb} MB is needed while unpacking, "
                 f"{free // (1024 * 1024)} MB is free. Nothing was changed.")


def unpack(z: zipfile.ZipFile, version: str = "") -> None:
    names = [n for n in z.namelist() if n.strip("/")]
    tops = {n.split("/")[0] for n in names}
    top = (tops.pop() + "/") if len(tops) == 1 else ""
    if not any(n == top + "libvlc.dll" for n in names):
        sys.exit("That zip has no libvlc.dll. Use the official 64-bit VLC zip (vlc-<version>-win64.zip).")
    tmp = DEST + ".tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    count = 0
    for n in names:
        if n.endswith("/") or not n.startswith(top):
            continue
        rel = n[len(top):]
        parts = rel.split("/")
        if "\\" in rel or ":" in rel or ".." in parts or rel.startswith("/"):
            continue
        keep = (len(parts) == 1 and parts[0].lower() in KEEP_FILES) or parts[0] in KEEP_DIRS
        if not keep:
            continue
        out = os.path.join(tmp, *parts)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with z.open(n) as s, open(out, "wb") as d:
            shutil.copyfileobj(s, d)
        count += 1
    if not os.path.isfile(os.path.join(tmp, "libvlc.dll")) or not os.path.isdir(os.path.join(tmp, "plugins")):
        shutil.rmtree(tmp, ignore_errors=True)
        sys.exit("The unpacked files are incomplete (libvlc.dll or plugins missing). Nothing was changed.")
    with open(os.path.join(tmp, VERSION_FILE), "w", encoding="utf-8") as f:
        f.write(version or "unknown")
    swap_in(tmp)
    print(f"Unpacked {count} files into {DEST}")


def main():
    args = [a for a in sys.argv[1:] if a not in ("--yes", "--force", "--check")]
    yes, force, check_only = "--yes" in sys.argv, "--force" in sys.argv, "--check" in sys.argv
    if args and args[0] in ("-h", "--help"):
        sys.exit(__doc__)
    if not check_only:
        clean_leftovers()
    if args and args[0] == "--zip":
        if len(args) < 2 or not os.path.isfile(args[1]):
            sys.exit("Give the path of a VLC win64 zip after --zip.")
        m = re.search(r"vlc-(3\.\d+\.\d+)-win64", os.path.basename(args[1]))
        unpack(zipfile.ZipFile(args[1]), m.group(1) if m else "")
        print("Done. Monocat will use this bundled engine.")
        return
    want = args[0] if args else ("latest" if check_only else DEFAULT_VERSION)
    if want == "latest":
        want = latest_version()
    if not re.fullmatch(r"3\.\d+\.\d+", want):
        sys.exit("Give a VLC 3.x version such as 3.0.21 (Monocat does not support VLC 4).")
    have = installed_version()
    if check_only:
        print(f"Bundled VLC engine: {have or 'none'}")
        print(f"Newest VLC 3.x:     {want}")
        if have and re.fullmatch(r"3\.\d+\.\d+", have) and vtuple(have) >= vtuple(want):
            print("The bundled engine is up to date.")
            return
        print("A newer engine is available." if have else "No bundled engine yet.")
        sys.exit(10)
    if have and not force and have == want:
        print(f"The bundled VLC engine is already version {have}. Nothing to do.")
        return
    if have and not force and re.fullmatch(r"3\.\d+\.\d+", have) and vtuple(have) > vtuple(want):
        print(f"The bundled VLC engine ({have}) is newer than {want}. Nothing to do. Use --force to replace it.")
        return
    print(f"Bundled VLC engine: {have or 'none'}  ->  {want}")
    if not yes and input("Download VLC " + want + " from videolan.org and install the engine into the vlc folder? [y/N] ").strip().lower() != "y":
        print("Cancelled.")
        sys.exit(2)
    check_space()
    url = BASE.format(v=want)
    data = fetch(url)
    verify(data, url)
    unpack(zipfile.ZipFile(io.BytesIO(data)), want)
    print(f"Done. Monocat now uses its bundled VLC engine {want}.")


if __name__ == "__main__":
    main()
