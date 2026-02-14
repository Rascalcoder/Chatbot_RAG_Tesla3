"""
Teljes RAG rendszer wrapper
Összekapcsolja az összes komponenst

Production-ready pipeline:
- Robust language detection (langdetect)
- Dual-query retrieval (orig + translated) with union + dedupe
- Deterministic translation (temp=0)
- Abstain fallback when no relevant evidence
- Translation cache with TTL + max size
- Rate limit / backoff for translation API
- Observability metrics
"""

import os
import json
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from collections import OrderedDict
from dotenv import load_dotenv

from .rag.document_processor import DocumentProcessor
from .rag.chunking import ChunkingStrategy
from .rag.embeddings import EmbeddingModel
from .rag.vector_store import VectorStore
from .rag.retrieval import RetrievalEngine
from .rag.reranking import Reranker
from .llm.generator import LLMGenerator
from .llm.streaming import StreamingGenerator
from .monitoring.metrics import MetricsCollector

load_dotenv()

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# P1: Translation cache with TTL + max size
# ---------------------------------------------------------------------------
class TranslationCache:
    """LRU cache with TTL for query translations."""

    def __init__(self, max_size: int = 500, ttl_seconds: int = 3600):
        self._cache: OrderedDict[str, Tuple[str, float]] = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl_seconds
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[str]:
        if key in self._cache:
            value, ts = self._cache[key]
            if time.time() - ts < self.ttl:
                self._cache.move_to_end(key)
                self.hits += 1
                return value
            else:
                del self._cache[key]
        self.misses += 1
        return None

    def put(self, key: str, value: str):
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = (value, time.time())
        if len(self._cache) > self.max_size:
            self._cache.popitem(last=False)

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


# ---------------------------------------------------------------------------
# P0: Robust language detection
# ---------------------------------------------------------------------------
def detect_language(text: str) -> str:
    """
    Detect language of text. Returns ISO 639-1 code (e.g. 'en', 'hu').
    Falls back to heuristic if langdetect is unavailable.
    """
    try:
        from langdetect import detect, DetectorFactory
        # Make detection deterministic
        DetectorFactory.seed = 0
        return detect(text)
    except ImportError:
        logger.warning("langdetect not installed, using heuristic fallback")
        return _heuristic_lang_detect(text)
    except Exception:
        return _heuristic_lang_detect(text)


def _heuristic_lang_detect(text: str) -> str:
    """Fallback heuristic: check for Hungarian characters/words."""
    hungarian_chars = set('áéíóöőúüűÁÉÍÓÖŐÚÜŰ')
    hungarian_words = {
        'hogyan', 'miért', 'milyen', 'mikor', 'hol', 'mit',
        'és', 'egy', 'nem', 'van', 'hogy', 'meg', 'fel', 'ki',
        'azt', 'ezt', 'ahol', 'ből', 'ból', 'nak', 'nek',
    }
    if any(c in text for c in hungarian_chars):
        return 'hu'
    words = set(text.lower().split())
    if len(words & hungarian_words) >= 2:
        return 'hu'
    return 'en'


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------
def load_config() -> Dict[str, Any]:
    """Konfiguráció betöltése JSON fájlból"""
    config_path = Path(__file__).parent.parent / "config.json"
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info(f"Config betöltve: {config_path}")
                return config
        except Exception as e:
            logger.warning(f"Config JSON betöltési hiba: {e}")
    return {}


# ---------------------------------------------------------------------------
# P0: Abstain threshold — below this similarity, we refuse to answer
# ---------------------------------------------------------------------------
ABSTAIN_THRESHOLD = 0.35
ABSTAIN_MESSAGE = (
    "Sajnálom, a rendelkezésre álló dokumentumokban nem találtam releváns "
    "információt ehhez a kérdéshez. Kérlek, fogalmazd át a kérdésedet, vagy "
    "kérdezz a Tesla Model 3 kézikönyv egy konkrét témájáról."
)


