[Setup]
AppName=Voice by SumanOnline
AppVersion=0.1.0
AppPublisher=SumanOnline
DefaultDirName={localappdata}\Programs\Voice by SumanOnline
DefaultGroupName=Voice by SumanOnline
OutputDir=dist
OutputBaseFilename=Voice-by-SumanOnline-Setup
SetupIconFile=..\assets\logo.ico
Compression=lzma2/max
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\assets\logo.ico
CloseApplications=yes
RestartApplications=no
ChangesAssociations=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\\start_desktop.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\\pyproject.toml"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\\assets\\*"; DestDir: "{app}\\assets"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\\voice_by_sumanonline\\*"; DestDir: "{app}\\voice_by_sumanonline"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\\ui\\dist\\*"; DestDir: "{app}\\ui\\dist"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "runtime\\*"; DestDir: "{app}\\runtime"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\\Voice by SumanOnline"; Filename: "{app}\\runtime\\pythonw.exe"; Parameters: "-m voice_by_sumanonline.main --ui"; WorkingDir: "{app}"; IconFilename: "{app}\\assets\\logo.ico"
Name: "{group}\\Uninstall Voice by SumanOnline"; Filename: "{uninstallexe}"
Name: "{autodesktop}\\Voice by SumanOnline"; Filename: "{app}\\runtime\\pythonw.exe"; Parameters: "-m voice_by_sumanonline.main --ui"; WorkingDir: "{app}"; IconFilename: "{app}\\assets\\logo.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\\runtime\\pythonw.exe"; Parameters: "-m voice_by_sumanonline.main --ui"; WorkingDir: "{app}"; Description: "{cm:LaunchProgram,Voice by SumanOnline}"; Flags: nowait postinstall skipifsilent
