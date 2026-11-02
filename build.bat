@echo off
chcp 65001 > nul

python --version > /dev/null 2>&1
if errorlevel 1 (
    echo Python not found. Install 64-bit Python 3.13 from https://www.python.org/downloads/
    pause
    exit /b 1
)

python -c "import struct; bits=struct.calcsize('P')*8; exit(0 if bits==64 else 1)"
if errorlevel 1 (
    echo ERROR: 32-bit Python detected. Please install 64-bit Python 3.13.
    pause
    exit /b 1
)

echo [1/3] Installing packages...
pip install pyinstaller pyside6 requests --quiet
if errorlevel 1 (
    echo Package installation failed.
    pause
    exit /b 1
)

echo [2/3] Building EXE...

pyinstaller --noconfirm --onefile --windowed --name "MuBig_UI v2.4" --icon "asset\logo\Mubig.ico" --add-data "asset;asset" --add-data "MuBig_config.json;." --hidden-import "PySide6.QtCore" --hidden-import "PySide6.QtGui" --hidden-import "PySide6.QtWidgets" --hidden-import "PySide6.QtNetwork" --hidden-import "requests" --hidden-import "src" --hidden-import "src.auth" --hidden-import "src.installer" --hidden-import "src.settings" --hidden-import "src.ui" --hidden-import "src.ui.main_window" --hidden-import "src.ui.install_tab" --hidden-import "src.ui.settings_tab" --hidden-import "src.ui.custom_widgets" --hidden-import "src.ui.styles" --hidden-import "src.ui.wtf_file_dialog" --hidden-import "src.utils" --hidden-import "src.utils.file_handler" --hidden-import "src.utils.game_paths" main.py

if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

echo.
echo [3/3] Done! Output: dist\MuBig_UI v2.4.exe
echo.
pause
