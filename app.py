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
import pandas as pd

# Projekt mappa hozzáadása a PYTHONPATH-hoz
project_dir = Path(__file__).parent.absolute()
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

# Logging beállítása
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# RAG rendszer import
from src.rag_system import RAGSystem
from src.utils.session_manager import SessionManager
from src.monitoring.analytics import Analytics
from src.monitoring.metrics import MetricsCollector

# -----------------------------
# UI helper functions
# -----------------------------
def _get_doc_count() -> int:
    try:
        if st.session_state.rag_system is None:
            logger.warning("_get_doc_count: rag_system is None")
            return 0
        stats = st.session_state.rag_system.get_stats()
        doc_count = int(stats.get("vector_db", {}).get("document_count", 0) or 0)
        logger.info(f"_get_doc_count: {doc_count}")
        return doc_count
    except Exception as e:
        logger.error(f"_get_doc_count exception: {e}", exc_info=True)
        return 0


def _new_chat_session():
    """Create a new conversation (keeps vector DB, clears chat history)."""
    st.session_state.current_session_id = st.session_state.session_manager.create_session()
    st.session_state.messages = []


def _format_source(doc: Dict[str, Any], idx: int) -> str:
    md = doc.get("metadata", {}) or {}
    file_name = md.get("file_name") or md.get("source") or "Ismeretlen fájl"
    page_number = md.get("page_number")
    chunk_index = md.get("chunk_index")

    parts = [f"**[{idx}]** `{file_name}`"]
    
    # Oldalszám hozzáadása (prioritás!)
    if page_number is not None:
        parts.append(f"📄 **Oldal {page_number}**")
    
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

# Session state inicializálása - EAGER LOADING!
# Betöltjük a RAG rendszert az oldal betöltésekor, hogy lássa a meglévő dokumentumokat
if 'rag_system' not in st.session_state:
    try:
        st.session_state.rag_system = RAGSystem()
        logger.info("RAG rendszer inicializálva (eager loading)")
    except Exception as e:
        st.error(f"RAG rendszer inicializálási hiba: {e}")
        logger.error(f"RAG init hiba: {e}")
        st.session_state.rag_system = None

if 'session_manager' not in st.session_state:
    st.session_state.session_manager = SessionManager()

if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = st.session_state.session_manager.create_session()

if 'messages' not in st.session_state:
    st.session_state.messages = []