class RAGSystem:
    """Teljes RAG rendszer osztály"""

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        top_k: int = None,
        use_reranking: bool = True
    ):
        # Konfiguráció
        config = load_config()

        self.chunk_size = chunk_size or int(os.getenv('CHUNK_SIZE', 1000))
        self.chunk_overlap = chunk_overlap or int(os.getenv('CHUNK_OVERLAP', 200))
        self.top_k = top_k or int(os.getenv('TOP_K', 5))

        # Model configuration
        llm_model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        embedding_model = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

        use_openai_llm = llm_model.startswith("gpt-") or "gpt" in llm_model.lower()
        use_openai_embedding = embedding_model.startswith("text-embedding-")

        # Komponensek inicializálása
        self.document_processor = DocumentProcessor()
        self.chunking = ChunkingStrategy(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        self.embedding_model = EmbeddingModel(use_openai=use_openai_embedding, model_name=embedding_model)
        self.vector_store = VectorStore()

        self.similarity_threshold = float(
            config.get('similarity_threshold')
            or os.getenv('SIMILARITY_THRESHOLD')
            or 0.3
        )
        self.retrieval_engine = RetrievalEngine(
            vector_store=self.vector_store,
            embedding_model=self.embedding_model,
            top_k=self.top_k,
            similarity_threshold=self.similarity_threshold
        )
        self.reranker = Reranker(use_reranking=use_reranking)
        self.llm_generator = LLMGenerator(use_openai=use_openai_llm, model_name=llm_model)
        self.streaming_generator = StreamingGenerator(use_openai=use_openai_llm, model_name=llm_model)
        self.metrics_collector = MetricsCollector()

        # P1: Translation cache
        self._translation_cache = TranslationCache(
            max_size=int(os.getenv('TRANSLATION_CACHE_SIZE', 500)),
            ttl_seconds=int(os.getenv('TRANSLATION_CACHE_TTL', 3600))
        )

        # P1: Rate limit state for translation API
        self._translate_backoff = 0.0
        self._translate_last_error_time = 0.0

        # Tesla System Prompt betöltése
        self.system_message = self._load_system_prompt()

        logger.info("RAG rendszer inicializálva")

    def _load_system_prompt(self) -> str:
        """Tesla System Prompt betöltése"""
        try:
            prompt_path = os.path.join(os.path.dirname(__file__), '..', 'System_prompt_Tesla.txt')
            if os.path.exists(prompt_path):
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logger.warning(f"System prompt nem található: {prompt_path}")
                return None
        except Exception as e:
            logger.error(f"Hiba a system prompt betöltésekor: {e}")
            return None

    # ------------------------------------------------------------------
    # P0: Robust language detection + P0: Deterministic translation
    # ------------------------------------------------------------------
    def _detect_language(self, text: str) -> str:
        """Detect language of user query."""
        return detect_language(text)

    def _translate_to_english(self, query: str) -> Optional[str]:
        """
        Translate query to English using OpenAI API.
        P0: temp=0, strict "translation only" prompt.
        P1: Rate limit with exponential backoff.
        Returns None if translation fails.
        """
        # Check cache first
        cached = self._translation_cache.get(query)
        if cached is not None:
            return cached

        # P1: Backoff check
        if self._translate_backoff > 0:
            elapsed = time.time() - self._translate_last_error_time
            if elapsed < self._translate_backoff:
                logger.warning(f"Translation API backoff active ({self._translate_backoff:.1f}s)")
                return None

        t0 = time.time()
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a translation engine. Translate the user's text to English. "
                            "Output ONLY the English translation, nothing else. "
                            "Do not explain, do not add notes."
                        )
                    },
                    {"role": "user", "content": query}
                ],
                temperature=0,  # P0: Deterministic
                max_tokens=150
            )

            translated = response.choices[0].message.content.strip()

            # Cache the result
            self._translation_cache.put(query, translated)

            # Reset backoff on success
            self._translate_backoff = 0.0

            # P1: Observability
            translate_latency = time.time() - t0
            self.metrics_collector.record_pipeline_event(
                event_type='translation',
                data={
                    'original': query[:100],
                    'translated': translated[:100],
                    'latency': translate_latency,
                    'cache_hit': False
                }
            )

            logger.info(f"Query fordítva: '{query[:40]}' -> '{translated[:40]}' ({translate_latency:.2f}s)")
            return translated

        except Exception as e:
            # P1: Exponential backoff (1s, 2s, 4s, 8s, max 30s)
            self._translate_backoff = min(max(self._translate_backoff * 2, 1.0), 30.0)
            self._translate_last_error_time = time.time()
            logger.warning(f"Fordítási hiba (backoff={self._translate_backoff:.1f}s): {e}")
            return None

    # ------------------------------------------------------------------
    # Pipeline 6: Dual-query retrieval
    # ------------------------------------------------------------------
    def _dual_retrieve(
        self,
        original_query: str,
        translated_query: Optional[str],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Retrieve with both original and translated queries, then union + dedupe.

        If translation failed, falls back to original query only.
        Retrieves top_k*2 from each, unions by chunk id, dedupes,
        keeps best similarity per chunk.
        """
        # Retrieve with original query
        results_orig = self.retrieval_engine.retrieve(original_query, top_k=top_k * 2)

        # Retrieve with translated query (if available and different)
        results_trans = []
        if translated_query and translated_query.lower() != original_query.lower():
            results_trans = self.retrieval_engine.retrieve(translated_query, top_k=top_k * 2)

        # Union + dedupe by chunk id (keep highest similarity)
        seen: Dict[str, Dict[str, Any]] = {}
        for r in results_orig + results_trans:
            chunk_id = r.get('id', '')
            if chunk_id not in seen or r.get('similarity', 0) > seen[chunk_id].get('similarity', 0):
                seen[chunk_id] = r

        # Sort by similarity descending
        merged = sorted(seen.values(), key=lambda x: x.get('similarity', 0), reverse=True)

        logger.info(
            f"Dual-retrieve: {len(results_orig)} orig + {len(results_trans)} trans "
            f"-> {len(merged)} merged"
        )

        return merged

    # ------------------------------------------------------------------
    # P0: Abstain check
    # ------------------------------------------------------------------
    def _should_abstain(self, context: List[Dict[str, Any]]) -> bool:
        """Check if we should abstain (no relevant evidence)."""
        if not context:
            return True
        top_sim = max(r.get('similarity', 0) for r in context)
        return top_sim < ABSTAIN_THRESHOLD

    # ------------------------------------------------------------------
    # Document management
    # ------------------------------------------------------------------
    def add_documents(self, file_paths: List[str]):
        """Dokumentumok hozzáadása a rendszerhez"""
        documents = self.document_processor.process_multiple_files(file_paths)
        if not documents:
            logger.warning("Nincs feldolgozható dokumentum")
            return

        chunks = self.chunking.chunk_documents(documents)
        if not chunks:
            logger.warning("Nincs chunk generálva")
            return

        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.embedding_model.embed_texts(texts)

        metadatas = []
        ids = []
        for i, chunk in enumerate(chunks):
            metadata = chunk.get('metadata', {}).copy()
            metadata['chunk_index'] = chunk.get('chunk_index', i)
            metadatas.append(metadata)
            ids.append(f"chunk_{i}")

        self.vector_store.add_documents(
            texts=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

        logger.info(f"{len(chunks)} chunk hozzáadva a rendszerhez")

    # ------------------------------------------------------------------
    # Main query pipeline
    # ------------------------------------------------------------------
    def query(
        self,
        query: str,
        stream: bool = False,
        top_k: Optional[int] = None,
        conversation_history: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Query futtatása - production-ready pipeline.

        Pipeline:
        1. Detect language
        2. If not English: translate to English
        3. Dual-query retrieval (orig + translated), union + dedupe
        4. Rerank with English query (chunks are English)
        5. Abstain check: if no relevant evidence, refuse to answer
        6. LLM generation with original query (answer in user's language)

        Args:
            query: Felhasználói kérdés
            stream: Streaming válasz generálás
            top_k: Visszaadott dokumentumok száma
            conversation_history: Korábbi üzenetek [{'role': 'user'|'assistant', 'content': str}]
        """
        start_time = time.time()
        effective_top_k = top_k or self.top_k

        # 1. Detect language
        user_lang = self._detect_language(query)
        translated_query = None

        # 2. Translate if not English
        if user_lang != 'en':
            translated_query = self._translate_to_english(query)

        # 3. Dual-query retrieval
        all_retrieved = self._dual_retrieve(query, translated_query, effective_top_k)

        retrieval_time = time.time() - start_time

        # P1: Observability
        self.metrics_collector.record_retrieval(query, len(all_retrieved), retrieval_time)
        self.metrics_collector.record_pipeline_event(
            event_type='retrieval_detail',
            data={
                'query': query[:100],
                'user_lang': user_lang,
                'translated': translated_query[:100] if translated_query else None,
                'retrieval_k': len(all_retrieved),
                'top_similarity': all_retrieved[0].get('similarity', 0) if all_retrieved else 0,
                'cache_hit_rate': self._translation_cache.hit_rate
            }
        )

        # 4. Rerank with English query
        rerank_query = translated_query or query
        if self.reranker.use_reranking and all_retrieved:
            reranked = self.reranker.rerank(rerank_query, all_retrieved, top_k=effective_top_k)
            # Fallback if reranker gives very negative scores
            if reranked and reranked[0].get('rerank_score', 0) < -5:
                logger.warning("Reranking negative scores, falling back to similarity order")
                reranked = all_retrieved[:effective_top_k]
        else:
            reranked = all_retrieved[:effective_top_k]

        # 5. Abstain check
        if self._should_abstain(reranked):
            logger.info(f"Abstain: no relevant evidence for '{query[:40]}'")
            return {
                'query': query,
                'answer': ABSTAIN_MESSAGE,
                'context': reranked,
                'metadata': {
                    'retrieval_time': retrieval_time,
                    'response_time': 0,
                    'total_time': time.time() - start_time,
                    'abstained': True,
                    'user_lang': user_lang
                }
            }

        # 6. LLM generation - ORIGINAL query (answer in user's language)
        if stream:
            return {
                'query': query,
                'context': reranked,
                'stream': True,
                'generator': self.streaming_generator.generate_stream(
                    query, reranked, system_message=self.system_message,
                    conversation_history=conversation_history
                )
            }
        else:
            response_start = time.time()
            answer = self.llm_generator.generate(query, reranked, system_message=self.system_message, conversation_history=conversation_history)
            response_time = time.time() - response_start

            # Token estimation & cost
            estimated_tokens = len(answer.split()) * 1.3
            cost = self.metrics_collector.calculate_cost(
                self.llm_generator.model_name,
                int(estimated_tokens * 0.7),
                int(estimated_tokens * 0.3)
            )

            self.metrics_collector.record_llm_call(
                prompt_tokens=int(estimated_tokens * 0.7),
                completion_tokens=int(estimated_tokens * 0.3),
                model=self.llm_generator.model_name,
                total_time=response_time,
                cost=cost
            )

            return {
                'query': query,
                'answer': answer,
                'context': reranked,
                'metadata': {
                    'retrieval_time': retrieval_time,
                    'response_time': response_time,
                    'total_time': time.time() - start_time,
                    'user_lang': user_lang,
                    'translated_query': translated_query,
                    'reranked_count': len(reranked),
                    'abstained': False
                }
            }

    def get_stats(self) -> Dict[str, Any]:
        """Rendszer statisztikák"""
        collection_info = self.vector_store.get_collection_info()
        metrics_stats = self.metrics_collector.get_statistics(days=30)

        return {
            'vector_db': collection_info,
            'metrics': metrics_stats,
            'translation_cache': {
                'hit_rate': self._translation_cache.hit_rate,
                'size': len(self._translation_cache._cache),
                'max_size': self._translation_cache.max_size
            }
        }
