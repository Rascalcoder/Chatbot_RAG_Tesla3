@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Starting TEST Streamlit...
echo.
python -m streamlit run app_simple.py --server.port 8502
pause


