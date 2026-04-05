@echo off
echo ============================================
echo   Speech-to-Text Installer
echo ============================================
echo.
echo   Tento nastroj ti umozni diktovat text
echo   kamkoli pomoci klavesove zkratky Ctrl+Space.
echo.
echo   Jak to funguje:
echo     1. Ctrl+Space = zacni nahravat (cervene kolecko u kurzoru)
echo     2. Mluv cesky, klidne prepni okno, brouzdej...
echo     3. Ctrl+Space = zastav a vloz text tam kde je kurzor
echo.
echo   Pozadavky: Python 3.10+, mikrofon
echo   GPU (NVIDIA): volitelne, zrychluje prepis
echo.
echo ============================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python nebyl nalezen.
    echo   1. Stahni Python 3.10+ z https://python.org
    echo   2. Pri instalaci ZATRNI "Add Python to PATH"
    echo   3. Spust tento skript znovu
    pause
    exit /b 1
)

echo [1/4] Vytvarim virtualni prostredi...
python -m venv .venv
if %ERRORLEVEL% neq 0 (
    echo ERROR: Nepodarilo se vytvorit virtualni prostredi.
    pause
    exit /b 1
)

echo [2/4] Instaluji zavislosti (muze trvat par minut)...
call .venv\Scripts\activate.bat
pip install -r requirements.txt --quiet
if %ERRORLEVEL% neq 0 (
    echo ERROR: Instalace zavislosti selhala.
    pause
    exit /b 1
)

echo [3/4] Kontroluji prostredi...
echo.
python setup_check.py
echo.

echo [4/4] Autostart
echo.
echo   Chces aby se Speech-to-Text spoustelo automaticky
echo   pri zapnuti pocitace? (Doporuceno)
echo.
set /p AUTOSTART="   Pridat do autostartu? [A/n]: "

if /i "%AUTOSTART%"=="n" (
    echo   Autostart preskocen. Spoustej rucne pres start.bat
) else (
    powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Startup') + '\Speech-to-Text.lnk'); $s.TargetPath = '%~dp0start.bat'; $s.WorkingDirectory = '%~dp0'; $s.WindowStyle = 7; $s.Description = 'Speech-to-Text (Ctrl+Space)'; $s.Save()"
    if %ERRORLEVEL% equ 0 (
        echo   Autostart pridan! Speech-to-Text se spusti pri startu PC.
    ) else (
        echo   VAROVANI: Nepodarilo se pridat autostart. Pridej rucne:
        echo   Zkopiruj start.bat do: shell:startup
    )
)

echo.
echo ============================================
echo   Instalace dokoncena!
echo.
echo   Spusteni: dvojklik na start.bat
echo   Ovladani: Ctrl+Space (start/stop nahravani)
echo ============================================
pause
