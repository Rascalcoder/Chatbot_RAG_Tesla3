"""
Streamlit főalkalmazás
RAG alapú AI asszisztens webes felülete
"""

import streamlit as st
import os
import sys
import logging
from pathlib import Path
import tempfile
import uuid
from typing import List, Dict, Any, Optional

# Projekt mappa hozzáadása a PYTHONPATH-hoz
project_dir = Path(__file__).parent.absolute()
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

# Logging beállítása
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# RAG rendszer import
from src.rag_system import RAGSystem
# HF auth helper: ensure token is loaded from env or token file (but token file is ignored by git)
from src.utils.hf_auth import ensure_hf_token_env

# Ensure HF token env is set if available (does not create a token)
_hf_token = ensure_hf_token_env()
HF_TOKEN_PRESENT = bool(_hf_token)
from src.utils.session_manager import SessionManager
from src.monitoring.analytics import Analytics
from src.monitoring.metrics import MetricsCollector

# -----------------------------
# UI helper functions
# -----------------------------
def _get_doc_count() -> int:
    try:
        stats = st.session_state.rag_system.get_stats()
        return int(stats.get("vector_db", {}).get("document_count", 0) or 0)
    except Exception:
        return 0


def _new_chat_session():
    """Create a new conversation (keeps vector DB, clears chat history)."""
    st.session_state.current_session_id = st.session_state.session_manager.create_session()
    st.session_state.messages = []


def _format_source(doc: Dict[str, Any], idx: int) -> str:
    md = doc.get("metadata", {}) or {}
    file_name = md.get("file_name") or md.get("source") or "Ismeretlen fájl"
    chunk_index = md.get("chunk_index")

    parts = [f"**[{idx}]** `{file_name}`"]
    if chunk_index is not None:
        parts.append(f"(chunk: {chunk_index})")
    if doc.get("similarity") is not None:
        try:
            parts.append(f"sim: {float(doc.get('similarity')):.2f}")
        except Exception:
            pass
    if doc.get("rerank_score") is not None:
        try:
            parts.append(f"rerank: {float(doc.get('rerank_score')):.2f}")
        except Exception:
            pass

    return " ".join(parts)


def _handle_feedback(message_id: str, rating: str, query: str = None, response: str = None):
    """Handle user feedback submission"""
    try:
        if st.session_state.rag_system and st.session_state.rag_system.metrics_collector:
            st.session_state.rag_system.metrics_collector.record_user_feedback(
                message_id=message_id,
                rating=rating,
                query=query,
                response=response
            )
            return True
    except Exception as e:
        logger.error(f"Feedback rögzítési hiba: {e}")
        return False
    return False


def _render_message(message: Dict[str, Any], show_sources: bool, show_feedback: bool = True):
    role = message.get("role", "assistant")
    content = message.get("content", "")
    context = message.get("context")
    message_id = message.get("message_id", str(uuid.uuid4()))

    with st.chat_message(role):
        st.markdown(content)

        if show_sources and role == "assistant" and context:
            with st.expander("Források / Kontextus", expanded=False):
                for i, doc in enumerate(context, 1):
                    st.markdown(_format_source(doc, i))
                    text = (doc.get("text") or "").strip()
                    if text:
                        st.caption(text[:800] + ("…" if len(text) > 800 else ""))

        # Feedback gombok asszisztens válaszokhoz
        if show_feedback and role == "assistant" and st.session_state.rag_system:
            feedback_key = f"feedback_{message_id}"

            # Ha még nincs feedback adva
            if feedback_key not in st.session_state:
                st.caption("Hasznos volt ez a válasz?")
                col1, col2, col3 = st.columns([1, 1, 8])

                with col1:
                    if st.button("👍", key=f"pos_{message_id}", help="Hasznos"):
                        if _handle_feedback(message_id, "positive", response=content):
                            st.session_state[feedback_key] = "positive"
                            st.rerun()

                with col2:
                    if st.button("👎", key=f"neg_{message_id}", help="Nem hasznos"):
                        if _handle_feedback(message_id, "negative", response=content):
                            st.session_state[feedback_key] = "negative"
                            st.rerun()
            else:
                # Feedback már meg lett adva
                rating = st.session_state[feedback_key]
                icon = "👍" if rating == "positive" else "👎"
                st.caption(f"{icon} Köszönjük a visszajelzést!")

