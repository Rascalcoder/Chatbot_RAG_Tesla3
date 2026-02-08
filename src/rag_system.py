"""
Teljes RAG rendszer wrapper
Összekapcsolja az összes komponenst
"""

import os
import logging
from typing import List, Dict, Any, Optional
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


class RAGSystem:
    """Teljes RAG rendszer osztály"""
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        top_k: int = None,
        use_reranking: bool = True
    ):
        """
        Args:
            chunk_size: Chunk méret
            chunk_overlap: Chunk átfedés
            top_k: Top K eredmények
            use_reranking: Használjon-e rerankinget
        """
        # Konfiguráció
        self.chunk_size = chunk_size or int(os.getenv('CHUNK_SIZE', 1000))
        self.chunk_overlap = chunk_overlap or int(os.getenv('CHUNK_OVERLAP', 200))
        self.top_k = top_k or int(os.getenv('TOP_K', 5))

        # Model configuration (easy to upgrade later via env only)
        # Examples:
        #   LLM_MODEL=Qwen/Qwen3-4B-Instruct-2507
        #   EMBEDDING_MODEL=BAAI/bge-m3
        llm_model = os.getenv("LLM_MODEL", "Qwen/Qwen3-4B-Instruct-2507")
        embedding_model = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")

        # Auto-detect OpenAI models
        use_openai_llm = llm_model.startswith("gpt-") or "gpt" in llm_model.lower()
        use_openai_embedding = embedding_model.startswith("text-embedding-")

        # Komponensek inicializálása
        self.document_processor = DocumentProcessor()
        self.chunking = ChunkingStrategy(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        # Embedding (lokális vagy OpenAI)
        self.embedding_model = EmbeddingModel(use_openai=use_openai_embedding, model_name=embedding_model)
        self.vector_store = VectorStore()
        self.retrieval_engine = RetrievalEngine(
            vector_store=self.vector_store,
            embedding_model=self.embedding_model,
            top_k=self.top_k
        )
        self.reranker = Reranker(use_reranking=use_reranking)
        # LLM (lokális vagy OpenAI)
        self.llm_generator = LLMGenerator(use_openai=use_openai_llm, model_name=llm_model)
        self.streaming_generator = StreamingGenerator(use_openai=use_openai_llm, model_name=llm_model)
        self.metrics_collector = MetricsCollector()

        # Tesla System Prompt betöltése
        self.system_message = self._load_system_prompt()

        logger.info("RAG rendszer inicializálva")

    def _load_system_prompt(self) -> str:
        """Tesla System Prompt betöltése"""
        try:
            prompt_path = os.path.join(os.path.dirname(__file__), '..', 'System_prompt_Tesla.txt')
            if os.path.exists(prompt_path):
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                logger.info("Tesla System Prompt betöltve")
                return content
            else:
                logger.warning(f"System prompt nem található: {prompt_path}")
                return None
        except Exception as e:
            logger.error(f"Hiba a system prompt betöltésekor: {e}")
            return None

    def add_documents(self, file_paths: List[str]):
        """
        Dokumentumok hozzáadása a rendszerhez
        
        Args:
            file_paths: Fájl elérési utak listája
        """
        # Dokumentumok feldolgozása
        documents = self.document_processor.process_multiple_files(file_paths)
        
        if not documents:
            logger.warning("Nincs feldolgozható dokumentum")
            return
        
        # Chunking
        chunks = self.chunking.chunk_documents(documents)
        
        if not chunks:
            logger.warning("Nincs chunk generálva")
            return
        
        # Embedding generálás
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.embedding_model.embed_texts(texts)
        
        # Metadata előkészítése
        metadatas = []
        ids = []
        for i, chunk in enumerate(chunks):
            metadata = chunk.get('metadata', {}).copy()
            metadata['chunk_index'] = chunk.get('chunk_index', i)
            metadatas.append(metadata)
            ids.append(f"chunk_{i}")
        
        # Vektor adatbázisba mentés
        self.vector_store.add_documents(
            texts=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"{len(chunks)} chunk hozzáadva a rendszerhez")
    
    def query(
        self,
        query: str,
        stream: bool = False,
        top_k: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Query futtatása
        
        Args:
            query: Keresési lekérdezés
            stream: Használjon-e streaminget
            top_k: Top K eredmények
            
        Returns:
            Válasz dict
        """
        import time
        start_time = time.time()
        
        # Retrieval
        retrieved = self.retrieval_engine.retrieve(query, top_k=top_k or self.top_k)
        
        retrieval_time = time.time() - start_time
        self.metrics_collector.record_retrieval(query, len(retrieved), retrieval_time)
        
        # Reranking
        reranked = self.reranker.rerank(query, retrieved, top_k=3)
        
        # LLM válasz generálás
        if stream:
            # Streaming válasz
            return {
                'query': query,
                'context': reranked,
                'stream': True,
                'generator': self.streaming_generator.generate_stream(query, reranked, system_message=self.system_message)
            }
        else:
            # Normál válasz
            response_start = time.time()
            answer = self.llm_generator.generate(query, reranked, system_message=self.system_message)
            response_time = time.time() - response_start
            
            # Metrikák rögzítése
            # (Token számokat a LLM válaszból kellene kinyerni, itt csak becsüljük)
            estimated_tokens = len(answer.split()) * 1.3  # Becslés
            cost = self.metrics_collector.calculate_cost(
                self.llm_generator.model_name,
                int(estimated_tokens * 0.7),  # prompt
                int(estimated_tokens * 0.3)    # completion
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
                    'total_time': time.time() - start_time
                }
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Rendszer statisztikák"""
        collection_info = self.vector_store.get_collection_info()
        metrics_stats = self.metrics_collector.get_statistics(days=30)
        
        return {
            'vector_db': collection_info,
            'metrics': metrics_stats
        }

