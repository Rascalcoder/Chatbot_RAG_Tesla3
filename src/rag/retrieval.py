"""
Retrieval mechanizmus implementáció
"""

from typing import List, Dict, Any, Optional
import logging
from .vector_store import VectorStore
from .embeddings import EmbeddingModel

logger = logging.getLogger(__name__)


class RetrievalEngine:
    """Retrieval engine osztály"""
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_model: EmbeddingModel,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ):
        """
        Args:
            vector_store: Vektor adatbázis
            embedding_model: Embedding modell
            top_k: Visszaadandó eredmények száma
            similarity_threshold: Hasonlósági küszöb
        """
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
    
    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Dokumentumok visszakeresése query alapján
        
        Args:
            query: Keresési lekérdezés
            top_k: Visszaadandó eredmények száma (opcionális)
            
        Returns:
            Találatok listája
        """
        if not query or not query.strip():
            logger.warning("Üres query retrieval")
            return []
        
        top_k = top_k or self.top_k
        
        try:
            # Query embedding generálása
            query_embedding = self.embedding_model.embed_text(query)
            
            # Keresés a vektor adatbázisban
            results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k
            )
            
            # Hasonlósági küszöb alkalmazása
            filtered_results = []
            for result in results:
                # ChromaDB distance-t használunk (kisebb = hasonlóbb)
                # Átváltjuk similarity-re (1 - normalized distance)
                distance = result.get('distance', 1.0)
                similarity = 1.0 - min(distance, 1.0)
                
                if similarity >= self.similarity_threshold:
                    result['similarity'] = similarity
                    filtered_results.append(result)
            
            logger.info(f"Retrieval: {len(filtered_results)} találat a '{query}' query-re")
            return filtered_results
        
        except Exception as e:
            logger.error(f"Hiba a retrieval során: {e}")
            return []
    
    def retrieve_with_metadata(
        self,
        query: str,
        metadata_filter: Dict[str, Any] = None,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieval metadata szűréssel
        
        Args:
            query: Keresési lekérdezés
            metadata_filter: Metadata szűrési feltételek
            top_k: Visszaadandó eredmények száma
            
        Returns:
            Találatok listája
        """
        top_k = top_k or self.top_k
        
        try:
            query_embedding = self.embedding_model.embed_text(query)
            
            results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                filter_dict=metadata_filter
            )
            
            # Hasonlósági küszöb alkalmazása
            filtered_results = []
            for result in results:
                distance = result.get('distance', 1.0)
                similarity = 1.0 - min(distance, 1.0)
                
                if similarity >= self.similarity_threshold:
                    result['similarity'] = similarity
                    filtered_results.append(result)
            
            return filtered_results
        
        except Exception as e:
            logger.error(f"Hiba a metadata szűréses retrieval során: {e}")
            return []