# Oldal konfiguráció
st.set_page_config(
    page_title="RAG AI Asszisztens",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state inicializálása - LAZY LOADING!
# Ne töltsd be a RAG rendszert az oldal betöltésekor!
if 'rag_system' not in st.session_state:
    st.session_state.rag_system = None  # Később töltődik be
    logger.info("RAG rendszer placeholder létrehozva (lazy loading)")

if 'session_manager' not in st.session_state:
    st.session_state.session_manager = SessionManager()

if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = st.session_state.session_manager.create_session()

if 'messages' not in st.session_state:
    st.session_state.messages = []

# Főoldal
def main_page():
    """Főoldal - Chat és dokumentum feltöltés"""
    # Inform user if HF token not present
    if not HF_TOKEN_PRESENT:
        st.warning(
            "HuggingFace token nincs beállítva. Futtasd `huggingface-cli login` vagy állítsd be a HUGGINGFACE_HUB_TOKEN környezeti változót (ne commit-oljuk)."
        )

    st.title("🤖 RAG Alapú AI Asszisztens")
    st.markdown("---")
    
    # Sidebar - Dokumentum feltöltés
    with st.sidebar:
        st.header("📄 Dokumentum Feltöltés")

        st.subheader("💬 Chat vezérlés")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Új chat", use_container_width=True):
                _new_chat_session()
                st.rerun()
        with col_b:
            if st.button("Chat törlése", use_container_width=True):
                st.session_state.messages = []
                st.rerun()

        show_sources = st.toggle("Források megjelenítése", value=True)
        
        uploaded_files = st.file_uploader(
            "Válassz dokumentumokat",
            type=['pdf', 'txt', 'docx'],
            accept_multiple_files=True
        )
        
        if st.button("Dokumentumok Hozzáadása", type="primary"):
            if not uploaded_files:
                st.warning("Előbb válassz ki legalább 1 fájlt.")
            else:
                # LAZY LOADING: RAG rendszer inicializálása MOST!
                if st.session_state.rag_system is None:
                    with st.spinner("🔄 RAG rendszer inicializálása... (első alkalommal 10-20 perc, modellek letöltése)"):
                        try:
                            st.session_state.rag_system = RAGSystem()
                            st.success("✅ RAG rendszer betöltve!")
                            logger.info("RAG rendszer inicializálva (lazy)")
                        except Exception as e:
                            st.error(f"❌ RAG rendszer inicializálási hiba: {e}")
                            logger.error(f"RAG init hiba: {e}")
                            st.stop()
                
                with st.spinner("Dokumentumok feldolgozása..."):
                    # Fájlok mentése ideiglenes könyvtárba
                    temp_dir = Path(tempfile.mkdtemp())
                    file_paths = []
                    
                    for uploaded_file in uploaded_files:
                        file_path = temp_dir / uploaded_file.name
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        file_paths.append(str(file_path))
                    
                    # Dokumentumok hozzáadása a RAG rendszerhez
                    try:
                        st.session_state.rag_system.add_documents(file_paths)
                        st.success(f"{len(file_paths)} dokumentum sikeresen hozzáadva!")
                    except Exception as e:
                        st.error(f"Hiba a dokumentumok hozzáadásánál: {e}")
                        logger.error(f"Dokumentum hozzáadás hiba: {e}")
        
        st.markdown("---")
        st.header("ℹ️ Információk")
        
        # Rendszer statisztikák
        doc_count = _get_doc_count()
        st.metric("Dokumentumok (vector DB)", doc_count)
        st.caption(f"Session: `{st.session_state.current_session_id}`")
    
    # Chat felület
    st.header("💬 Chat")
    
    # Üzenetek megjelenítése
    for message in st.session_state.messages:
        _render_message(message, show_sources=show_sources)
    
    # Chat input ellenőrzések
    if st.session_state.rag_system is None:
        st.info("📋 Előbb tölts fel legalább 1 dokumentumot a bal oldalon! (Ez inicializálja a RAG rendszert)")
        return
    
    doc_count = _get_doc_count()
    if doc_count <= 0:
        st.info("📄 Dokumentum feltöltve, de nincs a vector store-ban. Próbáld újra feltölteni.")
        return

    if prompt := st.chat_input("Kérdezz valamit a dokumentumokról..."):
        # Felhasználó üzenet hozzáadása
        user_msg_id = str(uuid.uuid4())
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "message_id": user_msg_id
        })
        st.session_state.session_manager.add_message(
            st.session_state.current_session_id,
            "user",
            prompt
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        # Asszisztens válasz generálása
        assistant_msg_id = str(uuid.uuid4())
        with st.chat_message("assistant"):
            try:
                # Streaming válasz
                response = st.session_state.rag_system.query(prompt, stream=True)

                message_placeholder = st.empty()
                full_response = ""
                context_docs = response.get("context") or []

                # buffereljük, ha karakterenként jön (ne frissítsünk túl gyakran)
                buffer = ""
                for chunk in response["generator"]:
                    buffer += chunk
                    if len(buffer) >= 32:
                        full_response += buffer
                        buffer = ""
                        message_placeholder.markdown(full_response + "▌")

                if buffer:
                    full_response += buffer
                    message_placeholder.markdown(full_response + "▌")

                message_placeholder.markdown(full_response)

                if show_sources and context_docs:
                    with st.expander("Források / Kontextus", expanded=False):
                        for i, doc in enumerate(context_docs, 1):
                            st.markdown(_format_source(doc, i))
                            text = (doc.get("text") or "").strip()
                            if text:
                                st.caption(text[:800] + ("…" if len(text) > 800 else ""))

                # Feedback gombok
                st.caption("Hasznos volt ez a válasz?")
                col1, col2, col3 = st.columns([1, 1, 8])

                feedback_key = f"feedback_{assistant_msg_id}"
                with col1:
                    if st.button("👍", key=f"pos_{assistant_msg_id}", help="Hasznos"):
                        if _handle_feedback(assistant_msg_id, "positive", query=prompt, response=full_response):
                            st.session_state[feedback_key] = "positive"

                with col2:
                    if st.button("👎", key=f"neg_{assistant_msg_id}", help="Nem hasznos"):
                        if _handle_feedback(assistant_msg_id, "negative", query=prompt, response=full_response):
                            st.session_state[feedback_key] = "negative"

                # Válasz mentése
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response,
                    "context": context_docs,
                    "message_id": assistant_msg_id
                })
                st.session_state.session_manager.add_message(
                    st.session_state.current_session_id,
                    "assistant",
                    full_response,
                    metadata={"context": context_docs},
                )
            
            except Exception as e:
                error_message = f"Hiba történt: {str(e)}"
                st.error(error_message)
                logger.error(f"Chat hiba: {e}")
                st.session_state.messages.append({"role": "assistant", "content": error_message})
                st.session_state.session_manager.add_message(
                    st.session_state.current_session_id,
                    "assistant",
                    error_message,
                    metadata={"error": True},
                )


