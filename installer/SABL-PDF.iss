#define AppName "Simple PDF"
#define AppVersion "1.0.2"

[Setup]
AppId={{B0B635E2-0CB9-4FA1-BF4C-7BF92A2F1D94}
AppName={#AppName}
AppVersion={#AppVersion}
ChangesAssociations=yes
DefaultDirName={autopf}\Simple PDF
DefaultGroupName=Simple PDF
OutputDir=..\dist\installer
OutputBaseFilename=Simple-PDF-Setup-v{#AppVersion}-x64
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName=Simple PDF

[Files]
Source: "..\dist\Simple PDF\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Simple PDF"; Filename: "{app}\Simple PDF.exe"
Name: "{autodesktop}\Simple PDF"; Filename: "{app}\Simple PDF.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[InstallDelete]
Type: files; Name: "{app}\SABL PDF.exe"
Type: files; Name: "{group}\SABL PDF.lnk"
Type: files; Name: "{autodesktop}\SABL PDF.lnk"

[Registry]
Root: HKCU; Subkey: "Software\RegisteredApplications"; ValueName: "SABL PDF"; Flags: deletevalue
Root: HKCU; Subkey: "Software\Classes\Applications\SABL PDF.exe"; Flags: deletekey
Root: HKCU; Subkey: "Software\Classes\SABL.PDF"; ValueType: string; ValueData: "Simple PDF Document"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SABL.PDF\DefaultIcon"; ValueType: string; ValueData: "{app}\Simple PDF.exe,0"
Root: HKCU; Subkey: "Software\Classes\SABL.PDF\shell\open\command"; ValueType: string; ValueData: """{app}\Simple PDF.exe"" ""%1"""
Root: HKCU; Subkey: "Software\Classes\.pdf\OpenWithProgids"; ValueType: string; ValueName: "SABL.PDF"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\Applications\Simple PDF.exe\SupportedTypes"; ValueType: string; ValueName: ".pdf"; ValueData: ""; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\SABL PDF\Capabilities"; ValueType: string; ValueName: "ApplicationName"; ValueData: "Simple PDF"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\SABL PDF\Capabilities"; ValueType: string; ValueName: "ApplicationDescription"; ValueData: "Simple offline PDF viewer"
Root: HKCU; Subkey: "Software\SABL PDF\Capabilities\FileAssociations"; ValueType: string; ValueName: ".pdf"; ValueData: "SABL.PDF"
Root: HKCU; Subkey: "Software\RegisteredApplications"; ValueType: string; ValueName: "Simple PDF"; ValueData: "Software\SABL PDF\Capabilities"; Flags: uninsdeletevalue

[Run]
Filename: "{app}\Simple PDF.exe"; Description: "Open Simple PDF"; Flags: postinstall nowait skipifsilent
