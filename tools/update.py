"""Update Monocat's program files from its GitHub repository. Standard library only.

    python tools\\update.py            check, ask, then update
    python tools\\update.py --yes      check, then update without asking (UPDATE.bat asks once itself)
    python tools\\update.py --check    report only: exit 0 = up to date, 10 = newer version available, 1 = could not check

What it does:
  * downloads  https://github.com/<UPDATE_REPO>/archive/refs/heads/<UPDATE_BRANCH>.zip
    (UPDATE_REPO and UPDATE_BRANCH are set in app/__init__.py)
  * compares the version in app/__init__.py with the installed one
  * backs up the current files to backup_before_update\\ (only the newest backup is kept)
  * copies the new files over and removes program files the new version no longer has,
    so old files do not pile up

What it never touches: .venv, the vlc folder, your settings and library (%APPDATA%\\Monocat) and the
backup of your original file icons (assoc_backup.json). Changed .bat files are saved as NAME.bat.new;
UPDATE.bat swaps them in after this script has finished.
"""
import io
import os
import re
import shutil
import sys
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP_DIR = os.path.join(ROOT, "backup_before_update")
# Paths (relative to the project root) that an update may replace.
MANAGED = ["app", "assets", "tools", "launcher", "installer", "main.py", "requirements.txt", "Monocat.exe",
           "README.md", "LICENSE", "THIRD_PARTY_NOTICES.md"]


def _init_value(name: str, default: str) -> str:
    try:
        with open(os.path.join(ROOT, "app", "__init__.py"), encoding="utf-8") as f:
            return re.search(name + r'\s*=\s*"([^"]*)"', f.read()).group(1)
    except (OSError, AttributeError):
        return default


def local_version() -> str:
    return _init_value("APP_VERSION", "0")


def vtuple(v: str):
    return tuple(int(p) if p.isdigit() else 0 for p in re.split(r"[.\-]", v))


def source_url() -> str:
    override = os.environ.get("MONOCAT_UPDATE_URL")      # testing, or a fork pointing elsewhere
    if override:
        return override
    repo = os.environ.get("MONOCAT_UPDATE_REPO") or _init_value("UPDATE_REPO", "")
    branch = _init_value("UPDATE_BRANCH", "main")
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repo) or repo.startswith("YOUR-GITHUB-USER"):
        sys.exit("No update source is set. Edit UPDATE_REPO in app\\__init__.py "
                 "(for example \"yourname/Monocat\") and run this again.")
    return f"https://github.com/{repo}/archive/refs/heads/{branch}.zip"