# Főoldal
def main_page():
    """Főoldal - Chat és dokumentum feltöltés"""
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
            elif st.session_state.rag_system is None:
                st.error("RAG rendszer nem inicializálódott. Frissítsd az oldalt (F5).")
            else:
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
        st.error("⚠️ RAG rendszer nem inicializálódott. Frissítsd az oldalt (F5).")
        return

    doc_count = _get_doc_count()
    if doc_count <= 0:
        st.info("📄 Nincs dokumentum a vector adatbázisban. Tölts fel PDF/TXT/DOCX fájlokat a bal oldali feltöltővel!")
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

                # LLM metrikák rögzítése streaming után
                try:
                    estimated_tokens = len(full_response.split()) * 1.3
                    prompt_tokens = int(estimated_tokens * 0.7)
                    completion_tokens = int(estimated_tokens * 0.3)
                    model_name = st.session_state.rag_system.llm_generator.model_name

                    cost = st.session_state.rag_system.metrics_collector.calculate_cost(
                        model_name, prompt_tokens, completion_tokens
                    )

                    st.session_state.rag_system.metrics_collector.record_llm_call(
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        model=model_name,
                        cost=cost
                    )
                except Exception as metric_error:
                    logger.warning(f"Metrika rögzítés hiba: {metric_error}")

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
            import pandas as pd  # Local import for nested scope
            
            # Adatok tisztítása és típus konverzió
            try:
                # Numerikus oszlopok konverziója
                latency_trends['first_token_time'] = pd.to_numeric(latency_trends['first_token_time'], errors='coerce')
                latency_trends['total_time'] = pd.to_numeric(latency_trends['total_time'], errors='coerce')
                
                # NaN értékek eltávolítása
                latency_trends = latency_trends.dropna(subset=['first_token_time', 'total_time'])
                
                if not latency_trends.empty:
                    fig = px.line(
                        latency_trends,
                        x='date',
                        y=['first_token_time', 'total_time'],
                        title='Latency Trendek',
                        labels={'date': 'Dátum', 'value': 'Idő (másodperc)'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Nincs elég adat a latency trendek megjelenítéséhez.")
            except Exception as e:
                st.warning(f"Latency grafikon hiba: {e}")
                logger.warning(f"Latency plot error: {e}")
        
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
    """Evaluation oldal - RAG, Prompt, App szintű értékelés az UI-ból"""
    st.title("🧪 Evaluation")
    st.markdown("---")

    if st.session_state.rag_system is None:
        st.error("RAG rendszer nem inicializálódott. Frissítsd az oldalt (F5).")
        return

    rag_system = st.session_state.rag_system
    doc_count = _get_doc_count()

    from src.evaluation.rag_eval import RAGEvaluator
    from src.evaluation.prompt_eval import PromptEvaluator
    from src.evaluation.app_eval import AppEvaluator
    from src.evaluation.test_cases import RAG_TEST_CASES, PROMPT_TEST_CASES, APP_TEST_CASES

    tab1, tab2, tab3 = st.tabs(["📊 RAG Szintű", "💬 Prompt Szintű", "🚀 Alkalmazás Szintű"])

    # ── TAB 1: RAG ──────────────────────────────────────────────
    with tab1:
        st.subheader("📊 RAG Szintű Értékelés")

        # -- Retrieval --
        st.markdown("### Retrieval Minőség (Precision / Recall / MRR)")
        if doc_count <= 0:
            st.warning("Nincs dokumentum a vector DB-ben. Tölts fel dokumentumokat a Főoldalon a retrieval értékelés előtt!")

        if st.button("Retrieval Értékelés Futtatása", disabled=(doc_count <= 0), key="btn_ret"):
            with st.spinner("Retrieval értékelés folyamatban..."):
                ev = RAGEvaluator(
                    vector_store=rag_system.vector_store,
                    retrieval_engine=rag_system.retrieval_engine,
                    embedding_model=rag_system.embedding_model,
                    chunking_strategy=rag_system.chunking,
                )
                res = ev.evaluate_retrieval_by_keywords(RAG_TEST_CASES['retrieval_tests'])
                st.session_state.eval_retrieval = res
                ev.save_results(res, str(Path("evaluations/rag_retrieval_results.json")))

        res = st.session_state.get('eval_retrieval')
        if res:
            km = res.get('keyword_metrics', {})
            br = res.get('basic_retrieval', {})
            st.markdown(f"**Tesla-specifikus tesztek** ({km.get('num_queries', 0)} query, kulcsszó alapú)")
            c1, c2, c3 = st.columns(3)
            c1.metric("Precision", f"{km.get('precision', 0):.3f}")
            c2.metric("Recall", f"{km.get('recall', 0):.3f}")
            c3.metric("MRR", f"{km.get('mrr', 0):.3f}")
            if br.get('num_queries', 0) > 0:
                st.markdown(f"**Általános retrieval teszt** ({br['num_queries']} query)")
                st.metric("Sikerességi arány", f"{br.get('success_rate', 0):.1%}")
            with st.expander("Részletes eredmények", expanded=False):
                kw_details = [d for d in res.get('details', []) if d.get('type') == 'keyword']
                if kw_details:
                    df = pd.DataFrame([{
                        'Query': d['query'][:60],
                        'Precision': d.get('precision', 0),
                        'Recall': d.get('recall', 0),
                        'MRR': d.get('mrr', 0),
                        'Talált kulcsszavak': ', '.join(d.get('keywords_found', [])),
                    } for d in kw_details])
                    st.dataframe(df, use_container_width=True)

        st.markdown("---")

        # -- Embedding --
        st.markdown("### Embedding Modell Teljesítmény")
        if st.button("Embedding Értékelés Futtatása", key="btn_emb"):
            with st.spinner("Embedding értékelés folyamatban..."):
                ev = RAGEvaluator(
                    vector_store=rag_system.vector_store,
                    retrieval_engine=rag_system.retrieval_engine,
                    embedding_model=rag_system.embedding_model,
                )
                res = ev.evaluate_embedding_quality(RAG_TEST_CASES['embedding_tests'])
                st.session_state.eval_embedding = res
                ev.save_results(res, str(Path("evaluations/rag_embedding_results.json")))

        res = st.session_state.get('eval_embedding')
        if res:
            c1, c2, c3 = st.columns(3)
            c1.metric("Korreláció", f"{res.get('correlation', 0):.3f}")
            c2.metric("Átlag prediktált sim.", f"{res.get('mean_predicted_sim', 0):.3f}")
            c3.metric("Átlag valós sim.", f"{res.get('mean_true_sim', 0):.3f}")
            st.caption(f"Teszt párok száma: {res.get('num_pairs', 0)}")

        st.markdown("---")

        # -- Chunking --
        st.markdown("### Chunking Stratégia Hatékonyság")
        if st.button("Chunking Értékelés Futtatása", key="btn_chk"):
            with st.spinner("Chunking értékelés folyamatban..."):
                ev = RAGEvaluator(
                    vector_store=rag_system.vector_store,
                    retrieval_engine=rag_system.retrieval_engine,
                    embedding_model=rag_system.embedding_model,
                    chunking_strategy=rag_system.chunking,
                )
                res = ev.evaluate_chunking_tests(RAG_TEST_CASES['chunking_tests'])
                st.session_state.eval_chunking = res
                ev.save_results(res, str(Path("evaluations/rag_chunking_results.json")))

        res = st.session_state.get('eval_chunking')
        if res:
            c1, c2, c3 = st.columns(3)
            c1.metric("Chunk szám pontosság", f"{res.get('chunk_count_accuracy', 0):.1%}")
            c2.metric("Méret érvényesség", f"{res.get('size_validity_rate', 0):.1%}")
            c3.metric("Tesztek száma", res.get('total_tests', 0))
            with st.expander("Részletes eredmények", expanded=False):
                for tr in res.get('test_results', []):
                    s = tr.get('statistics', {})
                    match = "✅" if tr.get('chunk_count_match') else "❌"
                    st.markdown(
                        f"{match} Elvárt: **{tr['expected_chunks']}** chunk, "
                        f"Kapott: **{tr['actual_chunks']}** chunk — "
                        f"Átlag méret: {s.get('avg_chunk_size', 0):.0f}, "
                        f"Min: {s.get('min_chunk_size', 0)}, Max: {s.get('max_chunk_size', 0)}"
                    )

    # ── TAB 2: Prompt ────────────────────────────────────────────
    with tab2:
        st.subheader("💬 Prompt Szintű Értékelés")
        st.caption(f"Tesztek száma: {len(PROMPT_TEST_CASES)} | Context relevance, hallucináció detektálás, LLM-as-Judge")

        col1, col2 = st.columns([3, 1])
        with col1:
            run_eval = st.button("Prompt Értékelés Futtatása", key="btn_prompt")
        with col2:
            if st.button("🗑️ Cache Törlése", key="btn_clear_prompt"):
                if 'eval_prompt' in st.session_state:
                    del st.session_state.eval_prompt
                st.success("Cache törölve!")
                st.rerun()
        
        if run_eval:
            import time
            start_time = time.time()
            with st.spinner(f"Prompt értékelés futtatása ({len(PROMPT_TEST_CASES)} teszt, ez pár percig tarthat)..."):
                ev = PromptEvaluator(llm_generator=rag_system.llm_generator)
                res = ev.run_evaluation(PROMPT_TEST_CASES)
                res['_run_timestamp'] = time.time()  # Időbélyeg hozzáadása
                res['_run_duration'] = time.time() - start_time
                st.session_state.eval_prompt = res
                ev.save_results(res, str(Path("evaluations/prompt_evaluation_results.json")))
            st.success(f"✅ Értékelés befejezve {res['_run_duration']:.1f} másodperc alatt!")

        res = st.session_state.get('eval_prompt')
        if res:
            summary = res.get('summary', {})
            
            # Időbélyeg megjelenítése (ha van)
            if '_run_timestamp' in res:
                import datetime
                run_time = datetime.datetime.fromtimestamp(res['_run_timestamp'])
                st.caption(f"⏱️ Utolsó futtatás: {run_time.strftime('%Y-%m-%d %H:%M:%S')} ({res.get('_run_duration', 0):.1f}s)")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Tesztek száma", summary.get('num_tests', 0))
            c2.metric("Átlag Context Relevance", f"{summary.get('avg_context_relevance', 0):.3f}")
            c3.metric("Átlag Hallucináció Score", f"{summary.get('avg_hallucination_score', 0):.3f}")
            with st.expander("Tesztenkénti eredmények", expanded=False):
                test_results = res.get('results', [])
                if test_results:
                    df = pd.DataFrame([{
                        'Query': r['query'][:50],
                        'Context Rel.': round(r.get('context_relevance', 0), 3),
                        'Hallucináció': round(r.get('hallucination_score', 0), 3),
                        'Válasz (részlet)': (r.get('answer', '') or '')[:80],
                    } for r in test_results])
                    st.dataframe(df, use_container_width=True)

    # ── TAB 3: Alkalmazás ────────────────────────────────────────
    with tab3:
        st.subheader("🚀 Alkalmazás Szintű Értékelés")

        # -- Latency --
        st.markdown("### Latency Teszt")
        if doc_count <= 0:
            st.warning("Nincs dokumentum a vector DB-ben. Tölts fel dokumentumokat a latency teszt előtt!")
        lat_queries = APP_TEST_CASES.get('latency_tests', {}).get('queries', [])
        num_runs = APP_TEST_CASES.get('latency_tests', {}).get('num_runs', 3)

        if st.button("Latency Teszt Futtatása", disabled=(doc_count <= 0), key="btn_lat"):
            import time
            start_time = time.time()
            try:
                with st.spinner(f"Latency teszt ({len(lat_queries)} query x {num_runs} futtatás)..."):
                    ev = AppEvaluator(rag_system=rag_system)
                    res = ev.evaluate_latency(lat_queries, num_runs=num_runs)
                    res['_run_timestamp'] = time.time()
                    res['_run_duration'] = time.time() - start_time
                    st.session_state.eval_latency = res
                    ev.save_results({'latency': res}, str(Path("evaluations/app_latency_results.json")))
                st.success(f"✅ Latency teszt befejezve {res['_run_duration']:.1f} másodperc alatt!")
            except Exception as e:
                st.error(f"❌ Latency teszt hiba: {e}")
                logger.error(f"Latency teszt hiba: {e}", exc_info=True)

        res = st.session_state.get('eval_latency')
        if res:
            # Időbélyeg megjelenítése (ha van)
            if '_run_timestamp' in res:
                import datetime
                run_time = datetime.datetime.fromtimestamp(res['_run_timestamp'])
                st.caption(f"⏱️ Utolsó futtatás: {run_time.strftime('%Y-%m-%d %H:%M:%S')} ({res.get('_run_duration', 0):.1f}s)")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Átlag First Token", f"{res.get('avg_first_token_time', 0):.2f}s")
            c2.metric("Átlag Total Time", f"{res.get('avg_total_time', 0):.2f}s")
            c3.metric("P95 First Token", f"{res.get('p95_first_token_time', 0):.2f}s")
            c4.metric("P95 Total Time", f"{res.get('p95_total_time', 0):.2f}s")
            st.caption(f"{res.get('num_queries', 0)} query x {res.get('num_runs_per_query', 0)} futtatás")

        st.markdown("---")

        # -- User Journey --
        st.markdown("### User Journey Teszt")
        journeys = APP_TEST_CASES.get('user_journeys', [])
        if doc_count <= 0:
            st.warning("Nincs dokumentum a vector DB-ben. Tölts fel dokumentumokat a user journey teszt előtt!")

        if st.button("User Journey Teszt Futtatása", disabled=(doc_count <= 0), key="btn_uj"):
            import time
            start_time = time.time()
            try:
                with st.spinner(f"User journey teszt ({len(journeys)} journey)..."):
                    ev = AppEvaluator(rag_system=rag_system)
                    res = ev.run_full_evaluation(APP_TEST_CASES)
                    res['_run_timestamp'] = time.time()
                    res['_run_duration'] = time.time() - start_time
                    st.session_state.eval_journey = res
                    ev.save_results(res, str(Path("evaluations/app_evaluation_results.json")))
                st.success(f"✅ User journey teszt befejezve {res['_run_duration']:.1f} másodperc alatt!")
            except Exception as e:
                st.error(f"❌ User journey teszt hiba: {e}")
                logger.error(f"User journey teszt hiba: {e}", exc_info=True)

        res = st.session_state.get('eval_journey')
        if res and 'user_journeys' in res:
            # Időbélyeg megjelenítése (ha van)
            if '_run_timestamp' in res:
                import datetime
                run_time = datetime.datetime.fromtimestamp(res['_run_timestamp'])
                st.caption(f"⏱️ Utolsó futtatás: {run_time.strftime('%Y-%m-%d %H:%M:%S')} ({res.get('_run_duration', 0):.1f}s)")
            
            jrs = res['user_journeys']
            success_count = sum(1 for jr in jrs if jr.get('success_rate', 0) >= 0.5)
            st.metric("Journey sikeresség", f"{success_count}/{len(jrs)}")
            with st.expander("Részletes journey eredmények", expanded=False):
                for i, jr in enumerate(jrs):
                    name = journeys[i]['name'] if i < len(journeys) else f"Journey {i+1}"
                    rate = jr.get('success_rate', 0)
                    t = jr.get('total_time', 0)
                    icon = "✅" if rate >= 0.5 else "❌"
                    st.markdown(f"{icon} **{name}** — Sikeresség: {rate:.0%}, Idő: {t:.1f}s")


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

