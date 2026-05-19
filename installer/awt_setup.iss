; Inno Setup 6 스크립트 — AWT v1.0 Windows 인스톨러 (D46)
; 빌드: ISCC.exe installer\awt_setup.iss

#define AppName "AWT"
#define AppVersion "1.0.0"
#define AppPublisher "AWT Team"
#define AppExeName "AWT.exe"
#define DistDir "..\dist\AWT"

[Setup]
AppId={{A3B2C1D0-E4F5-4A6B-8C7D-9E0F1A2B3C4D}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL=https://github.com/awt-team/awt
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=..\dist\installer
OutputBaseFilename=AWT_Setup_{#AppVersion}
SetupIconFile=awt.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
MinVersion=10.0.17763

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; PyInstaller COLLECT 출력 디렉터리 전체 포함
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 사용자 데이터(~/.awt)는 보존, 앱 디렉터리만 제거
Type: filesandordirs; Name: "{app}"

[Code]
// PostgreSQL 연결 환경변수 설정 안내
procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpFinished then
  begin
    MsgBox(
      'AWT 설치가 완료되었습니다.' + #13#10 + #13#10 +
      '실행 전 다음 환경변수를 설정하세요:' + #13#10 +
      '  AWT_DB_HOST, AWT_DB_PORT, AWT_DB_NAME,' + #13#10 +
      '  AWT_DB_USER, AWT_DB_PASSWORD' + #13#10 + #13#10 +
      'Playwright 브라우저를 설치하려면 cmd에서:' + #13#10 +
      '  playwright install chromium',
      mbInformation, MB_OK
    );
  end;
end;
