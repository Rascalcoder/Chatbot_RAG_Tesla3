"""
MŰKÖDŐ CHATBOT - OpenAI alapú
Gyors betöltés, azonnal használható
"""

import streamlit as st
import os
from pathlib import Path
import tempfile
from typing import List, Dict, Any
import PyPDF2
from openai import OpenAI

# Oldal konfiguráció
st.set_page_config(
    page_title="RAG Chatbot (OpenAI)",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# OpenAI client inicializálása
@st.cache_resource
def get_openai_client():
    api_key = os.getenv('OPENAI_API_KEY', 'your-api-key-here')
    if api_key == 'your-api-key-here':
        st.error("⚠️ OPENAI_API_KEY nincs beállítva! Állítsd be környezeti változóban vagy írsd be alább.")
        return None
    return OpenAI(api_key=api_key)

# PDF szöveg kinyerés
def extract_text_from_pdf(pdf_path: str) -> str:
    """PDF szöveg kinyerése"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"PDF olvasási hiba: {e}")
        return ""

# Egyszerű chunking
def simple_chunk(text: str, chunk_size: int = 1000) -> List[str]:
    """Egyszerű chunking"""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

# Chat függvény OpenAI-val
def chat_with_openai(client: OpenAI, query: str, context: str) -> str:
    """OpenAI chat"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Gyors és olcsó
            messages=[
                {
                    "role": "system",
                    "content": "Te egy segítőkész AI asszisztens vagy. Válaszolj a kérdésekre a megadott dokumentum alapján. Ha az információ nincs a dokumentumban, mondd meg."
                },
                {
                    "role": "user",
                    "content": f"Dokumentum kontextus:\n{context}\n\nKérdés: {query}"
                }
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Hiba: {str(e)}"

# Session state inicializálás
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'document_text' not in st.session_state:
    st.session_state.document_text = ""
if 'api_key_input' not in st.session_state:
    st.session_state.api_key_input = ""

# Főoldal
st.title("🤖 RAG Chatbot (OpenAI)")
st.markdown("**Gyors, működő verzió OpenAI API-val**")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Beállítások")
    
    # API Key input
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=st.session_state.api_key_input,
        help="Szerezz API kulcsot: https://platform.openai.com/api-keys"
    )
    
    if api_key:
        os.environ['OPENAI_API_KEY'] = api_key
        st.session_state.api_key_input = api_key
        st.success("✅ API kulcs beállítva")
    else:
        st.warning("⚠️ API kulcs szükséges")
    
    st.markdown("---")
    st.header("📄 Dokumentum Feltöltés")
    
    uploaded_file = st.file_uploader(
        "Válassz PDF dokumentumot",
        type=['pdf'],
        help="Csak PDF támogatott"
    )
    
    if st.button("Dokumentum Feldolgozása", type="primary", disabled=not uploaded_file):
        if uploaded_file:
            with st.spinner("PDF feldolgozása..."):
                # Fájl mentése
                temp_dir = Path(tempfile.mkdtemp())
                file_path = temp_dir / uploaded_file.name
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Szöveg kinyerése
                text = extract_text_from_pdf(str(file_path))
                
                if text:
                    st.session_state.document_text = text
                    st.success(f"✅ {len(text)} karakter feldolgozva!")
                else:
                    st.error("❌ Nem sikerült a PDF feldolgozása")
    
    st.markdown("---")
    st.header("ℹ️ Információk")
    
    if st.session_state.document_text:
        st.metric("Dokumentum", "✅ Feltöltve")
        st.caption(f"{len(st.session_state.document_text)} karakter")
    else:
        st.metric("Dokumentum", "❌ Nincs")
    
    if st.button("🔄 Chat Törlése"):
        st.session_state.messages = []
        st.rerun()

# Chat felület
st.header("💬 Chat")

# Üzenetek megjelenítése
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if not st.session_state.document_text:
    st.info("📋 **Először tölts fel egy PDF dokumentumot a bal oldalon!**")
elif not api_key:
    st.warning("⚠️ **OpenAI API kulcs szükséges a chathez!**")
else:
    if prompt := st.chat_input("Kérdezz valamit a dokumentumról..."):
        # Felhasználó üzenet
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Asszisztens válasz
        with st.chat_message("assistant"):
            with st.spinner("Gondolkodom..."):
                client = get_openai_client()
                
                if client:
                    # Egyszerű keresés a dokumentumban (első 3000 karakter kontextusként)
                    context = st.session_state.document_text[:3000]
                    
                    # Ha a kérdésben van kulcsszó, keressük meg
                    query_lower = prompt.lower()
                    words = query_lower.split()
                    
                    # Próbáljuk megtalálni a releváns részt
                    best_context = context
                    for word in words:
                        if len(word) > 3:  # Csak hosszabb szavak
                            idx = st.session_state.document_text.lower().find(word)
                            if idx != -1:
                                # 1500 karakter a találat körül
                                start = max(0, idx - 750)
                                end = min(len(st.session_state.document_text), idx + 750)
                                best_context = st.session_state.document_text[start:end]
                                break
                    
                    answer = chat_with_openai(client, prompt, best_context)
                    st.markdown(answer)
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer
                    })
                else:
                    error_msg = "❌ OpenAI client inicializálási hiba"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })

# Footer
st.markdown("---")
st.caption("💡 **Működő chatbot OpenAI GPT-4o-mini-vel** | Gyors és megbízható")

with st.expander("🔧 Használati útmutató"):
    st.markdown("""
    ### Lépések:
    
    1. **OpenAI API Key beszerzése**:
       - Menj ide: https://platform.openai.com/api-keys
       - Jelentkezz be vagy regisztrálj
       - Készíts új API kulcsot
       - Másold be a bal oldali mezőbe
    
    2. **PDF feltöltés**:
       - Kattints a "Browse files" gombra
       - Válassz egy PDF fájlt (pl. model_3.pdf)
       - Kattints "Dokumentum Feldolgozása"
       - Várj (~5 másodperc)
    
    3. **Chat használat**:
       - Írd be a kérdésedet
       - Nyomj Enter-t
       - Várd meg a választ (~2-5 másodperc)
    
    ### Költségek:
    - GPT-4o-mini: ~$0.15/1M input token, ~$0.60/1M output token
    - Átlagos kérdés: ~0.001-0.005 USD
    - 100 kérdés: ~$0.10-0.50
    
    ### Miért ez működik?
    - ✅ Nincs modell letöltés (OpenAI felhőben)
    - ✅ Gyors válaszok (2-5 mp)
    - ✅ Egyszerű architektúra
    - ✅ Nincs GPU szükség
    """)

