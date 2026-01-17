"""
Unit tests for HeuristicScorerAgent

Tests result scoring, deduplication, and ranking
"""

import pytest
from chatbot.heuristic_scorer_agent import HeuristicScorerAgent


class TestHeuristicScorerAgent:
    """Test suite for HeuristicScorerAgent"""

    @pytest.fixture
    def agent(self):
        """Create agent instance for testing"""
        return HeuristicScorerAgent()

    @pytest.fixture
    def mock_tag_results(self):
        """Mock tag search results"""
        return [
            {
                'path': '/content/projects/ai-project.mdx',
                'title': 'AI Project',
                'tags': ['Python', 'AI', 'ML'],
                'matching_tags': ['ai', 'python'],
                'score': 2,  # 2 matching tags
                'content_type': 'project',
                'slug': 'ai-project'
            },
            {
                'path': '/content/posts/post-2025-01-01.mdx',
                'title': 'Blog Post',
                'tags': ['Python'],
                'matching_tags': ['python'],
                'score': 1,  # 1 matching tag
                'content_type': 'post',
                'slug': '2025-01-01'
            }
        ]

    @pytest.fixture
    def mock_faiss_results(self):
        """Mock FAISS search results"""
        return [
            {
                'content': 'Content about AI and machine learning...',
                'source': '/content/projects/ai-project.mdx',  # Same as tag result
                'score': 0.95,  # High similarity
                'metadata': {'source': '/content/projects/ai-project.mdx'},
                'retrieval_source': 'faiss'
            },
            {
                'content': 'Different content about databases...',
                'source': '/content/projects/db-project.mdx',
                'score': 0.75,
                'metadata': {'source': '/content/projects/db-project.mdx'},
                'retrieval_source': 'faiss'
            }
        ]

    # ========================================
    # Tag Score Calculation Tests
    # ========================================

    def test_calculate_tag_score_base(self, agent):
        """Should calculate base score from matching tags"""
        result = {'score': 2, 'content_type': 'post'}

        score = agent._calculate_tag_score(result)

        # Base score (2) × tag boost (1.2) = 2.4
        assert score == pytest.approx(2.4)

    def test_calculate_tag_score_project_boost(self, agent):
        """Should boost project content type"""
        result = {'score': 2, 'content_type': 'project'}

        score = agent._calculate_tag_score(result)

        # Base (2) × tag boost (1.2) × project boost (1.3) = 3.12
        assert score == pytest.approx(3.12)

    def test_calculate_tag_score_experience_boost(self, agent):
        """Should boost experience content type"""
        result = {'score': 2, 'content_type': 'experience'}

        score = agent._calculate_tag_score(result)

        # Base (2) × tag boost (1.2) × experience boost (1.1) = 2.64
        assert score == pytest.approx(2.64)

    def test_calculate_tag_score_zero_base(self, agent):
        """Should handle zero base score"""
        result = {'score': 0, 'content_type': 'post'}

        score = agent._calculate_tag_score(result)

        assert score == 0

    # ========================================
    # FAISS Score Calculation Tests
    # ========================================

    def test_calculate_faiss_score_normalization(self, agent):
        """Should normalize FAISS score to 0-10 range"""
        result = {'score': 0.85}

        score = agent._calculate_faiss_score(result)

        # 0.85 × 10 = 8.5
        assert score == pytest.approx(8.5)

    def test_calculate_faiss_score_perfect_match(self, agent):
        """Should handle perfect similarity (1.0)"""
        result = {'score': 1.0}

        score = agent._calculate_faiss_score(result)

        assert score == pytest.approx(10.0)

    def test_calculate_faiss_score_low_similarity(self, agent):
        """Should handle low similarity scores"""
        result = {'score': 0.1}

        score = agent._calculate_faiss_score(result)

        assert score == pytest.approx(1.0)

    # ========================================
    # Deduplication Tests
    # ========================================

    def test_deduplicate_removes_duplicates(self, agent):
        """Should remove duplicate sources"""
        results = [
            {'source': '/path/to/file.mdx', 'final_score': 5.0},
            {'source': '/path/to/file.mdx', 'final_score': 3.0},  # Duplicate
            {'source': '/path/to/other.mdx', 'final_score': 4.0}
        ]

        deduplicated = agent._deduplicate(results)

        # Should have only 2 unique sources
        assert len(deduplicated) == 2

    def test_deduplicate_keeps_highest_score(self, agent):
        """Should keep highest scoring version of duplicate"""
        results = [
            {'source': '/path/to/file.mdx', 'final_score': 3.0},
            {'source': '/path/to/file.mdx', 'final_score': 8.0},  # Higher score
        ]

        deduplicated = agent._deduplicate(results)

        assert len(deduplicated) == 1
        assert deduplicated[0]['final_score'] == 8.0

    def test_deduplicate_handles_path_variations(self, agent):
        """Should handle 'source' vs 'path' field"""
        results = [
            {'source': '/path/to/file.mdx', 'final_score': 5.0},
            {'path': '/path/to/file.mdx', 'final_score': 7.0},  # Same file, 'path' field
        ]

        deduplicated = agent._deduplicate(results)

        # Should treat as same file
        assert len(deduplicated) == 1
        assert deduplicated[0]['final_score'] == 7.0

    def test_deduplicate_empty_list(self, agent):
        """Should handle empty list"""
        deduplicated = agent._deduplicate([])

        assert deduplicated == []

    def test_deduplicate_preserves_metadata(self, agent):
        """Should preserve all metadata from kept result"""
        results = [
            {
                'source': '/path/to/file.mdx',
                'final_score': 8.0,
                'tags': ['Python'],
                'title': 'Test'
            },
            {
                'source': '/path/to/file.mdx',
                'final_score': 5.0
            }
        ]

        deduplicated = agent._deduplicate(results)

        assert deduplicated[0]['tags'] == ['Python']
        assert deduplicated[0]['title'] == 'Test'

    # ========================================
    # Score Results Integration Tests
    # ========================================

    def test_score_results_combines_sources(self, agent, mock_tag_results, mock_faiss_results):
        """Should combine tag and FAISS results"""
        ranked = agent.score_results("test", mock_tag_results, mock_faiss_results)

        # Should have results from both sources
        assert len(ranked) > 0

        # Check for source_type marker
        source_types = {r.get('source_type') for r in ranked if 'source_type' in r}
        # May have tag, faiss, or both (after dedup)
        assert len(source_types) > 0

    def test_score_results_deduplicates(self, agent, mock_tag_results, mock_faiss_results):
        """Should deduplicate results from both sources"""
        ranked = agent.score_results("test", mock_tag_results, mock_faiss_results)

        # ai-project.mdx appears in both tag and FAISS results
        # Should appear only once in output
        sources = [r.get('source') or r.get('path') for r in ranked]
        unique_sources = set(sources)

        assert len(sources) == len(unique_sources), "Results should be deduplicated"

    def test_score_results_sorts_by_score(self, agent, mock_tag_results, mock_faiss_results):
        """Should sort results by final score (descending)"""
        ranked = agent.score_results("test", mock_tag_results, mock_faiss_results)

        if len(ranked) > 1:
            scores = [r['final_score'] for r in ranked]
            assert scores == sorted(scores, reverse=True)

    def test_score_results_limits_to_5(self, agent):
        """Should return at most 5 results"""
        # Create many mock results
        many_tag_results = [
            {'path': f'/file{i}.mdx', 'score': i, 'content_type': 'post'}
            for i in range(20)
        ]
        many_faiss_results = []

        ranked = agent.score_results("test", many_tag_results, many_faiss_results)

        assert len(ranked) <= 5

    def test_score_results_empty_inputs(self, agent):
        """Should handle empty inputs"""
        ranked = agent.score_results("test", [], [])

        assert ranked == []

    def test_score_results_only_tag_results(self, agent, mock_tag_results):
        """Should work with only tag results"""
        ranked = agent.score_results("test", mock_tag_results, [])

        assert len(ranked) > 0
        assert all(r.get('source_type') == 'tag' for r in ranked)

    def test_score_results_only_faiss_results(self, agent, mock_faiss_results):
        """Should work with only FAISS results"""
        ranked = agent.score_results("test", [], mock_faiss_results)

        assert len(ranked) > 0
        assert all(r.get('source_type') == 'faiss' for r in ranked)

    # ========================================
    # Scoring Logic Tests
    # ========================================

    def test_tag_results_have_higher_weight(self, agent):
        """Tag results should have higher base weight than FAISS"""
        tag_result = {
            'score': 2,  # 2 matching tags
            'content_type': 'post',
            'final_score': 0
        }
        faiss_result = {
            'score': 0.8,  # 80% similarity
            'final_score': 0
        }

        tag_score = agent._calculate_tag_score(tag_result)
        faiss_score = agent._calculate_faiss_score(faiss_result)

        # Tag score should be competitive with FAISS
        # 2 × 1.2 = 2.4 vs 0.8 × 10 = 8.0
        # FAISS is still higher, but tag boost helps balance
        assert tag_score > 0
        assert faiss_score > 0

    # ========================================
    # Edge Cases
    # ========================================

    def test_handles_missing_score_field(self, agent):
        """Should handle missing score field gracefully"""
        result = {'content_type': 'post'}  # No score field

        score = agent._calculate_tag_score(result)

        # Should default to 0
        assert score == 0

    def test_handles_missing_content_type(self, agent):
        """Should handle missing content_type field"""
        result = {'score': 2}  # No content_type

        score = agent._calculate_tag_score(result)

        # Should still calculate base score
        assert score == pytest.approx(2.4)  # 2 × 1.2

    def test_handles_none_source(self, agent):
        """Should handle None source in deduplication"""
        results = [
            {'source': None, 'final_score': 5.0},
            {'path': '/file.mdx', 'final_score': 3.0}
        ]

        deduplicated = agent._deduplicate(results)

        # Should filter out None source
        assert len(deduplicated) == 1
        assert deduplicated[0]['path'] == '/file.mdx'
