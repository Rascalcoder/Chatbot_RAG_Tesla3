"""
Evaluation futtatás script
"""

import os
import sys
import logging
from pathlib import Path

# Logging beállítása
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# RAG rendszer import
from src.rag_system import RAGSystem
from src.evaluation.rag_eval import RAGEvaluator
from src.evaluation.prompt_eval import PromptEvaluator
from src.evaluation.app_eval import AppEvaluator
from src.evaluation.test_cases import RAG_TEST_CASES, PROMPT_TEST_CASES, APP_TEST_CASES


def run_rag_evaluation():
    """RAG szintű evaluation futtatása"""
    logger.info("RAG szintű evaluation indítása...")
    
    try:
        # RAG rendszer inicializálása
        rag_system = RAGSystem()
        
        # Evaluator inicializálása
        evaluator = RAGEvaluator(
            vector_store=rag_system.vector_store,
            retrieval_engine=rag_system.retrieval_engine,
            embedding_model=rag_system.embedding_model,
            chunking_strategy=rag_system.chunking
        )
        
        # Evaluation futtatása
        results = evaluator.run_full_evaluation(RAG_TEST_CASES)
        
        # Eredmények mentése
        output_path = Path("./evaluations/rag_evaluation_results.json")
        evaluator.save_results(results, str(output_path))
        
        logger.info(f"RAG evaluation befejezve. Eredmények: {output_path}")
        print("\n=== RAG Evaluation Eredmények ===")
        rm = results.get('retrieval_metrics', {})
        # Új kulcsszó alapú formátum
        if 'keyword_metrics' in rm:
            km = rm['keyword_metrics']
            br = rm.get('basic_retrieval', {})
            print(f"Retrieval Precision (kulcsszó): {km.get('precision', 0):.3f}")
            print(f"Retrieval Recall (kulcsszó): {km.get('recall', 0):.3f}")
            print(f"MRR (kulcsszó): {km.get('mrr', 0):.3f}")
            print(f"Általános retrieval sikeresség: {br.get('success_rate', 0):.1%}")
        else:
            print(f"Retrieval Precision: {rm.get('precision', 0):.3f}")
            print(f"Retrieval Recall: {rm.get('recall', 0):.3f}")
            print(f"MRR: {rm.get('mrr', 0):.3f}")
        
        return results
    
    except Exception as e:
        logger.error(f"Hiba a RAG evaluation során: {e}")
        raise


def run_prompt_evaluation():
    """Prompt szintű evaluation futtatása"""
    logger.info("Prompt szintű evaluation indítása...")
    
    try:
        # RAG rendszer inicializálása
        rag_system = RAGSystem()
        
        # Evaluator inicializálása
        evaluator = PromptEvaluator(llm_generator=rag_system.llm_generator)
        
        # Evaluation futtatása
        results = evaluator.run_evaluation(PROMPT_TEST_CASES)
        
        # Eredmények mentése
        output_path = Path("./evaluations/prompt_evaluation_results.json")
        evaluator.save_results(results, str(output_path))
        
        logger.info(f"Prompt evaluation befejezve. Eredmények: {output_path}")
        print("\n=== Prompt Evaluation Eredmények ===")
        summary = results.get('summary', {})
        print(f"Átlagos Context Relevance: {summary.get('avg_context_relevance', 0):.3f}")
        print(f"Átlagos Hallucináció Score: {summary.get('avg_hallucination_score', 0):.3f}")
        
        return results
    
    except Exception as e:
        logger.error(f"Hiba a prompt evaluation során: {e}")
        raise


def run_app_evaluation():
    """Alkalmazás szintű evaluation futtatása"""
    logger.info("Alkalmazás szintű evaluation indítása...")
    
    try:
        # RAG rendszer inicializálása
        rag_system = RAGSystem()
        
        # Evaluator inicializálása
        evaluator = AppEvaluator(rag_system=rag_system)
        
        # Evaluation futtatása
        results = evaluator.run_full_evaluation(APP_TEST_CASES)
        
        # Eredmények mentése
        output_path = Path("./evaluations/app_evaluation_results.json")
        evaluator.save_results(results, str(output_path))
        
        logger.info(f"App evaluation befejezve. Eredmények: {output_path}")
        print("\n=== Alkalmazás Evaluation Eredmények ===")
        if 'latency' in results:
            latency = results['latency']
            print(f"Átlagos First Token Time: {latency.get('avg_first_token_time', 0):.3f}s")
            print(f"Átlagos Total Time: {latency.get('avg_total_time', 0):.3f}s")
        
        return results
    
    except Exception as e:
        logger.error(f"Hiba az app evaluation során: {e}")
        raise


def main():
    """Fő függvény"""
    import argparse
    
    parser = argparse.ArgumentParser(description='RAG Evaluation Runner')
    parser.add_argument(
        '--type',
        choices=['rag', 'prompt', 'app', 'all'],
        default='all',
        help='Evaluation típusa'
    )
    
    args = parser.parse_args()
    
    # Eredmények könyvtár létrehozása
    Path("./evaluations").mkdir(parents=True, exist_ok=True)
    
    try:
        if args.type in ['rag', 'all']:
            run_rag_evaluation()
        
        if args.type in ['prompt', 'all']:
            run_prompt_evaluation()
        
        if args.type in ['app', 'all']:
            run_app_evaluation()
        
        print("\n[OK] Osszes evaluation befejezve!")
    
    except Exception as e:
        logger.error(f"Evaluation hiba: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

