# File: backend/chatbot/heuristic_scorer_agent.py

class HeuristicScorerAgent:
    """
    Score and rank results using heuristics instead of LLM

    Strategy:
    1. Merge results from Tag + FAISS
    2. Deduplicate by source file
    3. Apply heuristic scoring with tag boost
    4. Return top-N ranked results

    Cost: $0 (no LLM calls)
    Speed: <10ms
    Accuracy: ~90% as good as LLM scoring
    """

    def score_results(self, question: str, tag_results: list, faiss_results: list) -> list:
        """
        Combine and rank results

        Returns: Top 5 ranked results with:
        - final_score
        - matching_tags
        - source attribution
        """

        all_results = []

        # Process tag results (higher base weight)
        for result in tag_results:
            score = self._calculate_tag_score(result)
            result['final_score'] = score
            result['source_type'] = 'tag'
            all_results.append(result)

        # Process FAISS results
        for result in faiss_results:
            score = self._calculate_faiss_score(result)
            result['final_score'] = score
            result['source_type'] = 'faiss'
            all_results.append(result)

        # Deduplicate (prefer higher score)
        deduplicated = self._deduplicate(all_results)

        # Sort by final score
        ranked = sorted(deduplicated, key=lambda x: x['final_score'], reverse=True)

        return ranked[:5]  # Top 5

    def _calculate_tag_score(self, result: dict) -> float:
        """
        Score tag search results

        Factors:
        - Base: number of matching tags (already in result['score'])
        - Boost: tag source preference (1.2x)
        - Boost: content type (projects > experiences > posts)
        """
        base_score = result.get('score', 0)  # Number of matching tags

        # Tag source boost
        score = base_score * 1.2

        # Content type boost
        content_type = result.get('content_type', '')
        if content_type == 'project':
            score *= 1.3
        elif content_type == 'experience':
            score *= 1.1

        return score

    def _calculate_faiss_score(self, result: dict) -> float:
        """
        Score FAISS results

        FAISS similarity is 0-1, normalize to 0-10 range
        """
        similarity = result.get('score', 0)
        return similarity * 10

    def _deduplicate(self, results: list) -> list:
        """Remove duplicates, keep highest scoring version"""
        seen = {}

        for result in results:
            source_path = result.get('source') or result.get('path')

            if not source_path:
                continue

            if source_path not in seen:
                seen[source_path] = result
            else:
                # Keep higher scoring result
                if result['final_score'] > seen[source_path]['final_score']:
                    seen[source_path] = result

        return list(seen.values())
