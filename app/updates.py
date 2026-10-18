"""Update checks for Monocat and its bundled VLC engine.

Nothing here runs by itself unless the user turned on "Check for updates when Monocat starts"
(off by default). Help > Check for updates runs one check on request. A check makes anonymous
read-only requests and sends nothing about the user or the computer:

  * github.com raw file  <UPDATE_REPO>/<UPDATE_BRANCH>/app/__init__.py   to read the newest APP_VERSION
  * get.videolan.org/vlc/                                                to find the newest VLC 3.x engine
    (portable folder installs only; the installed Setup build gets VLC updates with each Monocat release)

Actually installing an update is done by UPDATE.bat (portable) or by downloading the new Setup.
"""
import os
import re
import ssl
import threading
import time
import urllib.request

from PySide6.QtCore import QObject, Signal

from . import APP_VERSION, UPDATE_BRANCH, UPDATE_REPO

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAY = 24 * 3600
VLC_INDEX = "https://get.videolan.org/vlc/"
VLC_ZIP = VLC_INDEX + "{v}/win64/vlc-{v}-win64.zip"


def parse_version(v: str) -> tuple:
    nums = re.findall(r"\d+", (v or "").split("-")[0])
    return tuple(int(n) for n in nums[:3]) + (0,) * (3 - len(nums[:3]))


def is_newer(remote: str, local: str) -> bool:
    return bool(remote) and bool(local) and parse_version(remote) > parse_version(local)


def configured_repo() -> str:
    repo = os.environ.get("MONOCAT_UPDATE_REPO") or UPDATE_REPO
    if re.fullmatch(r"[\w.-]+/[\w.-]+", repo or "") and not repo.startswith("YOUR-GITHUB-USER"):
        return repo
    return ""


def releases_page() -> str:
    repo = configured_repo()
    return f"https://github.com/{repo}/releases/latest" if repo else ""


def is_portable() -> bool:
    """True for the folder install (INSTALL.bat / UPDATE.bat), False for the installed Setup build."""
    return os.path.isfile(os.path.join(ROOT, "UPDATE.bat")) and not getattr(__import__("sys"), "frozen", False)


def local_vlc_version() -> str:
    """Version of the VLC engine bundled in the vlc folder, or '' if Monocat uses another VLC."""
    try:
        with open(os.path.join(ROOT, "vlc", "monocat-vlc-version.txt"), encoding="utf-8") as f:
            v = f.read().strip()
        return v if re.fullmatch(r"3\.\d+\.\d+", v) else ""
    except OSError:
        return ""


def _ssl_context():
    ctx = ssl.create_default_context()
    if not ctx.get_ca_certs():
        for f in ("/etc/ssl/certs/ca-certificates.crt", "/etc/pki/tls/certs/ca-bundle.crt",
                  "/etc/ssl/ca-bundle.pem", "/etc/ssl/cert.pem"):
            if os.path.isfile(f):
                try:
                    ctx.load_verify_locations(f)
                    break
                except (OSError, ssl.SSLError):
                    pass
    return ctx


def _get(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": f"Monocat/{APP_VERSION}"})
    return urllib.request.urlopen(req, timeout=timeout, context=_ssl_context())


def fetch_app_version(repo: str) -> str:
    url = f"https://raw.githubusercontent.com/{repo}/{UPDATE_BRANCH}/app/__init__.py"
    with _get(url) as r:
        text = r.read(20000).decode("utf-8", "replace")
    m = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', text)
    if not m:
        raise ValueError("no version found")
    return m.group(1)


def fetch_vlc_version() -> str:
    """Newest VLC 3.x folder on videolan.org that really has a win64 zip."""
    with _get(VLC_INDEX) as r:
        html = r.read().decode("utf-8", "replace")
    found = sorted(set(re.findall(r'href="(3\.\d+\.\d+)/"', html)), key=parse_version, reverse=True)
    for v in found[:4]:
        try:
            with _get(VLC_ZIP.format(v=v) + ".sha256", timeout=15):
                return v
        except Exception:
            continue
    return ""


def collect() -> dict:
    errors = []
    app_remote = vlc_remote = ""
    repo = configured_repo()
    if not repo:
        errors.append("Monocat: no update source is set (UPDATE_REPO in app/__init__.py).")
    else:
        try:
            app_remote = fetch_app_version(repo)
        except Exception:
            errors.append("Monocat: could not reach github.com.")
    if is_portable() and local_vlc_version():
        try:
            vlc_remote = fetch_vlc_version()
            if not vlc_remote:
                errors.append("VLC engine: no release was found on videolan.org.")
        except Exception:
            errors.append("VLC engine: could not reach videolan.org.")
    return {"app_remote": app_remote, "vlc_remote": vlc_remote, "errors": errors, "t": time.time(), "checked": True}


# ---------------------------------------------------------------- reading a result
def app_newer(info: dict) -> bool:
    return is_newer((info or {}).get("app_remote", ""), APP_VERSION)


def vlc_newer(info: dict) -> bool:
    return is_portable() and is_newer((info or {}).get("vlc_remote", ""), local_vlc_version())


def has_update(info: dict) -> bool:
    return app_newer(info) or vlc_newer(info)


def describe(info: dict) -> str:
    """One line for a tooltip, e.g. 'Monocat 1.1.0 and VLC engine 3.0.22'."""
    parts = []
    if app_newer(info):
        parts.append(f"Monocat {info['app_remote']}")
    if vlc_newer(info):
        parts.append(f"VLC engine {info['vlc_remote']}")
    return " and ".join(parts)


def cached_info(store) -> dict:
    c = store.setting("update_cache") or {}
    return {"app_remote": c.get("app_remote", ""), "vlc_remote": c.get("vlc_remote", ""), "errors": [],
            "t": c.get("t", 0), "checked": bool(c)}


class UpdateChecker(QObject):
    result = Signal(dict)

    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
        self.busy = False
        self.result.connect(self._persist)      # runs on the GUI thread, so the store is written safely

    def due(self) -> bool:
        """Automatic check at start-up: only if the user opted in, at most once a day."""
        if not self.store.setting("check_updates"):
            return False
        try:
            last = float(self.store.setting("last_update_check") or 0)
        except (TypeError, ValueError):
            last = 0.0
        return time.time() - last > DAY

    def check(self, manual=False):
        if self.busy:
            return
        self.busy = True
        self.store.set_setting("last_update_check", time.time())
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            info = collect()
        except Exception:
            info = {"app_remote": "", "vlc_remote": "", "errors": ["The check failed."], "t": time.time(), "checked": True}
        self.busy = False
        self.result.emit(info)

    def _persist(self, info: dict):
        old = self.store.setting("update_cache") or {}
        self.store.set_setting("update_cache", {
            "app_remote": info.get("app_remote") or old.get("app_remote", ""),
            "vlc_remote": info.get("vlc_remote") or old.get("vlc_remote", ""),
            "t": info.get("t", 0)})


def start_update() -> bool:
    """Portable install: open UPDATE.bat in its own window. Returns False if that is not possible."""
    bat = os.path.join(ROOT, "UPDATE.bat")
    try:
        os.startfile(bat)               # Windows only
        return True
    except (AttributeError, OSError):
        return False
