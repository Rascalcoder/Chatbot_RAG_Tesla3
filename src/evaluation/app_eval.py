"""
Alkalmazás szintű értékelés
Teljes user journey tesztelés, response quality, latency, performance
"""

from typing import List, Dict, Any
import logging
import time
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class AppEvaluator:
    """Alkalmazás szintű értékelő osztály"""
    
    def __init__(self, rag_system):
        """
        Args:
            rag_system: Teljes RAG rendszer
        """
        self.rag_system = rag_system
    
    def evaluate_user_journey(
        self,
        journey: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Teljes user journey értékelése
        
        Args:
            journey: User journey dict {'steps': [{'action': str, 'input': str, 'expected': str}]}
            
        Returns:
            Journey értékelési eredmények
        """
        results = {
            'steps': [],
            'total_time': 0,
            'success_rate': 0
        }
        
        start_time = time.time()
        successful_steps = 0
        
        for step in journey.get('steps', []):
            step_result = self._evaluate_step(step)
            results['steps'].append(step_result)
            
            if step_result.get('success', False):
                successful_steps += 1
        
        results['total_time'] = time.time() - start_time
        results['success_rate'] = successful_steps / len(journey['steps']) if journey['steps'] else 0
        
        return results
    
    def _evaluate_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Egy lépés értékelése"""
        action = step.get('action')
        step_start = time.time()
        
        try:
            if action == 'query':
                # Query futtatása
                query = step.get('input', '')
                response = self.rag_system.query(query)
                
                step_time = time.time() - step_start
                
                # Response quality értékelés
                quality_score = self._evaluate_response_quality(
                    query=query,
                    response=response.get('answer', ''),
                    context=response.get('context', [])
                )
                
                # Success meghatározása
                expected = step.get('expected', '')
                success = self._check_expectation(response.get('answer', ''), expected)
                
                return {
                    'action': action,
                    'input': query,
                    'response': response.get('answer', ''),
                    'latency': step_time,
                    'quality_score': quality_score,
                    'success': success,
                    'expected': expected
                }
            
            elif action == 'upload':
                # Dokumentum feltöltés szimulálása
                # Itt csak időt mérünk
                step_time = time.time() - step_start
                return {
                    'action': action,
                    'input': step.get('input', ''),
                    'latency': step_time,
                    'success': True
                }
            
            else:
                return {
                    'action': action,
                    'error': f'Ismeretlen action: {action}',
                    'success': False
                }
        
        except Exception as e:
            logger.error(f"Hiba a step értékelésénél: {e}")
            return {
                'action': action,
                'error': str(e),
                'success': False,
                'latency': time.time() - step_start
            }
    
    def _evaluate_response_quality(
        self,
        query: str,
        response: str,
        context: List[Dict[str, Any]]
    ) -> float:
        """
        Response quality értékelése
        
        Returns:
            Quality score (0-1)
        """
        # Egyszerű heurisztika
        if not response:
            return 0.0
        
        # Válasz hossza
        length_score = min(len(response) / 500, 1.0)
        
        # Kontextus használat
        context_text = " ".join([doc.get('text', '') for doc in context]).lower()
        response_words = set(response.lower().split())
        context_words = set(context_text.split())
        
        overlap = len(response_words & context_words)
        context_score = overlap / len(response_words) if response_words else 0
        
        # Kombinált score
        quality = (length_score * 0.3 + context_score * 0.7)
        return min(quality, 1.0)
    
    def _check_expectation(self, actual: str, expected: str) -> bool:
        """Várható eredmény ellenőrzése"""
        if not expected:
            return True  # Ha nincs elvárás, akkor sikeres
        
        # Egyszerű substring ellenőrzés
        expected_lower = expected.lower()
        actual_lower = actual.lower()
        
        return expected_lower in actual_lower
    
    def evaluate_latency(
        self,
        queries: List[str],
        num_runs: int = 3
    ) -> Dict[str, Any]:
        """
        Latency metrikák mérése
        
        Args:
            queries: Teszt lekérdezések
            num_runs: Hányszor futtassuk le
            
        Returns:
            Latency statisztikák
        """
        all_first_tokens = []
        all_total_times = []
        
        for query in queries:
            query_first_tokens = []
            query_total_times = []
            
            for _ in range(num_runs):
                start = time.time()
                response = self.rag_system.query(query, stream=False)
                
                first_token = response.get('metadata', {}).get('first_token_time', 0)
                total_time = time.time() - start
                
                query_first_tokens.append(first_token)
                query_total_times.append(total_time)
            
            all_first_tokens.extend(query_first_tokens)
            all_total_times.extend(query_total_times)
        
        import numpy as np
        
        return {
            'num_queries': len(queries),
            'num_runs_per_query': num_runs,
            'avg_first_token_time': np.mean(all_first_tokens) if all_first_tokens else 0,
            'avg_total_time': np.mean(all_total_times) if all_total_times else 0,
            'p95_first_token_time': np.percentile(all_first_tokens, 95) if all_first_tokens else 0,
            'p95_total_time': np.percentile(all_total_times, 95) if all_total_times else 0
        }
    
    def run_full_evaluation(
        self,
        test_cases: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Teljes alkalmazás értékelés
        
        Args:
            test_cases: Teszt esetek
            
        Returns:
            Összesített eredmények
        """
        results = {}
        
        # User journey értékelés
        if 'user_journeys' in test_cases:
            journey_results = []
            for journey in test_cases['user_journeys']:
                result = self.evaluate_user_journey(journey)
                journey_results.append(result)
            results['user_journeys'] = journey_results
        
        # Latency értékelés
        if 'latency_tests' in test_cases:
            latency_results = self.evaluate_latency(
                test_cases['latency_tests']['queries'],
                test_cases['latency_tests'].get('num_runs', 3)
            )
            results['latency'] = latency_results
        
        return results
    
    def save_results(self, results: Dict[str, Any], file_path: str):
        """Eredmények mentése"""
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

