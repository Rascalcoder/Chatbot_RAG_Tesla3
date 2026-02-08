@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ====================================== > diagnose_log.txt
echo DIAGNOSTIC LOG >> diagnose_log.txt
echo ====================================== >> diagnose_log.txt
echo. >> diagnose_log.txt

echo [1] Python version: >> diagnose_log.txt
python --version >> diagnose_log.txt 2>&1
echo. >> diagnose_log.txt

echo [2] Streamlit import test: >> diagnose_log.txt
python -c "import streamlit; print('Streamlit OK:', streamlit.__version__)" >> diagnose_log.txt 2>&1
echo. >> diagnose_log.txt

echo [3] Pandas/Numpy test: >> diagnose_log.txt
python -c "import pandas, numpy; print('pandas:', pandas.__version__); print('numpy:', numpy.__version__)" >> diagnose_log.txt 2>&1
echo. >> diagnose_log.txt

echo [4] Langchain test: >> diagnose_log.txt
python -c "from langchain_text_splitters import RecursiveCharacterTextSplitter; print('langchain_text_splitters OK')" >> diagnose_log.txt 2>&1
echo. >> diagnose_log.txt

echo [5] RAG system import test: >> diagnose_log.txt
python -c "import sys; sys.path.insert(0, '.'); from src.rag_system import RAGSystem; print('RAGSystem OK')" >> diagnose_log.txt 2>&1
echo. >> diagnose_log.txt

echo ====================================== >> diagnose_log.txt
echo DONE - Check diagnose_log.txt >> diagnose_log.txt
echo ====================================== >> diagnose_log.txt

echo.
echo Diagnostic log saved to: diagnose_log.txt
echo.
pause


