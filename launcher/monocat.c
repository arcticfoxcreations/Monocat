/* Monocat.exe: small launcher so Windows lists Monocat by name and icon in "Open with".
   It runs  <folder>\.venv\Scripts\pythonw.exe <folder>\main.py <arguments>.
   Written for Monocat (MIT licence). Build: see README, section "Rebuilding the launcher". */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <wchar.h>

static const wchar_t *skip_argv0(const wchar_t *cmd) {
    if (*cmd == L'"') { cmd++; while (*cmd && *cmd != L'"') cmd++; if (*cmd) cmd++; }
    else { while (*cmd && *cmd != L' ' && *cmd != L'\t') cmd++; }
    while (*cmd == L' ' || *cmd == L'\t') cmd++;
    return cmd;
}

int WINAPI wWinMain(HINSTANCE h, HINSTANCE p, PWSTR c, int n) {
    (void)h; (void)p; (void)c; (void)n;
    wchar_t self[MAX_PATH * 2], dir[MAX_PATH * 2], py[MAX_PATH * 2], mainpy[MAX_PATH * 2];
    DWORD len = GetModuleFileNameW(NULL, self, MAX_PATH * 2);
    if (!len || len >= MAX_PATH * 2) return 1;
    wcscpy(dir, self);
    wchar_t *slash = wcsrchr(dir, L'\\');
    if (!slash) return 1;
    *slash = 0;
    swprintf(mainpy, MAX_PATH * 2, L"%ls\\main.py", dir);
    swprintf(py, MAX_PATH * 2, L"%ls\\.venv\\Scripts\\pythonw.exe", dir);
    if (GetFileAttributesW(py) == INVALID_FILE_ATTRIBUTES) {
        MessageBoxW(NULL, L"Monocat is not set up yet.\n\nRun INSTALL.bat in the Monocat folder first.",
                    L"Monocat", MB_ICONINFORMATION);
        return 1;
    }
    const wchar_t *args = skip_argv0(GetCommandLineW());
    size_t total = wcslen(py) + wcslen(mainpy) + wcslen(args) + 16;
    wchar_t *cmd = (wchar_t *)HeapAlloc(GetProcessHeap(), 0, total * sizeof(wchar_t));
    if (!cmd) return 1;
    swprintf(cmd, total, L"\"%ls\" \"%ls\" %ls", py, mainpy, args);
    STARTUPINFOW si; PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof si); si.cb = sizeof si;
    ZeroMemory(&pi, sizeof pi);
    if (!CreateProcessW(py, cmd, NULL, NULL, FALSE, 0, NULL, dir, &si, &pi)) {
        MessageBoxW(NULL, L"Monocat could not start Python.", L"Monocat", MB_ICONERROR);
        return 1;
    }
    AllowSetForegroundWindow(pi.dwProcessId);
    CloseHandle(pi.hThread);
    CloseHandle(pi.hProcess);
    return 0;
}
