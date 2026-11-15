[Setup]
AppName=Voice by SumanOnline
AppVersion=0.1.0
AppPublisher=SumanOnline
DefaultDirName={userappdata}\Programs\Voice by SumanOnline
DefaultGroupName=Voice by SumanOnline
OutputDir=dist
OutputBaseFilename=Voice-by-SumanOnline-Setup
SetupIconFile=..\assets\logo.ico
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\assets\logo.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\\start_desktop.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\\pyproject.toml"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\\uv.lock"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\\assets\\*"; DestDir: "{app}\\assets"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\\voice_by_sumanonline\\*"; DestDir: "{app}\\voice_by_sumanonline"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\\installer\\install.ps1"; DestDir: "{app}\\installer"; Flags: ignoreversion
Source: "..\\crates\\voice-launcher\\*"; DestDir: "{app}\\crates\\voice-launcher"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\\Voice by SumanOnline"; Filename: "{app}\\start_desktop.bat"; IconFilename: "{app}\\assets\\logo.ico"
Name: "{group}\\Uninstall Voice by SumanOnline"; Filename: "{uninstallexe}"
Name: "{autodesktop}\\Voice by SumanOnline"; Filename: "{app}\\start_desktop.bat"; IconFilename: "{app}\\assets\\logo.ico"; Tasks: desktopicon

[Run]
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\\installer\\install.ps1"""; Flags: runhidden
Filename: "{app}\\start_desktop.bat"; Description: "{cm:LaunchProgram,Voice by SumanOnline}"; Flags: nowait postinstall skipifsilent
