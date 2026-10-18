# Third-party notices

Monocat's own code is under the MIT licence (see `LICENSE`). Monocat is a modified fork of
Pylon by Nirmal Joseph Ukken (MIT), https://github.com/nirmaljosephukken/pylon-player.

## What is and is not included

**Source-code downloads (this repository)** contain no third-party binaries. `INSTALL.bat` installs
PySide6-Essentials and python-vlc from PyPI into a private `.venv` folder, and can install Python
and VLC through winget, only after asking.

**Release builds that include a `vlc` folder** contain libVLC (libvlc.dll, libvlccore.dll and the
plugins folder) from VideoLAN's official VLC 3.x for Windows, unmodified, copied by
`tools/get_vlc.py`. Their licence text is in `vlc\COPYING.txt`. The matching source code is at
https://code.videolan.org/videolan/vlc (choose the tag for the bundled version). Python is never
bundled.

## Components

| Component | Used for | Licence | Source |
| --- | --- | --- | --- |
| libVLC (VLC media player 3.0) | All playback, decoding and streaming | LGPL 2.1 or later (some VLC plugins are GPL) | https://www.videolan.org/vlc/ and https://code.videolan.org/videolan/vlc |
| python-vlc | Python bindings for libVLC | LGPL 2.1 or later | https://github.com/oaubert/python-vlc |
| Qt for Python (PySide6-Essentials, Shiboken6) | The user interface | LGPL v3 (or commercial) | https://www.qt.io/qt-for-python and https://code.qt.io/cgit/pyside/pyside-setup.git |
| Python | Runs Monocat | PSF License | https://www.python.org |

Qt and python-vlc are installed from PyPI as separate, replaceable libraries. If you redistribute
Monocat together with any of these components, you must follow their licences: ship their licence
texts, keep them replaceable as separate libraries, and point to their source code.

## Design credit

The interface adapts ideas from the VLC redesign concept by Juxtopposed
(https://www.youtube.com/@juxtopposed), published free on Figma Community under CC BY 4.0
(https://creativecommons.org/licenses/by/4.0/). Monocat re-implements the ideas in code with
changes; it contains no files or artwork from that design.

## Setup build (Monocat-Setup.exe)

The Setup build is made with PyInstaller and contains, besides Monocat and the VLC engine described above:
Python (Python Software Foundation License), PySide6 and Qt (LGPL 3.0; https://www.qt.io/licensing),
and python-vlc (LGPL 2.1 or later). These libraries are shipped unmodified as separate files in the
installation folder, so they can be replaced by the user. The Setup is created with Inno Setup
(https://jrsoftware.org/isinfo.php); Inno Setup's licence applies to the compiler, not to Monocat.

## Content you play

Monocat is a player. It does not include, host or link to any films, shows, music or streams.
You are responsible for having the right to play what you open.

## Trademarks

VLC and the VLC traffic-cone logo are trademarks of VideoLAN. Monocat is an independent project and
is not affiliated with, sponsored or endorsed by VideoLAN. Other names mentioned (for example
OpenSubtitles, Windows, Python, Qt) belong to their owners.
