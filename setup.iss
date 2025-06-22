#define MyAppName       "TA Processing Tool"
#define MyAppVersion    "1.0.0"
#define MyAppPublisher  "Hadi Fauzan Hanif"
#define MyAppURL        "mailto:hadifauzanhanif@gmail.com"
#define MyAppExeName    "TA Processing Tool.exe"

[Setup]
AppId={{9C2D3708-9AEC-4F14-B0CE-CAD7B50AEABC}
AppName=TA Daily Process Tool
AppVersion=1.0
AppPublisher=Hadi Fauzan Hanif
AppPublisherURL=https://github.com/hadifauzanhanif/TA-Daily-Process-Tool
AppSupportURL=https://github.com/hadifauzanhanif/TA-Daily-Process-Tool
AppUpdatesURL=https://github.com/hadifauzanhanif/TA-Daily-Process-Tool
DefaultDirName={autopf}\TA Daily Process Tool
DefaultGroupName=TA Daily Process Tool
AllowNoIcons=yes
LicenseFile=
InfoBeforeFile=
InfoAfterFile=
OutputDir=installer
OutputBaseFilename=TA_Daily_Process_Tool_Setup
SetupIconFile=HFH.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
InternalCompressLevel=ultra
CompressionThreads=auto

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "indonesian"; MessagesFile: "compiler:Languages\Indonesian.isl"

[Tasks]
Name: "desktopicon";        Description: "{cm:CreateDesktopIcon}";      GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon";    Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; --- Semua isi dist\ndb_processor_gui.dist → {app} ---
Source: "dist\ndb_processor_gui.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\TA Processing Tool.exe\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "HFH.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
; Buat struktur folder utama di Documents
Name: "{userdocs}\NDB CSV Processor";                Permissions: users-full
Name: "{userdocs}\NDB CSV Processor\output";         Permissions: users-full
Name: "{userdocs}\NDB CSV Processor\input";          Permissions: users-full



[Icons]
Name: "{group}\TA Daily Process Tool"; Filename: "{app}\TA Processing Tool.exe"; IconFilename: "{app}\HFH.ico"
Name: "{group}\{cm:ProgramOnTheWeb,TA Daily Process Tool}"; Filename: "{#MyAppURL}"
Name: "{group}\{cm:UninstallProgram,TA Daily Process Tool}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\TA Daily Process Tool"; Filename: "{app}\TA Processing Tool.exe"; IconFilename: "{app}\HFH.ico"; Tasks: desktopicon


[Run]
Filename: "{app}\TA Processing Tool.exe"; Description: "{cm:LaunchProgram,TA Daily Process Tool}"; Flags: nowait postinstall skipifsilent


[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

procedure InitializeWizard;
begin
  WizardForm.LicenseAcceptedRadio.Checked := True;
end;
