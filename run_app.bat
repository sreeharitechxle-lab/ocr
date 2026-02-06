@echo off
cd /d "%~dp0"
echo Current directory: "%CD%"

echo Activating venv...
if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
) else (
    echo venv activation script specificed not found
)

echo Checking python...
where python
if %errorlevel% neq 0 (
    echo 'where python' failed. trying direct path again...
    if exist "venv\Scripts\python.exe" (
        "venv\Scripts\python.exe" --version
    )
)

echo Installing requirements...
pip install -r requirements.txt
if %errorlevel% neq 0 echo pip install failed

echo Running app...
python app.py
if %errorlevel% neq 0 (
   echo fallback run...
   "venv\Scripts\python.exe" app.py
)
pause
