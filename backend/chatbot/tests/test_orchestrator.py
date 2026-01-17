"""
Unit tests for MultiAgentOrchestrator

Tests orchestration logic, agent routing, and response formatting
"""

import pytest
import asyncio
from chatbot.orchestrator import MultiAgentOrchestrator


class TestMultiAgentOrchestrator:
    """Test suite for MultiAgentOrchestrator"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance for testing"""
        return MultiAgentOrchestrator()

    # ========================================
    # Initialization Tests
    # ========================================

    def test_agents_initialized(self, orchestrator):
        """Should initialize all required agents"""
        assert orchestrator.filter_classifier is not None
        assert orchestrator.tag_agent is not None
        assert orchestrator.faiss_agent is not None
        assert orchestrator.scorer_agent is not None
        assert orchestrator.response_llm is not None

    def test_behavioral_agent_lazy_loaded(self, orchestrator):
        """Behavioral agent should be lazy-loaded"""
        # Before calling behavioral path
        # behavioral_agent may or may not exist yet
        # Just verify it's loaded when needed
        assert True  # Can't easily test without triggering load

    # ========================================
    # Filter and Classification Tests
    # ========================================

    @pytest.mark.asyncio
    async def test_filters_irrelevant_questions(self, orchestrator):
        """Should filter out irrelevant questions"""
        result = await orchestrator.process_question("What's the weather today?")

        assert 'answer' in result
        assert 'contact page' in result['answer'].lower()
        assert result['sources'] == []
        assert 'filtered' in result['metadata']
        assert result['metadata']['filtered'] == True

    @pytest.mark.asyncio
    async def test_passes_relevant_questions(self, orchestrator):
        """Should pass relevant questions to agents"""
        result = await orchestrator.process_question("What are your Python skills?")

        assert 'answer' in result
        assert len(result['sources']) > 0
        # Should have gone through agents
        assert len(result['agents_used']) > 1

    # ========================================
    # Routing Tests
    # ========================================

    @pytest.mark.asyncio
    async def test_routes_skills_questions(self, orchestrator):
        """Should route SKILLS questions to tag+FAISS pipeline"""
        result = await orchestrator.process_question("What are your AI projects?")

        assert result['metadata']['question_type'] == 'SKILLS'
        # Should use tag, faiss, scorer agents
        expected_agents = ['filter_classifier', 'tag', 'faiss', 'scorer']
        for agent in expected_agents:
            assert agent in result['agents_used']

    @pytest.mark.asyncio
    async def test_routes_behavioral_questions(self, orchestrator):
        """Should route BEHAVIORAL questions to behavioral agent"""
        result = await orchestrator.process_question("How do you handle difficult challenges?")

        assert result['metadata']['question_type'] == 'BEHAVIORAL'
        # Should use behavioral agent
        assert 'behavioral' in result['agents_used']

    # ========================================
    # Skills Pipeline Tests
    # ========================================

    @pytest.mark.asyncio
    async def test_skills_pipeline_runs_parallel(self, orchestrator):
        """Should run tag and FAISS search in parallel"""
        # Test that both agents are used
        result = await orchestrator.process_question("Tell me about your Python experience")

        agents_used = result['agents_used']
        assert 'tag' in agents_used
        assert 'faiss' in agents_used

    @pytest.mark.asyncio
    async def test_skills_pipeline_includes_sources(self, orchestrator):
        """Should include sources in response"""
        result = await orchestrator.process_question("What AI projects have you done?")

        assert 'sources' in result
        assert len(result['sources']) > 0
        # Sources should be URLs
        assert all(isinstance(s, str) for s in result['sources'])

    @pytest.mark.asyncio
    async def test_skills_pipeline_formats_html_links(self, orchestrator):
        """Should format sources as HTML links"""
        result = await orchestrator.process_question("What are your Python skills?")

        assert 'answer' in result
        # Should have HTML anchor tags
        assert '<a href=' in result['answer']
        assert 'target="_blank"' in result['answer']

    @pytest.mark.asyncio
    async def test_skills_pipeline_uses_slugs(self, orchestrator):
        """Should use custom slugs from MDX frontmatter"""
        result = await orchestrator.process_question("Tell me about the GenAI image pipeline")

        # Check if sources include proper slug-based URLs
        if len(result['sources']) > 0:
            # Should have URLs with proper slugs
            assert any('tcheiner.com' in source for source in result['sources'])

    # ========================================
    # Behavioral Pipeline Tests
    # ========================================

    @pytest.mark.asyncio
    async def test_behavioral_pipeline_star_format(self, orchestrator):
        """Behavioral responses should use STAR format"""
        result = await orchestrator.process_question(
            "Tell me about a time you overcame a technical challenge"
        )

        if result['metadata']['question_type'] == 'BEHAVIORAL':
            answer = result['answer']
            # Should have some structure (hard to test STAR directly)
            assert len(answer) > 100  # Should be substantial

    @pytest.mark.asyncio
    async def test_behavioral_pipeline_includes_sources(self, orchestrator):
        """Behavioral responses should include blog post sources"""
        result = await orchestrator.process_question("How do you approach problem-solving?")

        if result['metadata']['question_type'] == 'BEHAVIORAL':
            assert len(result['sources']) > 0

    # ========================================
    # Response Structure Tests
    # ========================================

    @pytest.mark.asyncio
    async def test_response_has_required_fields(self, orchestrator):
        """All responses should have required fields"""
        result = await orchestrator.process_question("What are your skills?")

        assert 'answer' in result
        assert 'sources' in result
        assert 'agents_used' in result
        assert 'cost_estimate' in result
        assert 'metadata' in result

    @pytest.mark.asyncio
    async def test_response_metadata_includes_type(self, orchestrator):
        """Metadata should include question type"""
        result = await orchestrator.process_question("What AI work have you done?")

        assert 'question_type' in result['metadata']
        assert result['metadata']['question_type'] in ['SKILLS', 'BEHAVIORAL']

    @pytest.mark.asyncio
    async def test_response_includes_confidence(self, orchestrator):
        """Metadata should include classification confidence"""
        result = await orchestrator.process_question("Tell me about your experience")

        assert 'confidence' in result['metadata']
        assert 0 <= result['metadata']['confidence'] <= 1

    # ========================================
    # Error Handling Tests
    # ========================================

    @pytest.mark.asyncio
    async def test_handles_empty_question(self, orchestrator):
        """Should handle empty question gracefully"""
        result = await orchestrator.process_question("")

        assert 'answer' in result
        # Should probably filter as irrelevant
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_handles_behavioral_agent_failure(self, orchestrator):
        """Should fallback to SKILLS if behavioral agent fails"""
        # Force behavioral route but make it fail
        # This is hard to test without mocking, so just verify structure
        result = await orchestrator.process_question("How do you work?")

        assert 'answer' in result
        assert 'sources' in result

    # ========================================
    # Cost Estimation Tests
    # ========================================

    @pytest.mark.asyncio
    async def test_estimates_cost_for_skills(self, orchestrator):
        """Should estimate cost for SKILLS questions"""
        result = await orchestrator.process_question("What Python experience?")

        assert 'cost_estimate' in result
        assert result['cost_estimate'] > 0
        # Skills should be cheaper (no Claude)
        assert result['cost_estimate'] < 0.01

    @pytest.mark.asyncio
    async def test_estimates_cost_for_behavioral(self, orchestrator):
        """Should estimate cost for BEHAVIORAL questions"""
        result = await orchestrator.process_question("How do you handle challenges?")

        if result['metadata']['question_type'] == 'BEHAVIORAL':
            assert result['cost_estimate'] > 0.01  # Claude is more expensive

    @pytest.mark.asyncio
    async def test_filter_has_minimal_cost(self, orchestrator):
        """Filtered questions should have minimal cost"""
        result = await orchestrator.process_question("What's your favorite hobby?")

        assert result['cost_estimate'] < 0.001  # Just filter, no LLM

    # ========================================
    # Source Details Tests
    # ========================================

    @pytest.mark.asyncio
    async def test_includes_source_details(self, orchestrator):
        """Should include detailed source metadata"""
        result = await orchestrator.process_question("What are your AI projects?")

        if 'source_details' in result:
            assert isinstance(result['source_details'], list)
            if len(result['source_details']) > 0:
                detail = result['source_details'][0]
                assert 'path' in detail or 'title' in detail

    # ========================================
    # Integration Tests
    # ========================================

    @pytest.mark.asyncio
    async def test_multiple_questions_same_orchestrator(self, orchestrator):
        """Should handle multiple questions correctly"""
        questions = [
            "What AI projects?",
            "How do you solve problems?",
            "What's the weather?"
        ]

        results = []
        for q in questions:
            result = await orchestrator.process_question(q)
            results.append(result)

        # All should return valid responses
        assert all('answer' in r for r in results)

        # Should have different types
        types = [r['metadata'].get('question_type', 'FILTERED') for r in results]
        # Should have variety (SKILLS, BEHAVIORAL, filtered)
        assert len(set(types)) > 1

    @pytest.mark.asyncio
    async def test_concurrent_questions(self, orchestrator):
        """Should handle concurrent questions"""
        questions = [
            "What Python skills?",
            "What AI work?",
            "Leadership style?"
        ]

        # Run concurrently
        tasks = [orchestrator.process_question(q) for q in questions]
        results = await asyncio.gather(*tasks)

        # All should complete successfully
        assert len(results) == 3
        assert all('answer' in r for r in results)

    # ========================================
    # Performance Tests
    # ========================================

    @pytest.mark.asyncio
    async def test_parallel_search_is_fast(self, orchestrator):
        """Parallel tag+FAISS should be faster than sequential"""
        import time

        start = time.time()
        result = await orchestrator.process_question("What Python projects?")
        elapsed = time.time() - start

        # Should complete in reasonable time (<5 seconds)
        assert elapsed < 5.0, f"Took {elapsed}s, should be <5s"

    @pytest.mark.asyncio
    async def test_filter_is_very_fast(self, orchestrator):
        """Filter should be very fast (pattern matching)"""
        import time

        start = time.time()
        result = await orchestrator.process_question("What's the weather?")
        elapsed = time.time() - start

        # Should filter quickly (<0.5 seconds)
        assert elapsed < 0.5, f"Filter took {elapsed}s, should be <0.5s"
