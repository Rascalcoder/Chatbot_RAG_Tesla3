"""
Prompt szintű értékelés
Single-turn eval, context relevance, hallucináció detektálás, LLM-as-Judge
"""

from typing import List, Dict, Any, Optional
import logging
import os
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class PromptEvaluator:
    """Prompt szintű értékelő osztály"""
    
    def __init__(self, llm_generator):
        """
        Args:
            llm_generator: LLM generator
        """
        self.llm_generator = llm_generator
        self._judge_client = None
        self._init_judge()
    
    def _init_judge(self):
        """LLM-as-Judge inicializálása"""
        try:
            from openai import OpenAI
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self._judge_client = OpenAI(api_key=api_key)
        except Exception as e:
            logger.warning(f"Judge inicializálás sikertelen: {e}")
    
    def evaluate_single_turn(
        self,
        query: str,
        context: List[Dict[str, Any]],
        expected_answer: str = None
    ) -> Dict[str, Any]:
        """
        Single-turn értékelés
        
        Args:
            query: Kérdés
            context: Kontextus dokumentumok
            expected_answer: Várt válasz (opcionális)
            
        Returns:
            Értékelési eredmények
        """
        # Válasz generálása
        answer = self.llm_generator.generate(query, context)
        
        results = {
            'query': query,
            'answer': answer,
            'context_relevance': self.evaluate_context_relevance(query, context, answer),
            'hallucination_score': self.detect_hallucination(context, answer)
        }
        
        if expected_answer:
            results['answer_similarity'] = self.compare_answers(answer, expected_answer)
        
        return results
    
    def evaluate_context_relevance(
        self,
        query: str,
        context: List[Dict[str, Any]],
        answer: str
    ) -> float:
        """
        Context relevance értékelése
        
        Args:
            query: Kérdés
            context: Kontextus
            answer: Generált válasz
            
        Returns:
            Relevance score (0-1)
        """
        if not self._judge_client:
            # Egyszerű heurisztika ha nincs judge
            context_text = " ".join([doc.get('text', '')[:500] for doc in context])
            query_words = set(query.lower().split())
            context_words = set(context_text.lower().split())
            overlap = len(query_words & context_words)
            return min(overlap / len(query_words) if query_words else 0, 1.0)
        
        try:
            prompt = f"""Értékeld, hogy a válasz mennyire releváns a kontextushoz és a kérdéshez.

Kérdés: {query}

Kontextus:
{self._format_context(context)}

Válasz: {answer}

Adj egy 0-1 közötti relevancia pontszámot, ahol:
- 1.0 = tökéletesen releváns
- 0.5 = részben releváns
- 0.0 = nem releváns

Csak a számot add vissza."""
            
            response = self._judge_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            
            score = float(response.choices[0].message.content.strip())
            return max(0.0, min(1.0, score))
        
        except Exception as e:
            logger.error(f"Hiba a context relevance értékelésénél: {e}")
            return 0.5
    
    def detect_hallucination(
        self,
        context: List[Dict[str, Any]],
        answer: str
    ) -> float:
        """
        Hallucináció detektálás
        
        Args:
            context: Kontextus
            answer: Generált válasz
            
        Returns:
            Hallucináció score (0-1, ahol 0 = nincs hallucináció, 1 = sok hallucináció)
        """
        if not self._judge_client:
            # Egyszerű heurisztika
            context_text = " ".join([doc.get('text', '') for doc in context]).lower()
            answer_words = set(answer.lower().split())
            context_words = set(context_text.split())
            
            # Hány szó van a válaszban, ami nincs a kontextusban
            unique_words = answer_words - context_words
            hallucination_ratio = len(unique_words) / len(answer_words) if answer_words else 0
            return min(hallucination_ratio, 1.0)
        
        try:
            prompt = f"""Értékeld, hogy a válasz mennyire tartalmaz hallucinációt (információt, ami nincs a kontextusban).

Kontextus:
{self._format_context(context)}

Válasz: {answer}

Adj egy 0-1 közötti hallucináció pontszámot, ahol:
- 0.0 = nincs hallucináció, minden információ a kontextusban van
- 0.5 = részben hallucináció
- 1.0 = sok hallucináció, a válasz nagy része nincs a kontextusban

Csak a számot add vissza."""
            
            response = self._judge_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            
            score = float(response.choices[0].message.content.strip())
            return max(0.0, min(1.0, score))
        
        except Exception as e:
            logger.error(f"Hiba a hallucináció detektálásánál: {e}")
            return 0.5
    
    def compare_answers(self, answer1: str, answer2: str) -> float:
        """
        Két válasz hasonlóságának összehasonlítása
        
        Args:
            answer1: Első válasz
            answer2: Második válasz
            
        Returns:
            Hasonlósági score (0-1)
        """
        # Egyszerű token overlap
        words1 = set(answer1.lower().split())
        words2 = set(answer2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        jaccard = len(intersection) / len(union) if union else 0
        return jaccard
    
    def _format_context(self, context: List[Dict[str, Any]]) -> str:
        """Kontextus formázása"""
        parts = []
        for i, doc in enumerate(context, 1):
            text = doc.get('text', '')[:500]  # Első 500 karakter
            parts.append(f"[{i}] {text}")
        return "\n\n".join(parts)
    
    def run_evaluation(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Teljes prompt értékelés futtatása
        
        Args:
            test_cases: Teszt esetek
            
        Returns:
            Összesített eredmények
        """
        results = []
        
        for test_case in test_cases:
            result = self.evaluate_single_turn(
                query=test_case['query'],
                context=test_case.get('context', []),
                expected_answer=test_case.get('expected_answer')
            )
            results.append(result)
        
        # Összesített metrikák
        avg_context_relevance = sum(r['context_relevance'] for r in results) / len(results)
        avg_hallucination = sum(r['hallucination_score'] for r in results) / len(results)
        
        return {
            'results': results,
            'summary': {
                'num_tests': len(results),
                'avg_context_relevance': avg_context_relevance,
                'avg_hallucination_score': avg_hallucination
            }
        }
    
    def save_results(self, results: Dict[str, Any], file_path: str):
        """Eredmények mentése"""
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

