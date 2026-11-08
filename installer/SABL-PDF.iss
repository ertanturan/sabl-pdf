#define AppName "SABL PDF"
#define AppVersion "0.1.0"

[Setup]
AppId={{B0B635E2-0CB9-4FA1-BF4C-7BF92A2F1D94}
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={autopf}\SABL PDF
DefaultGroupName=SABL PDF
OutputDir=..\dist\installer
OutputBaseFilename=SABL-PDF-Setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName=SABL PDF

[Files]
Source: "..\dist\SABL PDF\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SABL PDF"; Filename: "{app}\SABL PDF.exe"
Name: "{autodesktop}\SABL PDF"; Filename: "{app}\SABL PDF.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Registry]
Root: HKCU; Subkey: "Software\Classes\SABL.PDF"; ValueType: string; ValueData: "SABL PDF Document"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SABL.PDF\DefaultIcon"; ValueType: string; ValueData: "{app}\SABL PDF.exe,0"
Root: HKCU; Subkey: "Software\Classes\SABL.PDF\shell\open\command"; ValueType: string; ValueData: """{app}\SABL PDF.exe"" ""%1"""
Root: HKCU; Subkey: "Software\Classes\.pdf\OpenWithProgids"; ValueType: string; ValueName: "SABL.PDF"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\SABL PDF\Capabilities"; ValueType: string; ValueName: "ApplicationName"; ValueData: "SABL PDF"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\SABL PDF\Capabilities"; ValueType: string; ValueName: "ApplicationDescription"; ValueData: "Simple offline PDF viewer"
Root: HKCU; Subkey: "Software\SABL PDF\Capabilities\FileAssociations"; ValueType: string; ValueName: ".pdf"; ValueData: "SABL.PDF"
Root: HKCU; Subkey: "Software\RegisteredApplications"; ValueType: string; ValueName: "SABL PDF"; ValueData: "Software\SABL PDF\Capabilities"; Flags: uninsdeletevalue

[Run]
Filename: "{app}\SABL PDF.exe"; Description: "Open SABL PDF"; Flags: postinstall nowait skipifsilent
