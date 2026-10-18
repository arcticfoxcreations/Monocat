; Inno Setup script for the Monocat installer. Built by .github/workflows/release.yml (or by hand: see README).
; The version is passed in as /DAppVersion=1.0.0 and the PyInstaller output is expected in dist\Monocat.
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{6B1D2C57-3A0E-4C54-9E0B-7D5E2A6C1F42}
AppName=Monocat
AppVersion={#AppVersion}
AppVerName=Monocat {#AppVersion}
AppPublisher=Monocat contributors
AppPublisherURL=https://github.com/arcticfoxcreations/Monocat
DefaultDirName={autopf}\Monocat
DefaultGroupName=Monocat
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\monocat.ico
UninstallDisplayIcon={app}\Monocat.exe
OutputDir=..\dist-installer
OutputBaseFilename=Monocat-Setup-{#AppVersion}
LicenseFile=..\LICENSE
ChangesAssociations=yes

[Tasks]
Name: "desktopicon"; Description: "Create a Desktop shortcut"; GroupDescription: "Shortcuts:"
Name: "openwith"; Description: "List Monocat under ""Open with"" for video and audio files (your default player is not changed)"; GroupDescription: "File types:"

[Files]
Source: "..\dist\Monocat\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Monocat"; Filename: "{app}\Monocat.exe"
Name: "{autodesktop}\Monocat"; Filename: "{app}\Monocat.exe"; Tasks: desktopicon

[Registry]
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe"; ValueType: string; ValueName: "FriendlyAppName"; ValueData: "Monocat"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\Monocat.exe,0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe\shell\open"; ValueType: string; ValueName: "FriendlyAppName"; ValueData: "Monocat"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\Monocat.exe"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.3gp\OpenWithList\Monocat.exe"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe\SupportedTypes"; ValueType: string; ValueName: ".3gp"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.avi\OpenWithList\Monocat.exe"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe\SupportedTypes"; ValueType: string; ValueName: ".avi"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.flv\OpenWithList\Monocat.exe"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe\SupportedTypes"; ValueType: string; ValueName: ".flv"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.m2ts\OpenWithList\Monocat.exe"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe\SupportedTypes"; ValueType: string; ValueName: ".m2ts"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.m4v\OpenWithList\Monocat.exe"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe\SupportedTypes"; ValueType: string; ValueName: ".m4v"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mkv\OpenWithList\Monocat.exe"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe\SupportedTypes"; ValueType: string; ValueName: ".mkv"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mov\OpenWithList\Monocat.exe"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe\SupportedTypes"; ValueType: string; ValueName: ".mov"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mp4\OpenWithList\Monocat.exe"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe\SupportedTypes"; ValueType: string; ValueName: ".mp4"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mpeg\OpenWithList\Monocat.exe"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe\SupportedTypes"; ValueType: string; ValueName: ".mpeg"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mpg\OpenWithList\Monocat.exe"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe\SupportedTypes"; ValueType: string; ValueName: ".mpg"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mts\OpenWithList\Monocat.exe"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe\SupportedTypes"; ValueType: string; ValueName: ".mts"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.ogv\OpenWithList\Monocat.exe"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe\SupportedTypes"; ValueType: string; ValueName: ".ogv"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.ts\OpenWithList\Monocat.exe"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe\SupportedTypes"; ValueType: string; ValueName: ".ts"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.vob\OpenWithList\Monocat.exe"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe\SupportedTypes"; ValueType: string; ValueName: ".vob"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.webm\OpenWithList\Monocat.exe"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe\SupportedTypes"; ValueType: string; ValueName: ".webm"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.wmv\OpenWithList\Monocat.exe"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe\SupportedTypes"; ValueType: string; ValueName: ".wmv"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.aac\OpenWithList\Monocat.exe"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe\SupportedTypes"; ValueType: string; ValueName: ".aac"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.flac\OpenWithList\Monocat.exe"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe\SupportedTypes"; ValueType: string; ValueName: ".flac"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.m4a\OpenWithList\Monocat.exe"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe\SupportedTypes"; ValueType: string; ValueName: ".m4a"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mp3\OpenWithList\Monocat.exe"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe\SupportedTypes"; ValueType: string; ValueName: ".mp3"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.ogg\OpenWithList\Monocat.exe"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe\SupportedTypes"; ValueType: string; ValueName: ".ogg"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.opus\OpenWithList\Monocat.exe"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe\SupportedTypes"; ValueType: string; ValueName: ".opus"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.wav\OpenWithList\Monocat.exe"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\Monocat.exe\SupportedTypes"; ValueType: string; ValueName: ".wav"; ValueData: ""; Tasks: openwith

[Run]
Filename: "{app}\Monocat.exe"; Description: "Start Monocat"; Flags: nowait postinstall skipifsilent
