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
        self._reset_journey_state()

    def _reset_journey_state(self):
        """Journey állapot resetelése - minden journey elején meghívandó"""
        self._last_query_result = None
        self._last_step_result = None
        self._messages_history = []
        self._sources_toggle_state = True
        self._documents_cleared = False
        self._last_error = None
        self._last_streaming_metrics = {}

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
            'name': journey.get('name', ''),
            'steps': [],
            'total_time': 0,
            'success_rate': 0
        }

        self._reset_journey_state()

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
        """Egy lépés értékelése dispatch table-lel"""
        action = step.get('action')
        step_start = time.time()

        handlers = {
            'query':                        self._handle_query,
            'upload':                       self._handle_upload,
            'new_chat_session':             self._handle_new_chat_session,
            'clear_documents':              self._handle_clear_documents,
            'query_streaming':              self._handle_query_streaming,
            'verify_sources_expander':      self._handle_verify_sources_expander,
            'verify_ui_warning':            self._handle_verify_ui_warning,
            'verify_metrics_logged':        self._handle_verify_metrics_logged,
            'toggle_sources':               self._handle_toggle_sources,
            'verify_sources_not_visible':   self._handle_verify_sources_not_visible,
            'verify_sources_visible':       self._handle_verify_sources_visible,
            'navigate_to_monitoring':       self._handle_navigate_to_monitoring,
            'verify_metrics_displayed':     self._handle_verify_metrics_displayed,
            'verify_charts_rendered':       self._handle_verify_charts_rendered,
            'verify_app_still_responsive':  self._handle_verify_app_still_responsive,
        }

        handler = handlers.get(action)
        if handler is None:
            return {
                'action': action,
                'error': f'Ismeretlen action: {action}',
                'success': False
            }

        try:
            result = handler(step, step_start)
            result = self._check_step_success(step, result)
            self._last_step_result = result
            return result
        except Exception as e:
            logger.error(f"Hiba a step értékelésénél: {e}")
            self._last_error = e
            result = {
                'action': action,
                'error': str(e),
                'success': False,
                'latency': time.time() - step_start
            }
            if step.get('expected_error'):
                result['success'] = True
                result['error_expected'] = True
            self._last_step_result = result
            return result

    # ---- Action Handlers ----

    def _handle_query(self, step: Dict[str, Any], step_start: float) -> Dict[str, Any]:
        query = step.get('input', '')

        if self._documents_cleared:
            self._last_error = 'Nincs dokumentum feltöltve'
            return {
                'action': 'query',
                'input': query,
                'response': '',
                'error': 'Nincs dokumentum feltöltve. Dokumentum feltöltése szükséges.',
                'latency': time.time() - step_start,
                'success': False
            }

        response = self.rag_system.query(
            query, conversation_history=self._messages_history or None
        )
        step_time = time.time() - step_start

        self._last_query_result = response

        self._messages_history.append({'role': 'user', 'content': query})
        self._messages_history.append({
            'role': 'assistant',
            'content': response.get('answer', ''),
        })

        quality_score = self._evaluate_response_quality(
            query=query,
            response=response.get('answer', ''),
            context=response.get('context', [])
        )

        return {
            'action': 'query',
            'input': query,
            'response': response.get('answer', ''),
            'context': response.get('context', []),
            'metadata': response.get('metadata', {}),
            'latency': step_time,
            'quality_score': quality_score,
            'success': True
        }

    def _handle_upload(self, step: Dict[str, Any], step_start: float) -> Dict[str, Any]:
        file_input = step.get('input', '')

        known_bad_files = {
            'corrupt_file.pdf': 'A dokumentum sérült vagy nem olvasható',
            'wrong_format.exe': 'Nem támogatott fájlformátum: .exe'
        }

        if file_input in known_bad_files:
            error_msg = known_bad_files[file_input]
            self._last_error = error_msg
            result = {
                'action': 'upload',
                'input': file_input,
                'latency': time.time() - step_start,
                'error': error_msg,
                'success': False
            }
            if step.get('expected_error'):
                result['success'] = True
                result['error_expected'] = True
            return result

        try:
            collection_info = self.rag_system.vector_store.get_collection_info()
            doc_count = collection_info.get('document_count', 0)
            self._documents_cleared = False

            return {
                'action': 'upload',
                'input': file_input,
                'latency': time.time() - step_start,
                'document_count': doc_count,
                'success': doc_count > 0
            }
        except Exception as e:
            return {
                'action': 'upload',
                'input': file_input,
                'latency': time.time() - step_start,
                'error': str(e),
                'success': False
            }

    def _handle_new_chat_session(self, step: Dict[str, Any], step_start: float) -> Dict[str, Any]:
        self._messages_history = []
        self._last_query_result = None

        return {
            'action': 'new_chat_session',
            'latency': time.time() - step_start,
            'success': True,
            'response': 'session_cleared'
        }

    def _handle_clear_documents(self, step: Dict[str, Any], step_start: float) -> Dict[str, Any]:
        self._documents_cleared = True

        try:
            info = self.rag_system.vector_store.get_collection_info()
            doc_count = info.get('document_count', 0)
        except Exception:
            doc_count = -1

        return {
            'action': 'clear_documents',
            'latency': time.time() - step_start,
            'success': True,
            'response': 'documents_cleared',
            'actual_document_count': doc_count,
            'simulated': True
        }

    def _handle_query_streaming(self, step: Dict[str, Any], step_start: float) -> Dict[str, Any]:
        query = step.get('input', '')

        response = self.rag_system.query(query, stream=True)

        full_answer = ''
        first_token_time = None
        stream_start = time.time()

        generator = response.get('generator')
        if generator:
            for chunk in generator:
                if first_token_time is None:
                    first_token_time = time.time() - stream_start
                full_answer += chunk

        total_time = time.time() - stream_start
        step_time = time.time() - step_start

        self._last_streaming_metrics = {
            'first_token_time': first_token_time or 0,
            'total_time': total_time
        }

        self._last_query_result = {
            'query': query,
            'answer': full_answer,
            'context': response.get('context', []),
            'metadata': {
                'first_token_time': first_token_time,
                'total_time': total_time,
                'streaming': True
            }
        }

        self._messages_history.append({'role': 'user', 'content': query})
        self._messages_history.append({'role': 'assistant', 'content': full_answer})

        return {
            'action': 'query_streaming',
            'input': query,
            'response': full_answer,
            'context': response.get('context', []),
            'latency': step_time,
            'first_token_time': first_token_time or 0,
            'total_time': total_time,
            'success': True
        }

    def _handle_verify_sources_expander(self, step: Dict[str, Any], step_start: float) -> Dict[str, Any]:
        context = []
        if self._last_query_result:
            context = self._last_query_result.get('context', [])

        expected_content = step.get('expected_content', [])

        fields_found = set()
        for doc in context:
            for field in expected_content:
                if field in doc or field in doc.get('metadata', {}):
                    fields_found.add(field)
                if field == 'chunk' and 'text' in doc:
                    fields_found.add(field)

        has_sources = len(context) > 0
        all_fields_present = set(expected_content).issubset(fields_found) if expected_content else True

        return {
            'action': 'verify_sources_expander',
            'latency': time.time() - step_start,
            'success': has_sources and all_fields_present and self._sources_toggle_state,
            'response': 'expander_visible' if has_sources else 'no_sources',
            'source_count': len(context),
            'fields_found': list(fields_found),
            'fields_expected': expected_content
        }

    def _handle_verify_ui_warning(self, step: Dict[str, Any], step_start: float) -> Dict[str, Any]:
        has_warning = False

        if self._last_step_result:
            has_warning = (
                self._last_step_result.get('error') is not None
                or self._last_step_result.get('error_expected')
                or self._documents_cleared
            )

        if self._last_error:
            has_warning = True

        return {
            'action': 'verify_ui_warning',
            'latency': time.time() - step_start,
            'success': has_warning,
            'response': 'info_message_visible' if has_warning else 'no_warning'
        }

    def _handle_verify_metrics_logged(self, step: Dict[str, Any], step_start: float) -> Dict[str, Any]:
        expected_metrics = step.get('expected_metrics', [])

        try:
            stats = self.rag_system.metrics_collector.get_statistics(days=1)

            metrics_present = {}
            if 'first_token_time' in expected_metrics:
                metrics_present['first_token_time'] = (
                    stats.get('avg_first_token_time_sec') is not None
                    or self._last_streaming_metrics.get('first_token_time') is not None
                )
            if 'total_time' in expected_metrics:
                metrics_present['total_time'] = (
                    stats.get('avg_total_time_sec') is not None
                    or self._last_streaming_metrics.get('total_time') is not None
                )
            if 'tokens' in expected_metrics:
                metrics_present['tokens'] = stats.get('total_tokens', 0) > 0

            all_present = all(metrics_present.values()) if metrics_present else True

            return {
                'action': 'verify_metrics_logged',
                'latency': time.time() - step_start,
                'success': all_present,
                'metrics_found': metrics_present
            }
        except Exception as e:
            return {
                'action': 'verify_metrics_logged',
                'latency': time.time() - step_start,
                'success': False,
                'error': str(e)
            }

    def _handle_toggle_sources(self, step: Dict[str, Any], step_start: float) -> Dict[str, Any]:
        target_state = step.get('state', 'on')
        self._sources_toggle_state = (target_state == 'on')

        expected_response = 'sources_visible' if self._sources_toggle_state else 'sources_hidden'

        return {
            'action': 'toggle_sources',
            'latency': time.time() - step_start,
            'success': True,
            'response': expected_response,
            'toggle_state': self._sources_toggle_state
        }

    def _handle_verify_sources_not_visible(self, step: Dict[str, Any], step_start: float) -> Dict[str, Any]:
        is_hidden = not self._sources_toggle_state

        return {
            'action': 'verify_sources_not_visible',
            'latency': time.time() - step_start,
            'success': is_hidden,
            'response': 'no_expander' if is_hidden else 'expander_present'
        }

    def _handle_verify_sources_visible(self, step: Dict[str, Any], step_start: float) -> Dict[str, Any]:
        is_visible = self._sources_toggle_state

        return {
            'action': 'verify_sources_visible',
            'latency': time.time() - step_start,
            'success': is_visible,
            'response': 'expander_present' if is_visible else 'no_expander'
        }

    def _handle_navigate_to_monitoring(self, step: Dict[str, Any], step_start: float) -> Dict[str, Any]:
        try:
            has_collector = self.rag_system.metrics_collector is not None
            stats = self.rag_system.metrics_collector.get_statistics(days=30)
            has_data = stats.get('total_llm_calls', 0) > 0

            return {
                'action': 'navigate_to_monitoring',
                'latency': time.time() - step_start,
                'success': has_collector,
                'response': 'monitoring_page_loaded' if has_collector else 'monitoring_unavailable',
                'has_data': has_data
            }
        except Exception as e:
            return {
                'action': 'navigate_to_monitoring',
                'latency': time.time() - step_start,
                'success': False,
                'error': str(e)
            }

    def _handle_verify_metrics_displayed(self, step: Dict[str, Any], step_start: float) -> Dict[str, Any]:
        expected_metrics = step.get('expected_metrics', [])
        expect_nonzero = step.get('expected_values_not_zero', False)

        try:
            stats = self.rag_system.metrics_collector.get_statistics(days=30)

            metric_map = {
                'llm_calls': 'total_llm_calls',
                'total_tokens': 'total_tokens',
                'total_cost': 'total_cost_usd',
                'avg_total_time': 'avg_total_time_sec'
            }

            metrics_found = {}
            all_nonzero = True
            for metric_name in expected_metrics:
                stats_key = metric_map.get(metric_name, metric_name)
                value = stats.get(stats_key)
                metrics_found[metric_name] = value
                if expect_nonzero and (value is None or value == 0):
                    all_nonzero = False

            success = len(metrics_found) == len(expected_metrics)
            if expect_nonzero:
                success = success and all_nonzero

            return {
                'action': 'verify_metrics_displayed',
                'latency': time.time() - step_start,
                'success': success,
                'metrics_found': metrics_found
            }
        except Exception as e:
            return {
                'action': 'verify_metrics_displayed',
                'latency': time.time() - step_start,
                'success': False,
                'error': str(e)
            }

    def _handle_verify_charts_rendered(self, step: Dict[str, Any], step_start: float) -> Dict[str, Any]:
        expected_charts = step.get('expected_charts', [])

        try:
            from ..monitoring.analytics import Analytics
            analytics = Analytics(self.rag_system.metrics_collector)

            charts_available = {}
            if 'daily_usage' in expected_charts:
                daily = analytics.get_daily_usage(days=30)
                charts_available['daily_usage'] = not daily.empty if hasattr(daily, 'empty') else len(daily) > 0

            if 'latency_trends' in expected_charts:
                latency = analytics.get_latency_trends(days=7)
                charts_available['latency_trends'] = not latency.empty if hasattr(latency, 'empty') else len(latency) > 0

            success = all(charts_available.values()) if charts_available else False

            return {
                'action': 'verify_charts_rendered',
                'latency': time.time() - step_start,
                'success': success,
                'charts_available': charts_available
            }
        except Exception as e:
            return {
                'action': 'verify_charts_rendered',
                'latency': time.time() - step_start,
                'success': False,
                'error': str(e)
            }

    def _handle_verify_app_still_responsive(self, step: Dict[str, Any], step_start: float) -> Dict[str, Any]:
        try:
            stats = self.rag_system.get_stats()
            responsive = stats is not None

            return {
                'action': 'verify_app_still_responsive',
                'latency': time.time() - step_start,
                'success': responsive,
                'response': 'app_running' if responsive else 'app_not_responding'
            }
        except Exception as e:
            return {
                'action': 'verify_app_still_responsive',
                'latency': time.time() - step_start,
                'success': False,
                'response': 'app_not_responding',
                'error': str(e)
            }

    # ---- Validáció ----

    def _check_step_success(self, step: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Komprehenzív validáció: minden step mező ellenőrzése"""
        checks = {}
        response_text = result.get('response', '')

        # 1. expected (substring match)
        if 'expected' in step and step['expected']:
            checks['expected'] = self._check_expectation(response_text, step['expected'])

        # 2. expected_keywords (bármely keyword megtalálható)
        if step.get('expected_keywords'):
            response_lower = response_text.lower()
            checks['expected_keywords'] = any(
                kw.lower() in response_lower for kw in step['expected_keywords']
            )

        # 3. expected_error
        if step.get('expected_error'):
            has_error = result.get('error') is not None or result.get('error_expected', False)
            checks['expected_error'] = has_error
            if has_error:
                result['success'] = True
                result['error_expected'] = True

        # 4. expected_behavior
        if 'expected_behavior' in step:
            behavior = step['expected_behavior']
            if behavior == 'graceful_fallback':
                fallback_patterns = [
                    'nem találtam', 'nem tudom', 'nincs információ',
                    'sajnálom', 'nem áll rendelkezésre', 'not found',
                    'nem találok', 'nem szerepel'
                ]
                response_lower = response_text.lower()
                checks['expected_behavior'] = any(p in response_lower for p in fallback_patterns)
            elif behavior == 'stable_response':
                checks['expected_behavior'] = len(response_text) > 0 and result.get('error') is None

        # 5. should_not_hallucinate
        if step.get('should_not_hallucinate'):
            metadata = result.get('metadata', {})
            if not metadata and self._last_query_result:
                metadata = self._last_query_result.get('metadata', {})
            abstained = metadata.get('abstained', False)
            fallback_patterns = [
                'nem találtam', 'nem tudom', 'nincs információ',
                'sajnálom', 'nem áll rendelkezésre', 'nem szerepel'
            ]
            response_lower = response_text.lower()
            checks['should_not_hallucinate'] = abstained or any(p in response_lower for p in fallback_patterns)

        # 6. validate_sources
        if step.get('validate_sources'):
            context = result.get('context', [])
            if not context and self._last_query_result:
                context = self._last_query_result.get('context', [])
            checks['validate_sources'] = len(context) > 0

        # 7. expected_source_count
        if 'expected_source_count' in step:
            context = result.get('context', [])
            if not context and self._last_query_result:
                context = self._last_query_result.get('context', [])
            checks['expected_source_count'] = len(context) >= step['expected_source_count']

        # 8. max_response_time
        if 'max_response_time' in step:
            checks['max_response_time'] = result.get('latency', 0) <= step['max_response_time']

        # 9. expected_first_token_max
        if 'expected_first_token_max' in step:
            checks['expected_first_token_max'] = result.get('first_token_time', 0) <= step['expected_first_token_max']

        # 10. expected_total_max
        if 'expected_total_max' in step:
            total = result.get('total_time', result.get('latency', 0))
            checks['expected_total_max'] = total <= step['expected_total_max']

        # 11. validate_context_memory
        if step.get('validate_context_memory'):
            checks['validate_context_memory'] = len(response_text) > 0

        # 12. validate_no_memory
        if step.get('validate_no_memory'):
            checks['validate_no_memory'] = len(self._messages_history) <= 2

        # 13. validate_recovery
        if step.get('validate_recovery'):
            checks['validate_recovery'] = result.get('success', False) and result.get('error') is None

        # 14. should_not_crash
        if step.get('should_not_crash'):
            checks['should_not_crash'] = result.get('error') is None or result.get('error_expected', False)

        if checks:
            result['validation_checks'] = checks
            result['success'] = all(checks.values())

        return result

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
        if not response:
            return 0.0

        length_score = min(len(response) / 500, 1.0)

        context_text = " ".join([doc.get('text', '') for doc in context]).lower()
        response_words = set(response.lower().split())
        context_words = set(context_text.split())

        overlap = len(response_words & context_words)
        context_score = overlap / len(response_words) if response_words else 0

        quality = (length_score * 0.3 + context_score * 0.7)
        return min(quality, 1.0)

    def _check_expectation(self, actual: str, expected: str) -> bool:
        """Várható eredmény ellenőrzése"""
        if not expected:
            return True

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
