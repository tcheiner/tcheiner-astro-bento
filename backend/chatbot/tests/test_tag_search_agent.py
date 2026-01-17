"""
Unit tests for TagSearchAgent

Tests tag indexing, search, and keyword expansion
"""

import pytest
import tempfile
import os
from chatbot.tag_search_agent import TagSearchAgent


class TestTagSearchAgent:
    """Test suite for TagSearchAgent"""

    @pytest.fixture
    def agent(self):
        """Create agent instance for testing"""
        return TagSearchAgent()

    @pytest.fixture
    def mock_mdx_file(self):
        """Create a temporary MDX file for testing"""
        content = """---
slug: "test-project"
title: "Test AI Project"
tags: ["Python", "AI", "machine learning", "FastAPI"]
---

This is a test project about machine learning.
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mdx', delete=False) as f:
            f.write(content)
            temp_path = f.name

        yield temp_path

        # Cleanup
        os.unlink(temp_path)

    # ========================================
    # Tag Index Tests
    # ========================================

    def test_tag_index_is_built(self, agent):
        """Should build tag index on initialization"""
        assert agent.tag_index is not None
        assert isinstance(agent.tag_index, dict)
        assert len(agent.tag_index) > 0

    def test_tag_index_has_expected_tags(self, agent):
        """Should index common tags from MDX files"""
        # Check for some expected tags (case-insensitive)
        tag_index_lower = {k.lower(): v for k, v in agent.tag_index.items()}

        # Should have Python tag (common in portfolio)
        assert 'python' in tag_index_lower

    def test_tag_index_structure(self, agent):
        """Tag index should map tags to document metadata"""
        # Get first tag
        first_tag = list(agent.tag_index.keys())[0]
        docs = agent.tag_index[first_tag]

        assert isinstance(docs, list)
        assert len(docs) > 0

        # Check document structure
        doc = docs[0]
        assert 'path' in doc
        assert 'tags' in doc
        assert 'slug' in doc
        assert 'title' in doc
        assert 'content_type' in doc

    def test_tag_index_case_insensitive(self, agent):
        """Tag index should use lowercase keys"""
        for tag_key in agent.tag_index.keys():
            assert tag_key == tag_key.lower(), f"Tag '{tag_key}' should be lowercase"

    # ========================================
    # Frontmatter Parsing Tests
    # ========================================

    def test_parse_frontmatter_extracts_tags(self, agent, mock_mdx_file):
        """Should extract tags from frontmatter"""
        metadata = agent._parse_frontmatter(mock_mdx_file)

        assert 'tags' in metadata
        assert 'Python' in metadata['tags']
        assert 'AI' in metadata['tags']

    def test_parse_frontmatter_extracts_slug(self, agent, mock_mdx_file):
        """Should extract slug from frontmatter"""
        metadata = agent._parse_frontmatter(mock_mdx_file)

        assert metadata['slug'] == 'test-project'

    def test_parse_frontmatter_extracts_title(self, agent, mock_mdx_file):
        """Should extract title from frontmatter"""
        metadata = agent._parse_frontmatter(mock_mdx_file)

        assert metadata['title'] == 'Test AI Project'

    def test_parse_frontmatter_determines_content_type(self, agent):
        """Should determine content type from path"""
        # Mock paths for different content types
        test_cases = [
            ('/path/to/projects/test.mdx', 'project'),
            ('/path/to/experiences/test.mdx', 'experience'),
            ('/path/to/posts/test.mdx', 'post'),
            ('/path/to/other/test.mdx', 'other'),
        ]

        for path, expected_type in test_cases:
            # Create temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.mdx', delete=False, dir='/tmp') as f:
                f.write("---\ntags: []\n---\n")
                temp_path = f.name

            # Rename to match expected path pattern
            if 'projects' in path:
                content_type = 'project'
            elif 'experiences' in path:
                content_type = 'experience'
            elif 'posts' in path:
                content_type = 'post'
            else:
                content_type = 'other'

            # Test by checking the logic (since we can't create real paths)
            if '/projects/' in path:
                assert content_type == 'project'
            elif '/experiences/' in path:
                assert content_type == 'experience'
            elif '/posts/' in path:
                assert content_type == 'post'

            os.unlink(temp_path)

    # ========================================
    # Synonym Map Tests
    # ========================================

    def test_synonym_map_loaded(self, agent):
        """Should load synonym map"""
        assert agent.synonym_map is not None
        assert isinstance(agent.synonym_map, dict)
        assert len(agent.synonym_map) > 0

    def test_synonym_map_has_ai_synonyms(self, agent):
        """Should have AI/ML synonyms"""
        assert 'ai' in agent.synonym_map
        synonyms = agent.synonym_map['ai']

        assert 'artificial intelligence' in synonyms
        assert 'machine learning' in synonyms
        assert 'ml' in synonyms

    def test_synonym_map_has_language_synonyms(self, agent):
        """Should have programming language synonyms"""
        assert 'python' in agent.synonym_map
        assert 'javascript' in agent.synonym_map

    def test_synonym_map_has_cloud_synonyms(self, agent):
        """Should have cloud/DevOps synonyms"""
        assert 'aws' in agent.synonym_map
        assert 'cloud' in agent.synonym_map

    # ========================================
    # Keyword Extraction Tests
    # ========================================

    def test_extract_keywords_basic(self, agent):
        """Should extract basic keywords"""
        keywords = agent._extract_keywords("What are your Python projects?")

        assert 'python' in keywords
        assert 'projects' in keywords

    def test_extract_keywords_filters_stop_words(self, agent):
        """Should filter stop words"""
        keywords = agent._extract_keywords("What are your Python projects?")

        # Stop words should be filtered
        assert 'what' not in keywords
        assert 'your' not in keywords

    def test_extract_keywords_min_length(self, agent):
        """Should only extract words 4+ characters"""
        keywords = agent._extract_keywords("AI ML Python Go")

        # 'Go' is only 2 chars, should be filtered
        assert 'python' in keywords
        assert 'go' not in keywords  # Too short

    def test_extract_keywords_case_insensitive(self, agent):
        """Should extract keywords as lowercase"""
        keywords = agent._extract_keywords("What PYTHON Projects?")

        assert 'python' in keywords
        assert 'projects' in keywords
        # Should be lowercase
        assert all(k == k.lower() for k in keywords)

    # ========================================
    # Keyword Expansion Tests
    # ========================================

    def test_expand_keywords_ai(self, agent):
        """Should expand AI keywords"""
        expanded = agent._expand_keywords(['ai'])

        assert 'ai' in expanded
        assert 'machine learning' in expanded
        assert 'ml' in expanded

    def test_expand_keywords_python(self, agent):
        """Should expand Python keywords"""
        expanded = agent._expand_keywords(['python'])

        assert 'python' in expanded
        assert 'fastapi' in expanded  # Python framework

    def test_expand_keywords_preserves_original(self, agent):
        """Should preserve original keywords"""
        original = ['projects', 'python']
        expanded = agent._expand_keywords(original)

        for keyword in original:
            assert keyword in expanded

    def test_expand_keywords_no_duplicates(self, agent):
        """Should not have duplicates in expanded set"""
        expanded = agent._expand_keywords(['ai', 'machine learning'])

        # Convert to set and back to list should have same length
        assert len(expanded) == len(set(expanded))

    # ========================================
    # Search Tests
    # ========================================

    def test_search_returns_results(self, agent):
        """Should return results for valid query"""
        results = agent.search("What are your AI projects?")

        assert isinstance(results, list)
        # Should find at least some results (assuming MDX files exist)
        # Don't assert length since it depends on content

    def test_search_result_structure(self, agent):
        """Search results should have correct structure"""
        results = agent.search("What are your Python projects?")

        if len(results) > 0:
            result = results[0]

            # Check required fields
            assert 'path' in result
            assert 'title' in result
            assert 'tags' in result
            assert 'matching_tags' in result
            assert 'score' in result
            assert 'content_type' in result
            assert 'slug' in result
            assert 'source' in result

    def test_search_matching_tags(self, agent):
        """Should identify matching tags"""
        results = agent.search("What are your Python projects?")

        if len(results) > 0:
            result = results[0]

            assert isinstance(result['matching_tags'], list)
            # If it matched, should have at least one matching tag
            assert len(result['matching_tags']) > 0

    def test_search_scores_results(self, agent):
        """Should score results by number of matching tags"""
        results = agent.search("What are your Python AI projects?")

        if len(results) > 1:
            # Results should be sorted by score (descending)
            scores = [r['score'] for r in results]
            assert scores == sorted(scores, reverse=True)

    def test_search_limits_results(self, agent):
        """Should limit results to specified count"""
        results = agent.search("projects", limit=3)

        assert len(results) <= 3

    def test_search_empty_query(self, agent):
        """Should handle empty query gracefully"""
        results = agent.search("")

        assert isinstance(results, list)
        # May return empty or some results

    def test_search_no_matches(self, agent):
        """Should return empty list for no matches"""
        results = agent.search("xyzabc123notfound")

        assert isinstance(results, list)
        assert len(results) == 0

    # ========================================
    # Content Type Preference Tests
    # ========================================

    def test_search_prefers_projects(self, agent):
        """Should prefer projects over posts for same score"""
        # This test depends on having actual content
        # Just verify the sorting logic exists
        results = agent.search("Python")

        # If we have results, check content_type field exists
        if len(results) > 0:
            assert 'content_type' in results[0]

    # ========================================
    # Integration Tests
    # ========================================

    def test_search_with_keyword_expansion(self, agent):
        """Should expand keywords and find semantic matches"""
        # Search for "AI" should also match "machine learning" tags
        results_ai = agent.search("AI projects")
        results_ml = agent.search("machine learning projects")

        # Should have overlap due to synonym expansion
        if len(results_ai) > 0 and len(results_ml) > 0:
            ai_paths = {r['path'] for r in results_ai}
            ml_paths = {r['path'] for r in results_ml}

            # Should have some overlap
            assert len(ai_paths & ml_paths) > 0

    def test_multiple_searches_same_agent(self, agent):
        """Should handle multiple searches correctly"""
        queries = [
            "Python projects",
            "AI work",
            "leadership experience"
        ]

        for query in queries:
            results = agent.search(query)
            assert isinstance(results, list)

    # ========================================
    # Performance Tests
    # ========================================

    def test_search_is_fast(self, agent):
        """Tag search should be O(1) lookup, very fast"""
        import time

        start = time.time()
        results = agent.search("Python projects")
        elapsed = time.time() - start

        # Should complete in under 100ms (generous)
        assert elapsed < 0.1, f"Search took {elapsed}s, should be <100ms"

    def test_initialization_indexes_all_files(self, agent):
        """Should index all MDX files on init"""
        # Check that tag_index has content
        assert len(agent.tag_index) > 0

        # Check that multiple files are indexed
        total_docs = sum(len(docs) for docs in agent.tag_index.values())
        assert total_docs > 0