# Monitoring oldal
def monitoring_page():
    """Monitoring és analitika oldal"""
    st.title("📊 Monitoring és Analitika")
    st.markdown("---")
    
    try:
        metrics_collector = st.session_state.rag_system.metrics_collector
        analytics = Analytics(metrics_collector)
        
        # Statisztikák
        stats = metrics_collector.get_statistics(days=30)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("LLM Hívások", stats.get('total_llm_calls', 0))
        with col2:
            st.metric("Összes Tokenek", f"{stats.get('total_tokens', 0):,}")
        with col3:
            st.metric("Összes Költség", f"${stats.get('total_cost_usd', 0):.4f}")
        with col4:
            avg_time = stats.get('avg_total_time_sec', 0)
            st.metric("Átlagos Válaszidő", f"{avg_time:.2f}s" if avg_time else "N/A")
        
        st.markdown("---")
        
        # Napi használat grafikon
        st.subheader("Napi Használat")
        daily_usage = analytics.get_daily_usage(days=30)
        
        if not daily_usage.empty:
            import plotly.express as px
            
            fig = px.line(
                daily_usage,
                x='date',
                y='total_tokens',
                title='Napi Token Használat',
                labels={'date': 'Dátum', 'total_tokens': 'Tokenek'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Latency trendek
        st.subheader("Latency Trendek")
        latency_trends = analytics.get_latency_trends(days=7)
        
        if not latency_trends.empty:
            import plotly.express as px
            
            fig = px.line(
                latency_trends,
                x='date',
                y=['first_token_time', 'total_time'],
                title='Latency Trendek',
                labels={'date': 'Dátum', 'value': 'Idő (másodperc)'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Modell használat
        st.subheader("Modell Használat")
        model_usage = analytics.get_model_usage()

        if model_usage:
            import pandas as pd
            df = pd.DataFrame(model_usage).T.reset_index()
            df.columns = ['Modell', 'Tokenek', 'Költség', 'Hívások']
            st.dataframe(df, use_container_width=True)

        st.markdown("---")

        # Felhasználói Feedback
        st.subheader("📝 Felhasználói Feedback")
        feedback_stats = metrics_collector.get_feedback_statistics(days=30)

        if feedback_stats.get('total_feedbacks', 0) > 0:
            # Feedback metrikák
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Összes Feedback", feedback_stats.get('total_feedbacks', 0))
            with col2:
                st.metric("👍 Pozitív", feedback_stats.get('positive', 0))
            with col3:
                st.metric("👎 Negatív", feedback_stats.get('negative', 0))
            with col4:
                satisfaction = feedback_stats.get('satisfaction_score', 0)
                st.metric("Elégedettség", f"{satisfaction:.1f}%")

            # Feedback eloszlás (Pie chart)
            feedback_dist = analytics.get_feedback_distribution()
            if any(feedback_dist.values()):
                import plotly.express as px

                fig = px.pie(
                    values=list(feedback_dist.values()),
                    names=list(feedback_dist.keys()),
                    title='Feedback Eloszlás',
                    color_discrete_map={'positive': '#00CC96', 'negative': '#EF553B', 'neutral': '#636EFA'}
                )
                st.plotly_chart(fig, use_container_width=True)

            # Legutóbbi kommentek
            recent_comments = feedback_stats.get('recent_comments', [])
            if recent_comments:
                st.subheader("Legutóbbi Visszajelzések")
                for comment_data in recent_comments:
                    rating = comment_data.get('rating', 'neutral')
                    icon = "👍" if rating == 'positive' else "👎" if rating == 'negative' else "➖"
                    query = comment_data.get('query', 'N/A')
                    comment = comment_data.get('comment', '')
                    timestamp = comment_data.get('timestamp', '')

                    st.markdown(f"**{icon} {rating.upper()}** - {timestamp[:10]}")
                    st.caption(f"Kérdés: {query}")
                    if comment:
                        st.info(comment)
        else:
            st.info("Még nincs felhasználói feedback. A chat-ben adj visszajelzést a válaszokhoz!")

    except Exception as e:
        st.error(f"Hiba a monitoring betöltésénél: {e}")
        logger.error(f"Monitoring hiba: {e}")


# Evaluation oldal
def evaluation_page():
    """Evaluation oldal"""
    st.title("🧪 Evaluation")
    st.markdown("---")
    
    st.info("Az evaluation funkciók fejlesztés alatt állnak. A teszt esetek futtatásához használd a parancssort.")
    
    st.subheader("Evaluation Típusok")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### RAG Szintű")
        st.markdown("- Retrieval minőség")
        st.markdown("- Embedding teljesítmény")
        st.markdown("- Chunking hatékonyság")
    
    with col2:
        st.markdown("### Prompt Szintű")
        st.markdown("- Context relevance")
        st.markdown("- Hallucináció detektálás")
        st.markdown("- LLM-as-Judge")
    
    with col3:
        st.markdown("### Alkalmazás Szintű")
        st.markdown("- User journey")
        st.markdown("- Response quality")
        st.markdown("- Latency metrikák")


# Fő navigáció
def main():
    """Fő függvény"""
    pages = {
        "🏠 Főoldal": main_page,
        "📊 Monitoring": monitoring_page,
        "🧪 Evaluation": evaluation_page
    }
    
    # Sidebar navigáció
    st.sidebar.title("Navigáció")
    selected_page = st.sidebar.radio("Válassz oldalt", list(pages.keys()))
    
    # Kiválasztott oldal megjelenítése
    pages[selected_page]()


if __name__ == "__main__":
    main()

