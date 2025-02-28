@echo off
:: Navigate to the script's directory
cd /d "%~dp0"

:: Check and install required Python packages
echo Installing required Python packages...
python -m pip install --upgrade pip
pip install discord aiohttp python-dotenv pyfiglet colorama rich

:: Run the Python script
echo Running Discord Server Cloner...
python main.py

:: Keep the window open after execution
echo.
pause
exit
