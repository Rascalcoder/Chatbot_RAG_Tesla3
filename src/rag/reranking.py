"""
Reranking mechanizmus implementáció
Cross-encoder alapú reranking támogatása
"""

from typing import List, Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)


class Reranker:
    """Reranker osztály cross-encoder modellel"""
    
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        use_reranking: bool = True
    ):
        """
        Args:
            model_name: Reranking modell neve
            use_reranking: Használjon-e rerankinget
        """
        self.use_reranking = use_reranking
        self.model_name = model_name
        self._model = None
        
        if use_reranking:
            self._init_model()
    
    def _init_model(self):
        """Reranking modell inicializálása"""
        try:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(self.model_name)
            logger.info(f"Reranking modell inicializálva: {self.model_name}")
        except ImportError:
            logger.warning("sentence-transformers nincs telepítve. Reranking kikapcsolva.")
            self.use_reranking = False
        except Exception as e:
            logger.warning(f"Hiba a reranking modell inicializálásánál: {e}. Reranking kikapcsolva.")
            self.use_reranking = False
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Dokumentumok újrarangsorolása
        
        Args:
            query: Keresési lekérdezés
            documents: Dokumentumok listája
            top_k: Visszaadandó eredmények száma
            
        Returns:
            Rerankelt dokumentumok listája
        """
        if not documents:
            return []
        
        if not self.use_reranking or self._model is None:
            # Ha nincs reranking, csak top_k-t alkalmazzuk
            if top_k:
                return documents[:top_k]
            return documents
        
        try:
            # Query-document párok létrehozása
            pairs = [[query, doc['text']] for doc in documents]
            
            # Reranking scores számítása
            scores = self._model.predict(pairs)
            
            # Dokumentumok score-okkal párosítása
            scored_docs = []
            for doc, score in zip(documents, scores):
                doc_copy = doc.copy()
                doc_copy['rerank_score'] = float(score)
                scored_docs.append(doc_copy)
            
            # Score szerint rendezés (csökkenő)
            scored_docs.sort(key=lambda x: x['rerank_score'], reverse=True)
            
            # Top-k kiválasztása
            if top_k:
                scored_docs = scored_docs[:top_k]
            
            logger.info(f"Reranking: {len(scored_docs)} dokumentum újrarangsorolva")
            return scored_docs
        
        except Exception as e:
            logger.error(f"Hiba a reranking során: {e}")
            # Hiba esetén visszaadjuk az eredeti listát
            if top_k:
                return documents[:top_k]
            return documents
    
    def rerank_with_metadata(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        metadata_boost: Dict[str, float] = None
    ) -> List[Dict[str, Any]]:
        """
        Reranking metadata boost-tal
        
        Args:
            query: Keresési lekérdezés
            documents: Dokumentumok listája
            top_k: Visszaadandó eredmények száma
            metadata_boost: Metadata kulcsok és boost értékek
            
        Returns:
            Rerankelt dokumentumok listája
        """
        # Először alap reranking
        reranked = self.rerank(query, documents, top_k=None)
        
        # Metadata boost alkalmazása
        if metadata_boost:
            for doc in reranked:
                metadata = doc.get('metadata', {})
                boost = 0.0
                for key, value in metadata_boost.items():
                    if key in metadata:
                        boost += value
                
                # Boost hozzáadása a rerank score-hoz
                if 'rerank_score' in doc:
                    doc['rerank_score'] += boost
        
        # Újrarendezés boost után
        reranked.sort(key=lambda x: x.get('rerank_score', 0.0), reverse=True)
        
        # Top-k kiválasztása
        if top_k:
            reranked = reranked[:top_k]
        
        return reranked