def download(url: str) -> zipfile.ZipFile:
    print(f"Downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Monocat-updater"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
    except Exception as e:
        sys.exit(f"Could not download the update: {e}")
    try:
        return zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        sys.exit("The download was not a valid zip file. Nothing was changed.")


def find_top(z: zipfile.ZipFile) -> str:
    """GitHub archives have one top folder (Monocat-main/). Return its prefix, or '' if flat."""
    names = [n for n in z.namelist() if n.strip("/")]
    tops = {n.split("/")[0] for n in names}
    if len(tops) == 1 and not any(n == "main.py" for n in names):
        return tops.pop() + "/"
    return ""


def safe(z, top):
    for n in z.namelist():
        if not n.startswith(top) or n.endswith("/"):
            continue
        rel = n[len(top):]
        if not rel or rel.startswith(("/", "\\")) or "\\" in rel or ":" in rel or ".." in rel.split("/"):
            continue
        yield n, rel


def _crlf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")


def _remove_stale(new_files: set) -> int:
    """Delete program files the new version no longer ships (inside managed folders only),
    old bytecode, and leftover *.new files. Everything removed was backed up first."""
    removed = 0
    for folder in ("app", "assets", "tools", "launcher", "installer"):
        base = os.path.join(ROOT, folder)
        if not os.path.isdir(base) or not any(f.startswith(folder + "/") for f in new_files):
            continue          # the archive had nothing for this folder: leave it alone
        for dirpath, dirnames, filenames in os.walk(base, topdown=False):
            if os.path.basename(dirpath) == "__pycache__":
                shutil.rmtree(dirpath, ignore_errors=True)
                continue
            for fn in filenames:
                rel = os.path.relpath(os.path.join(dirpath, fn), ROOT).replace(os.sep, "/")
                if rel not in new_files:
                    try:
                        os.remove(os.path.join(dirpath, fn))
                        removed += 1
                        print(f"  removed old file {rel}")
                    except OSError:
                        pass
            if dirpath != base and not os.listdir(dirpath):
                try:
                    os.rmdir(dirpath)
                except OSError:
                    pass
    for fn in os.listdir(ROOT):
        if fn.endswith(".new") and not fn.lower().endswith(".bat.new"):
            try:
                os.remove(os.path.join(ROOT, fn))
            except OSError:
                pass
    return removed


def main():
    check_only = "--check" in sys.argv
    yes = "--yes" in sys.argv
    url = source_url()
    z = download(url)
    top = find_top(z)
    try:
        remote_init = z.read(top + "app/__init__.py").decode("utf-8")
        remote = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', remote_init).group(1)
    except (KeyError, AttributeError):
        sys.exit("That archive does not look like Monocat (no app/__init__.py with a version). Nothing was changed.")
    mine = local_version()
    print(f"Installed version: {mine}\nAvailable version: {remote}")
    if vtuple(remote) <= vtuple(mine):
        print("You already have the latest version.")
        return
    if check_only:
        print("A newer version is available. Run UPDATE.bat to install it.")
        sys.exit(10)
    if not yes and input("Update now? Your settings and library are kept. [y/N] ").strip().lower() != "y":
        print("Cancelled.")
        return

    if os.path.isdir(BACKUP_DIR):
        shutil.rmtree(BACKUP_DIR, ignore_errors=True)
    os.makedirs(BACKUP_DIR)
    for item in MANAGED:
        src = os.path.join(ROOT, item)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(BACKUP_DIR, item), ignore=shutil.ignore_patterns("__pycache__"))
        elif os.path.isfile(src):
            shutil.copy2(src, os.path.join(BACKUP_DIR, item))
    print(f"Backed up current files to {BACKUP_DIR}")

    staged_bats = []
    new_files = set()
    count = failed = 0
    for name, rel in safe(z, top):
        first = rel.split("/")[0]
        if "/" not in rel and rel.lower().endswith(".bat"):
            data = _crlf(z.read(name))
            dest = os.path.join(ROOT, rel)
            try:
                with open(dest, "rb") as f:
                    same = f.read() == data
            except OSError:
                same = False
            if not same:
                with open(dest + ".new", "wb") as f:
                    f.write(data)
                staged_bats.append(rel)
            continue
        if first not in MANAGED:
            continue
        new_files.add(rel)
        dest = os.path.join(ROOT, *rel.split("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        tmp = dest + ".new"
        try:
            with z.open(name) as s, open(tmp, "wb") as d:
                shutil.copyfileobj(s, d)
            os.replace(tmp, dest)
            count += 1
        except OSError as e:
            failed += 1
            print(f"  could not replace {rel}: {e}")
            try:
                os.remove(tmp)
            except OSError:
                pass
    if failed:
        print(f"{failed} file(s) could not be replaced, usually because Monocat is still running.")
        print("Close Monocat and run UPDATE.bat again. The backup is in backup_before_update.")
        sys.exit(1)
    removed = _remove_stale(new_files)
    print(f"Updated {count} files to version {remote}" + (f", removed {removed} old files." if removed else "."))
    if staged_bats:
        print("Newer batch files were saved as: " + ", ".join(sorted(b + ".new" for b in staged_bats)))
        print("UPDATE.bat puts them in place when it finishes.")
    print("If anything looks wrong, copy the contents of backup_before_update back over this folder.")


if __name__ == "__main__":
    main()
