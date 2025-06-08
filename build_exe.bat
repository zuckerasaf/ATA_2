@echo off
echo Building executable...

REM Activate virtual environment
call venv\Scripts\activate

REM Clean up old build files
echo Cleaning up old build files...
if exist "dist" rd /s /q "dist"
if exist "build" rd /s /q "build"
if exist "control_panel.spec" del "control_panel.spec"

REM Create spec file
echo Creating spec file...
pyi-makespec ^
    --onefile ^
    --add-data "src\utils\config.json;utils" ^
    --add-data "src\Doc\Doc_config.json;Doc" ^
    --hidden-import=tkinter ^
    --hidden-import=PIL ^
    --hidden-import=PIL.Image ^
    --hidden-import=PIL.ImageTk ^
    --hidden-import=PIL.ImageFont ^
    --hidden-import=PIL.ImageDraw ^
    src\gui\control_panel.py

REM Build using spec file
echo Building executable...
pyinstaller --noconfirm ^
    --clean ^
    --log-level DEBUG ^
    control_panel.spec

echo Build complete!
echo The executable is in the dist folder.
echo.
echo To debug the executable:
echo 1. Open Command Prompt
echo 2. Navigate to the dist folder
echo 3. Run: control_panel.exe
echo 4. Check for any error messages
pause 