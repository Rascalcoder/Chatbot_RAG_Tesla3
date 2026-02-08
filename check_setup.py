#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ellenőrző script a Streamlit alkalmazás indításához
"""

import sys
import os

print("=" * 50)
print("RAG Asszisztens - Ellenőrző Script")
print("=" * 50)

# 1. Python verzió
print(f"\n1. Python verzió: {sys.version}")

# 2. Munkakönyvtár
print(f"\n2. Munkakönyvtár: {os.getcwd()}")

# 3. app.py létezik-e
app_exists = os.path.exists("app.py")
print(f"\n3. app.py létezik: {app_exists}")

# 4. Streamlit telepítve-e
try:
    import streamlit
    print(f"4. Streamlit telepítve: Igen (verzió: {streamlit.__version__})")
except ImportError:
    print("4. Streamlit telepítve: NEM")
    sys.exit(1)

# 5. src modul létezik-e
src_exists = os.path.exists("src")
print(f"\n5. src/ mappa létezik: {src_exists}")

# 6. RAGSystem import
try:
    sys.path.insert(0, os.getcwd())
    from src.rag_system import RAGSystem
    print("6. RAGSystem import: Sikeres")
except ImportError as e:
    print(f"6. RAGSystem import: HIBA - {e}")

# 7. Függőségek ellenőrzése
print("\n7. Főbb függőségek ellenőrzése:")
dependencies = {
    'streamlit': 'streamlit',
    'langchain': 'langchain',
    'chromadb': 'chromadb',
    'sentence_transformers': 'sentence-transformers',
    'transformers': 'transformers',
    'torch': 'torch',
}

for module_name, package_name in dependencies.items():
    try:
        __import__(module_name)
        print(f"   ✓ {package_name}")
    except ImportError:
        print(f"   ✗ {package_name} - HIÁNYZIK")

print("\n" + "=" * 50)
print("Ellenőrzés befejezve!")
print("=" * 50)

if app_exists:
    print("\nIndítás: python -m streamlit run app.py")
else:
    print("\nHIBA: app.py nem található a munkakönyvtárban!")

