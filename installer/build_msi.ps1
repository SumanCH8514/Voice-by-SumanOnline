param(
    [string]$OutputDir = "$PSScriptRoot\dist"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$MsiPath = Join-Path $OutputDir "Voice-by-SumanOnline-Setup.msi"
if (Test-Path $MsiPath) {
    Remove-Item $MsiPath -Force
}

$installer = New-Object -ComObject WindowsInstaller.Installer
$database = $installer.OpenDatabase($MsiPath, 3)

$schemaQueries = @(
    "CREATE TABLE Property (Property CHAR(72) NOT NULL, Value CHAR(255) NOT NULL PRIMARY KEY Property)",
    "CREATE TABLE Directory (Directory CHAR(72) NOT NULL, Directory_Parent CHAR(72), DefaultDir CHAR(255) NOT NULL PRIMARY KEY Directory)",
    "CREATE TABLE Component (Component CHAR(72) NOT NULL, ComponentId CHAR(38), Directory_ CHAR(72) NOT NULL, Attributes INTEGER NOT NULL, Condition CHAR(255), KeyPath CHAR(72) PRIMARY KEY Component)",
    "CREATE TABLE Feature (Feature CHAR(38) NOT NULL, Feature_Parent CHAR(38), Title CHAR(64), Description CHAR(255), Display INTEGER NOT NULL, Level INTEGER NOT NULL, Directory_ CHAR(72), Attributes INTEGER NOT NULL PRIMARY KEY Feature)",
    "CREATE TABLE FeatureComponents (Feature_ CHAR(38) NOT NULL, Component_ CHAR(72) NOT NULL PRIMARY KEY Feature_, Component_)",
    "CREATE TABLE Media (DiskId INTEGER NOT NULL, LastSequence INTEGER NOT NULL, DiskPrompt CHAR(64), Cabinet CHAR(255), VolumeLabel CHAR(32), Source CHAR(32) PRIMARY KEY DiskId)",
    "CREATE TABLE CustomAction (Action CHAR(72) NOT NULL, Type INTEGER NOT NULL, Source CHAR(72), Target CHAR(255), ExtendedType LONG PRIMARY KEY Action)",
    "CREATE TABLE InstallExecuteSequence (Action CHAR(72) NOT NULL, Condition CHAR(255), Sequence INTEGER PRIMARY KEY Action)",
    "CREATE TABLE InstallUISequence (Action CHAR(72) NOT NULL, Condition CHAR(255), Sequence INTEGER PRIMARY KEY Action)",
    "CREATE TABLE AdminExecuteSequence (Action CHAR(72) NOT NULL, Condition CHAR(255), Sequence INTEGER PRIMARY KEY Action)"
)

foreach ($sql in $schemaQueries) {
    $v = $database.OpenView($sql)
    $v.Execute()
    $v.Close()
}

$productCode = [System.Guid]::NewGuid().ToString("B").ToUpper()
$upgradeCode = "{9B450690-D629-44F0-91E7-29CC2BBCB0B9}"

$properties = @(
    @("ProductCode", $productCode),
    @("ProductName", "Voice by SumanOnline"),
    @("ProductVersion", "0.1.0"),
    @("Manufacturer", "SumanOnline"),
    @("ProductLanguage", "1033"),
    @("UpgradeCode", $upgradeCode),
    @("ALLUSERS", "2"),
    @("MSIINSTALLPERUSER", "1"),
    @("ARPNOMODIFY", "1"),
    @("ARPNOREPAIR", "1")
)

foreach ($prop in $properties) {
    $q = "INSERT INTO Property (Property, Value) VALUES ('$($prop[0])', '$($prop[1])')"
    $v = $database.OpenView($q)
    $v.Execute()
    $v.Close()
}

$dirs = @(
    @("TARGETDIR", "null", "SourceDir"),
    @("SystemFolder", "'TARGETDIR'", "."),
    @("LocalAppDataFolder", "'TARGETDIR'", "."),
    @("ProgramsFolder", "'LocalAppDataFolder'", "Programs"),
    @("INSTALLDIR", "'ProgramsFolder'", "Voice by SumanOnline:Voice")
)

foreach ($d in $dirs) {
    $q = "INSERT INTO Directory (Directory, Directory_Parent, DefaultDir) VALUES ('$($d[0])', $($d[1]), '$($d[2])')"
    $v = $database.OpenView($q)
    $v.Execute()
    $v.Close()
}

$compGuid = [System.Guid]::NewGuid().ToString("B").ToUpper()
$qComp = "INSERT INTO Component (Component, ComponentId, Directory_, Attributes) VALUES ('MainAppComp', '$compGuid', 'INSTALLDIR', 0)"
$v = $database.OpenView($qComp)
$v.Execute()
$v.Close()

$qFeat = "INSERT INTO Feature (Feature, Title, Description, Display, Level, Directory_, Attributes) VALUES ('MainFeature', 'Voice by SumanOnline', 'Complete AI Voice Dictation App', 1, 1, 'INSTALLDIR', 0)"
$v = $database.OpenView($qFeat)
$v.Execute()
$v.Close()

$qFC = "INSERT INTO FeatureComponents (Feature_, Component_) VALUES ('MainFeature', 'MainAppComp')"
$v = $database.OpenView($qFC)
$v.Execute()
$v.Close()

$qMedia = "INSERT INTO Media (DiskId, LastSequence, DiskPrompt) VALUES (1, 1, 'Disk 1')"
$v = $database.OpenView($qMedia)
$v.Execute()
$v.Close()

$setupScriptPath = "$ProjectRoot\installer\install.ps1"
$escapedScript = $setupScriptPath.Replace("'", "''")
$qCA = "INSERT INTO CustomAction (Action, Type, Source, Target) VALUES ('RunInstallSetup', 3106, 'SystemFolder', 'powershell.exe -ExecutionPolicy Bypass -File ""$escapedScript""')"
$v = $database.OpenView($qCA)
$v.Execute()
$v.Close()

$actions = @(
    @("CostInitialize", 800),
    @("CostFinalize", 1000),
    @("InstallValidate", 1400),
    @("InstallInitialize", 1500),
    @("ProcessComponents", 1600),
    @("UnpublishFeatures", 1800),
    @("RegisterUser", 6000),
    @("RegisterProduct", 6100),
    @("PublishFeatures", 6300),
    @("PublishProduct", 6400),
    @("RunInstallSetup", 6500),
    @("InstallFinalize", 6600)
)

foreach ($act in $actions) {
    $q = "INSERT INTO InstallExecuteSequence (Action, Sequence) VALUES ('$($act[0])', $($act[1]))"
    $v = $database.OpenView($q)
    $v.Execute()
    $v.Close()
}

$uiActions = @(
    @("CostInitialize", 800),
    @("CostFinalize", 1000),
    @("ExecuteAction", 1300)
)

foreach ($u in $uiActions) {
    $q = "INSERT INTO InstallUISequence (Action, Sequence) VALUES ('$($u[0])', $($u[1]))"
    $v = $database.OpenView($q)
    $v.Execute()
    $v.Close()
}

$summary = $database.SummaryInformation(20)
$summary.Property(2) = "Voice by SumanOnline Setup"
$summary.Property(3) = "Voice by SumanOnline Installation"
$summary.Property(4) = "SumanOnline"
$summary.Property(7) = "x64;1033"
$summary.Property(9) = [System.Guid]::NewGuid().ToString("B").ToUpper()
$summary.Property(14) = 200
$summary.Property(15) = 0
$summary.Persist()

$database.Commit()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($database) | Out-Null
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($installer) | Out-Null

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Windows Installer (.msi) successfully created!" -ForegroundColor Green
Write-Host " Output file: $MsiPath" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
