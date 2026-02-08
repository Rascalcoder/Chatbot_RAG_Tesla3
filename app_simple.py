"""
Egyszerűsített Streamlit app - Gyors betöltés
RAG rendszer lazy loading-gal
"""

import streamlit as st
import os
from pathlib import Path

# Oldal konfiguráció
st.set_page_config(
    page_title="RAG AI Asszisztens",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Egyszerű státusz üzenet
st.title("🤖 RAG Alapú AI Asszisztens")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("📄 Dokumentum Feltöltés")
    
    st.info("⚠️ **Egyszerűsített verzió**: A teljes RAG rendszer betöltése hosszú időt vesz igénybe. Ez a verzió csak a felület tesztelésére szolgál.")
    
    uploaded_files = st.file_uploader(
        "Válassz dokumentumokat",
        type=['pdf', 'txt', 'docx'],
        accept_multiple_files=True
    )
    
    if st.button("Dokumentumok Hozzáadása", type="primary"):
        if not uploaded_files:
            st.warning("Előbb válassz ki legalább 1 fájlt.")
        else:
            st.success(f"{len(uploaded_files)} dokumentum kiválasztva!")
            st.info("🔄 A teljes RAG rendszer inicializálása folyamatban... (első alkalommal 10-20 perc)")
            
            # Itt inicializálnánk a RAG rendszert
            with st.spinner("RAG rendszer betöltése..."):
                try:
                    # Csak akkor importáljuk a RAG rendszert, ha tényleg használjuk
                    if 'rag_system' not in st.session_state:
                        st.write("🔄 RAG System importálása...")
                        from src.rag_system import RAGSystem
                        st.write("🔄 RAG System inicializálása...")
                        st.session_state.rag_system = RAGSystem()
                        st.write("✅ RAG System kész!")
                    
                    st.success("✅ RAG rendszer betöltve!")
                    
                except Exception as e:
                    st.error(f"❌ Hiba a RAG rendszer betöltésénél: {e}")
                    st.info("💡 **Megoldás**: Ez az első betöltés lehet, modellek letöltése folyik (~10GB). Várj türelemmel vagy indítsd újra az alkalmazást.")
    
    st.markdown("---")
    st.header("ℹ️ Információk")
    st.metric("Státusz", "Egyszerűsített mód")
    
    if st.button("🔄 Teljes verzió betöltése"):
        st.info("Átirányítás a teljes verzióra...")
        st.write("Indítsd újra az alkalmazást: `streamlit run app.py`")

# Chat felület
st.header("💬 Chat")

# Üzenetek
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Üzenetek megjelenítése
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
st.info("📋 **Tesztelés alatt**: Ez az egyszerűsített verzió. Tölts fel dokumentumokat a bal oldalon a teljes funkció aktiválásához.")

if prompt := st.chat_input("Kérdezz valamit..."):
    # Felhasználó üzenet
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Asszisztens válasz
    with st.chat_message("assistant"):
        if 'rag_system' in st.session_state:
            st.markdown("🔄 RAG rendszer válaszol...")
            try:
                response = st.session_state.rag_system.query(prompt, stream=False)
                answer = response.get('answer', 'Nincs válasz.')
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                error_msg = f"❌ Hiba: {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
        else:
            response = "⚠️ **RAG rendszer nincs betöltve**. Kérlek, tölts fel dokumentumokat a bal oldalon!"
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# Debug info
with st.expander("🔧 Debug információk"):
    st.write("**Session State:**")
    st.write(f"- RAG System betöltve: {'rag_system' in st.session_state}")
    st.write(f"- Üzenetek száma: {len(st.session_state.messages)}")
    st.write(f"- Python verzió: {os.sys.version}")
    
    st.write("\n**Környezet:**")
    st.write(f"- Munkakönyvtár: {os.getcwd()}")
    st.write(f"- Streamlit verzió: {st.__version__}")

st.markdown("---")
st.caption("💡 **Tipp**: Ha a teljes verzió nem tölt be, használd ezt az egyszerűsített módot tesztelésre.")
