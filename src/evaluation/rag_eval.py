"""
RAG szintű értékelés
Retrieval minőség, embedding teljesítmény, chunking hatékonyság
"""

from typing import List, Dict, Any
import logging
import numpy as np
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class RAGEvaluator:
    """RAG szintű értékelő osztály"""
    
    def __init__(self, vector_store, retrieval_engine, embedding_model, chunking_strategy=None):
        """
        Args:
            vector_store: Vektor adatbázis
            retrieval_engine: Retrieval engine
            embedding_model: Embedding modell
            chunking_strategy: Chunking stratégia (opcionális)
        """
        self.vector_store = vector_store
        self.retrieval_engine = retrieval_engine
        self.embedding_model = embedding_model
        self.chunking_strategy = chunking_strategy
    
    def evaluate_retrieval(
        self,
        queries: List[str],
        ground_truth: List[List[str]]
    ) -> Dict[str, float]:
        """
        Retrieval minőség értékelése
        
        Args:
            queries: Keresési lekérdezések
            ground_truth: Ground truth dokumentum ID-k listája minden query-hez
            
        Returns:
            Metrikák: precision, recall, MRR
        """
        if len(queries) != len(ground_truth):
            raise ValueError("A queries és ground_truth hossza nem egyezik")
        
        precisions = []
        recalls = []
        mrr_scores = []
        
        for query, gt_ids in zip(queries, ground_truth):
            # Retrieval futtatása
            results = self.retrieval_engine.retrieve(query, top_k=10)
            retrieved_ids = [r['id'] for r in results]
            
            # Precision és Recall számítása
            relevant_retrieved = len(set(retrieved_ids) & set(gt_ids))
            precision = relevant_retrieved / len(retrieved_ids) if retrieved_ids else 0
            recall = relevant_retrieved / len(gt_ids) if gt_ids else 0
            
            precisions.append(precision)
            recalls.append(recall)
            
            # MRR számítása
            mrr = 0.0
            for rank, result_id in enumerate(retrieved_ids, 1):
                if result_id in gt_ids:
                    mrr = 1.0 / rank
                    break
            mrr_scores.append(mrr)
        
        return {
            'precision': np.mean(precisions),
            'recall': np.mean(recalls),
            'mrr': np.mean(mrr_scores),
            'num_queries': len(queries)
        }

    def evaluate_retrieval_by_keywords(
        self,
        test_cases: List[Dict[str, Any]],
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Retrieval minőség értékelése kulcsszó alapon

        Args:
            test_cases: [{'query': str, 'expected_keywords': [str], 'category': str}]
            top_k: Top K eredmények

        Returns:
            Metrikák dict (keyword_metrics, basic_retrieval, details)
        """
        keyword_precisions = []
        keyword_recalls = []
        keyword_mrrs = []
        basic_successes = []
        details = []

        for test in test_cases:
            query = test['query']
            expected_keywords = [kw.lower() for kw in test.get('expected_keywords', [])]

            results = self.retrieval_engine.retrieve(query, top_k=top_k)

            if not expected_keywords:
                success = len(results) > 0
                basic_successes.append(success)
                details.append({
                    'query': query,
                    'category': test.get('category', ''),
                    'type': 'basic',
                    'success': success,
                    'retrieved_count': len(results)
                })
                continue

            relevant_count = 0
            keywords_found = set()
            first_relevant_rank = None

            for rank, result in enumerate(results, 1):
                text = (result.get('text', '') or '').lower()
                is_relevant = False

                for kw in expected_keywords:
                    if kw in text:
                        is_relevant = True
                        keywords_found.add(kw)

                if is_relevant:
                    relevant_count += 1
                    if first_relevant_rank is None:
                        first_relevant_rank = rank

            precision = relevant_count / len(results) if results else 0
            recall = len(keywords_found) / len(expected_keywords)
            mrr = 1.0 / first_relevant_rank if first_relevant_rank else 0

            keyword_precisions.append(precision)
            keyword_recalls.append(recall)
            keyword_mrrs.append(mrr)

            details.append({
                'query': query,
                'category': test.get('category', ''),
                'type': 'keyword',
                'precision': round(precision, 3),
                'recall': round(recall, 3),
                'mrr': round(mrr, 3),
                'retrieved_count': len(results),
                'relevant_count': relevant_count,
                'keywords_found': list(keywords_found),
                'keywords_expected': test.get('expected_keywords', [])
            })

        return {
            'keyword_metrics': {
                'precision': float(np.mean(keyword_precisions)) if keyword_precisions else 0,
                'recall': float(np.mean(keyword_recalls)) if keyword_recalls else 0,
                'mrr': float(np.mean(keyword_mrrs)) if keyword_mrrs else 0,
                'num_queries': len(keyword_precisions)
            },
            'basic_retrieval': {
                'success_rate': float(sum(basic_successes) / len(basic_successes)) if basic_successes else 0,
                'num_queries': len(basic_successes)
            },
            'num_total_queries': len(test_cases),
            'details': details
        }

    def evaluate_embedding_quality(
        self,
        test_pairs: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Embedding minőség értékelése
        
        Args:
            test_pairs: Teszt párok [{'text1': str, 'text2': str, 'similarity': float}]
            
        Returns:
            Embedding minőség metrikák
        """
        predicted_similarities = []
        true_similarities = []
        
        for pair in test_pairs:
            text1 = pair['text1']
            text2 = pair['text2']
            true_sim = pair['similarity']
            
            # Embedding generálás
            emb1 = self.embedding_model.embed_text(text1)
            emb2 = self.embedding_model.embed_text(text2)
            
            # Cosine similarity számítása
            cos_sim = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            
            predicted_similarities.append(cos_sim)
            true_similarities.append(true_sim)
        
        # Korreláció számítása
        correlation = np.corrcoef(predicted_similarities, true_similarities)[0, 1]
        
        return {
            'correlation': correlation,
            'num_pairs': len(test_pairs),
            'mean_predicted_sim': np.mean(predicted_similarities),
            'mean_true_sim': np.mean(true_similarities)
        }
    
    def evaluate_chunking_strategy(
        self,
        documents: List[Dict[str, Any]],
        chunking_strategy
    ) -> Dict[str, Any]:
        """
        Chunking stratégia hatékonyságának mérése
        
        Args:
            documents: Dokumentumok
            chunking_strategy: Chunking stratégia
            
        Returns:
            Chunking metrikák
        """
        all_chunks = chunking_strategy.chunk_documents(documents)
        stats = chunking_strategy.get_chunk_statistics(all_chunks)
        
        # Chunk méret konzisztencia
        chunk_sizes = [chunk['chunk_size'] for chunk in all_chunks]
        size_variance = np.var(chunk_sizes)
        
        return {
            **stats,
            'size_variance': size_variance,
            'size_std': np.std(chunk_sizes)
        }
    
    def run_full_evaluation(
        self,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Teljes RAG értékelés futtatása
        
        Args:
            test_cases: Teszt esetek
            
        Returns:
            Összesített eredmények
        """
        results = {
            'retrieval_metrics': {},
            'embedding_metrics': {},
            'chunking_metrics': {},
            'timestamp': str(Path().cwd())
        }
        
        # Retrieval értékelés
        if 'retrieval_tests' in test_cases:
            rt = test_cases['retrieval_tests']
            if isinstance(rt, list):
                retrieval_results = self.evaluate_retrieval_by_keywords(rt)
            else:
                retrieval_results = self.evaluate_retrieval(
                    rt['queries'], rt['ground_truth']
                )
            results['retrieval_metrics'] = retrieval_results
        
        # Embedding értékelés
        if 'embedding_tests' in test_cases:
            embedding_results = self.evaluate_embedding_quality(
                test_cases['embedding_tests']
            )
            results['embedding_metrics'] = embedding_results
        
        # Chunking értékelés
        if 'chunking_tests' in test_cases and self.chunking_strategy:
            chunking_results = self.evaluate_chunking_tests(
                test_cases['chunking_tests']
            )
            results['chunking_metrics'] = chunking_results
        
        return results
    
    def evaluate_chunking_tests(
        self,
        chunking_tests: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Chunking tesztek értékelése
        
        Args:
            chunking_tests: Chunking teszt esetek
            
        Returns:
            Chunking értékelési eredmények
        """
        results = []
        
        for test in chunking_tests:
            document = {
                'text': test['document'],
                'metadata': {'test_id': test.get('test_id', 'unknown')}
            }
            
            # Chunking futtatása
            chunks = self.chunking_strategy.chunk_document(document)
            
            # Statisztikák számítása
            stats = self.chunking_strategy.get_chunk_statistics(chunks)
            
            # Várható chunk szám ellenőrzése
            expected_chunks = test.get('expected_chunks', 0)
            chunk_count_match = abs(len(chunks) - expected_chunks) <= 1  # Engedmény 1 chunk-ra
            
            # Chunk méret ellenőrzése
            min_size = test.get('min_chunk_size', 0)
            max_size = test.get('max_chunk_size', float('inf'))
            size_valid = all(
                min_size <= chunk['chunk_size'] <= max_size 
                for chunk in chunks
            ) if chunks else False
            
            results.append({
                'test_id': test.get('test_id', 'unknown'),
                'expected_chunks': expected_chunks,
                'actual_chunks': len(chunks),
                'chunk_count_match': chunk_count_match,
                'size_valid': size_valid,
                'statistics': stats
            })
        
        # Összesített metrikák
        total_tests = len(results)
        chunk_count_matches = sum(1 for r in results if r['chunk_count_match'])
        size_valid_count = sum(1 for r in results if r['size_valid'])
        
        return {
            'total_tests': total_tests,
            'chunk_count_accuracy': chunk_count_matches / total_tests if total_tests > 0 else 0,
            'size_validity_rate': size_valid_count / total_tests if total_tests > 0 else 0,
            'test_results': results
        }
    
    def save_results(self, results: Dict[str, Any], file_path: str):
        """Eredmények mentése"""
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

