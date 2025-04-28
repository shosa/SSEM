#define MyAppName "SSEM"
#define MyAppVersion "2.2.0c"
#define MyAppPublisher "Stefano Solidoro"
#define MyAppURL "mailto:stefano.solidoro@icloud.com"
#define MyAppExeName "SSEM.exe"

[Setup]
AppId={{6E33FFCF-0DB0-45AB-9C52-A4DA9EDAB9A7}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputDir=output
OutputBaseFilename=SSEM-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern


[Dirs]
Name: "{app}\logs"; Permissions: users-modify
Name: "{app}\config"; Permissions: users-modify

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupicon"; Description: "Avvia automaticamente all'accensione"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\SSEM\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\SSEM\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{commonstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startupicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent