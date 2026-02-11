"""
Retrieval mechanizmus implementáció
Clean score normalization + dynamic threshold
"""

from typing import List, Dict, Any, Optional
import logging
from .vector_store import VectorStore
from .embeddings import EmbeddingModel

logger = logging.getLogger(__name__)

# ChromaDB cosine distance → similarity conversion
# ChromaDB returns cosine *distance* in [0, 2]:
#   0.0 = identical vectors
#   1.0 = orthogonal
#   2.0 = opposite
# We convert to similarity in [0, 1]:  sim = 1 - (dist / 2)
_DISTANCE_SCALE = 2.0


def _distance_to_similarity(distance: float) -> float:
    """Convert ChromaDB cosine distance to [0,1] similarity score."""
    return 1.0 - (min(max(distance, 0.0), _DISTANCE_SCALE) / _DISTANCE_SCALE)


class RetrievalEngine:
    """Retrieval engine osztály"""

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_model: EmbeddingModel,
        top_k: int = 5,
        similarity_threshold: float = 0.3,
        min_results: int = 2,
        relative_threshold_ratio: float = 0.7
    ):
        """
        Args:
            vector_store: Vektor adatbázis
            embedding_model: Embedding modell
            top_k: Visszaadandó eredmények száma
            similarity_threshold: Abszolút hasonlósági küszöb [0,1]
            min_results: Minimum megtartandó eredmények száma (fallback)
            relative_threshold_ratio: Relatív küszöb arány (top1 * ratio)
        """
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.min_results = min_results
        self.relative_threshold_ratio = relative_threshold_ratio

    def _score_and_filter(
        self,
        results: List[Dict[str, Any]],
        threshold: float = None
    ) -> List[Dict[str, Any]]:
        """
        Score normalization + dynamic threshold filtering.

        Strategy:
        1. Convert all distances to similarity [0,1]
        2. Dynamic threshold = max(abs_threshold, top1_sim * relative_ratio)
        3. Filter by dynamic threshold
        4. Fallback: always keep at least min_results

        Returns:
            Filtered and scored results, sorted by similarity desc
        """
        if not results:
            return []

        threshold = threshold if threshold is not None else self.similarity_threshold

        # 1. Score normalization
        for r in results:
            r['similarity'] = _distance_to_similarity(r.get('distance', _DISTANCE_SCALE))

        # Sort by similarity descending
        results.sort(key=lambda x: x['similarity'], reverse=True)

        # 2. Dynamic threshold
        if threshold > 0:
            top_sim = results[0]['similarity']
            dynamic_thr = max(threshold, top_sim * self.relative_threshold_ratio)

            filtered = [r for r in results if r['similarity'] >= dynamic_thr]

            # 3. Min results fallback
            if len(filtered) < self.min_results and len(results) >= self.min_results:
                filtered = results[:self.min_results]
                logger.info(
                    f"Retrieval threshold fallback: kept top {self.min_results} "
                    f"(dynamic_thr={dynamic_thr:.3f}, top_sim={top_sim:.3f})"
                )
            elif len(filtered) < len(results):
                logger.info(
                    f"Retrieval: threshold={dynamic_thr:.3f}, "
                    f"kept {len(filtered)}/{len(results)} chunks"
                )

            return filtered

        return results

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Dokumentumok visszakeresése query alapján

        Args:
            query: Keresési lekérdezés
            top_k: Visszaadandó eredmények száma (opcionális)

        Returns:
            Találatok listája (scored + filtered, sorted by similarity desc)
        """
        if not query or not query.strip():
            logger.warning("Üres query retrieval")
            return []

        top_k = top_k or self.top_k

        try:
            query_embedding = self.embedding_model.embed_text(query)

            results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k
            )

            scored = self._score_and_filter(results)

            logger.info(f"Retrieval: {len(scored)} találat a '{query[:60]}' query-re")
            return scored

        except Exception as e:
            logger.error(f"Hiba a retrieval során: {e}")
            return []

    def retrieve_with_metadata(
        self,
        query: str,
        metadata_filter: Dict[str, Any] = None,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieval metadata szűréssel"""
        top_k = top_k or self.top_k

        try:
            query_embedding = self.embedding_model.embed_text(query)

            results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                filter_dict=metadata_filter
            )

            return self._score_and_filter(results)

        except Exception as e:
            logger.error(f"Hiba a metadata szűréses retrieval során: {e}")
            return []
