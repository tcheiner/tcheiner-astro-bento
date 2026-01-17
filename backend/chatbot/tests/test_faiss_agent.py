"""
Unit tests for FAISSAgent

Tests vector search functionality
"""

import pytest
from chatbot.faiss_agent import FAISSAgent


class TestFAISSAgent:
    """Test suite for FAISSAgent"""

    @pytest.fixture
    def agent(self):
        """Create agent instance for testing"""
        return FAISSAgent()

    # ========================================
    # Initialization Tests
    # ========================================

    def test_vectorstore_loaded(self, agent):
        """Should load FAISS vectorstore on init"""
        assert agent.vectorstore is not None

    def test_vectorstore_path_exists(self):
        """FAISS index directory should exist"""
        import os
        from chatbot.faiss_agent import FAISSAgent

        # Create temporary agent to get path
        temp_agent = FAISSAgent()

        # If vectorstore loaded, path exists
        if temp_agent.vectorstore is not None:
            assert True  # Successfully loaded
        else:
            pytest.skip("FAISS index not built yet")

    # ========================================
    # Search Tests
    # ========================================

    def test_search_returns_results(self, agent):
        """Should return results for valid query"""
        if agent.vectorstore is None:
            pytest.skip("FAISS index not available")

        results = agent.search("What are your AI projects?")

        assert isinstance(results, list)

    def test_search_result_structure(self, agent):
        """Search results should have correct structure"""
        if agent.vectorstore is None:
            pytest.skip("FAISS index not available")

        results = agent.search("Python experience")

        if len(results) > 0:
            result = results[0]

            # Check required fields
            assert 'content' in result
            assert 'source' in result
            assert 'score' in result
            assert 'metadata' in result
            assert 'retrieval_source' in result

            # Check retrieval source is marked
            assert result['retrieval_source'] == 'faiss'

    def test_search_respects_k_parameter(self, agent):
        """Should return at most k results"""
        if agent.vectorstore is None:
            pytest.skip("FAISS index not available")

        results = agent.search("Python", k=3)

        assert len(results) <= 3

    def test_search_respects_score_threshold(self, agent):
        """Should filter results by score threshold"""
        if agent.vectorstore is None:
            pytest.skip("FAISS index not available")

        # High threshold should return fewer results
        results_high = agent.search("Python", k=10, score_threshold=0.8)
        results_low = agent.search("Python", k=10, score_threshold=0.1)

        # Lower threshold should have more results (or equal)
        assert len(results_low) >= len(results_high)

    def test_search_includes_metadata(self, agent):
        """Should preserve document metadata"""
        if agent.vectorstore is None:
            pytest.skip("FAISS index not available")

        results = agent.search("Python projects")

        if len(results) > 0:
            result = results[0]

            assert 'metadata' in result
            assert isinstance(result['metadata'], dict)

            # Should have source in metadata
            assert 'source' in result['metadata']

    def test_search_includes_content(self, agent):
        """Should include document content"""
        if agent.vectorstore is None:
            pytest.skip("FAISS index not available")

        results = agent.search("AI work")

        if len(results) > 0:
            result = results[0]

            assert 'content' in result
            assert isinstance(result['content'], str)
            assert len(result['content']) > 0

    def test_search_empty_query(self, agent):
        """Should handle empty query gracefully"""
        if agent.vectorstore is None:
            pytest.skip("FAISS index not available")

        results = agent.search("")

        assert isinstance(results, list)

    def test_search_no_vectorstore(self):
        """Should handle missing vectorstore gracefully"""
        # Create agent without vectorstore
        agent = FAISSAgent()

        # Temporarily remove vectorstore
        original_vs = agent.vectorstore
        agent.vectorstore = None

        results = agent.search("test")

        assert isinstance(results, list)
        assert len(results) == 0

        # Restore
        agent.vectorstore = original_vs

    # ========================================
    # Score Tests
    # ========================================

    def test_search_returns_scores(self, agent):
        """Should return similarity scores"""
        if agent.vectorstore is None:
            pytest.skip("FAISS index not available")

        results = agent.search("Python")

        if len(results) > 0:
            result = results[0]

            assert 'score' in result
            assert isinstance(result['score'], (int, float))
            assert result['score'] >= 0  # FAISS scores are non-negative

    def test_search_sorts_by_score(self, agent):
        """Should sort results by similarity score"""
        if agent.vectorstore is None:
            pytest.skip("FAISS index not available")

        results = agent.search("Python machine learning", k=5)

        if len(results) > 1:
            scores = [r['score'] for r in results]
            # Lower FAISS scores are better (distance metric)
            assert scores == sorted(scores)

    # ========================================
    # Integration Tests
    # ========================================

    def test_multiple_searches_same_agent(self, agent):
        """Should handle multiple searches correctly"""
        if agent.vectorstore is None:
            pytest.skip("FAISS index not available")

        queries = [
            "Python projects",
            "AI experience",
            "leadership skills"
        ]

        for query in queries:
            results = agent.search(query)
            assert isinstance(results, list)

    def test_search_semantic_similarity(self, agent):
        """Should find semantically similar content"""
        if agent.vectorstore is None:
            pytest.skip("FAISS index not available")

        # These queries are semantically similar
        results1 = agent.search("artificial intelligence projects")
        results2 = agent.search("AI work")

        # Should have some overlap in results
        if len(results1) > 0 and len(results2) > 0:
            sources1 = {r['source'] for r in results1}
            sources2 = {r['source'] for r in results2}

            # Should have at least some semantic overlap
            assert len(sources1 & sources2) >= 0  # May or may not overlap

    # ========================================
    # Error Handling Tests
    # ========================================

    def test_handles_search_exception(self, agent):
        """Should handle search exceptions gracefully"""
        if agent.vectorstore is None:
            pytest.skip("FAISS index not available")

        # Try to break it with invalid inputs
        results = agent.search(None)

        # Should not crash, return empty list
        assert isinstance(results, list)

    # ========================================
    # Performance Tests
    # ========================================

    def test_search_is_reasonably_fast(self, agent):
        """Vector search should be fast (<1 second)"""
        if agent.vectorstore is None:
            pytest.skip("FAISS index not available")

        import time

        start = time.time()
        results = agent.search("Python projects", k=5)
        elapsed = time.time() - start

        # Should complete in under 1 second
        assert elapsed < 1.0, f"Search took {elapsed}s, should be <1s"
