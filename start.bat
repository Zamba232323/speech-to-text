@echo off
call "%~dp0.venv\Scripts\activate.bat"
pythonw "%~dp0stt.py" %*
