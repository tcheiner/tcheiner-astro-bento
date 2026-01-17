"""
Unit tests for FilterClassifierAgent

Tests both pattern-matching (free) and LLM fallback paths
"""

import pytest
from chatbot.filter_classifier_agent import FilterClassifierAgent


class TestFilterClassifierAgent:
    """Test suite for FilterClassifierAgent"""

    @pytest.fixture
    def agent(self):
        """Create agent instance for testing"""
        return FilterClassifierAgent()

    # ========================================
    # Pattern Matching Tests (Free Path)
    # ========================================

    def test_pattern_irrelevant_hobby(self, agent):
        """Should reject hobby questions via pattern matching"""
        result = agent.analyze("What is your favorite hobby?")

        assert result['relevant'] == False
        assert result['type'] == 'IRRELEVANT'
        assert result['confidence'] >= 0.85

    def test_pattern_irrelevant_weather(self, agent):
        """Should reject weather questions via pattern matching"""
        result = agent.analyze("What's the weather today?")

        assert result['relevant'] == False
        assert result['type'] == 'IRRELEVANT'

    def test_pattern_irrelevant_code_generation(self, agent):
        """Should reject code generation requests"""
        result = agent.analyze("Write a function to sort an array")

        assert result['relevant'] == False
        assert result['type'] == 'IRRELEVANT'

    def test_pattern_skills_what_projects(self, agent):
        """Should accept 'what projects' as SKILLS via pattern"""
        result = agent.analyze("What projects have you worked on?")

        assert result['relevant'] == True
        assert result['type'] == 'SKILLS'
        assert result['confidence'] >= 0.85

    def test_pattern_skills_experience_with(self, agent):
        """Should accept 'experience with' as SKILLS via pattern"""
        result = agent.analyze("What's your experience with Python?")

        assert result['relevant'] == True
        assert result['type'] == 'SKILLS'

    def test_pattern_skills_tell_me_about_work(self, agent):
        """Should accept 'tell me about work' as SKILLS via pattern"""
        result = agent.analyze("Tell me about your work at ManaBurn")

        assert result['relevant'] == True
        assert result['type'] == 'SKILLS'

    def test_pattern_behavioral_how_do_you(self, agent):
        """Should accept 'how do you' as BEHAVIORAL via pattern"""
        result = agent.analyze("How do you handle difficult situations?")

        assert result['relevant'] == True
        assert result['type'] == 'BEHAVIORAL'
        assert result['confidence'] >= 0.80

    def test_pattern_behavioral_describe_approach(self, agent):
        """Should accept 'describe approach' as BEHAVIORAL via pattern"""
        result = agent.analyze("Describe your approach to problem-solving")

        assert result['relevant'] == True
        assert result['type'] == 'BEHAVIORAL'

    def test_pattern_behavioral_leadership_style(self, agent):
        """Should accept 'leadership style' as BEHAVIORAL via pattern"""
        result = agent.analyze("What's your leadership style?")

        assert result['relevant'] == True
        assert result['type'] == 'BEHAVIORAL'

    # ========================================
    # Edge Cases
    # ========================================

    def test_empty_question(self, agent):
        """Should handle empty question gracefully"""
        result = agent.analyze("")

        # Should fall back to LLM or reject
        assert 'relevant' in result
        assert 'type' in result

    def test_very_short_question(self, agent):
        """Should handle very short questions"""
        result = agent.analyze("AI?")

        assert 'relevant' in result
        assert 'type' in result

    def test_question_with_special_chars(self, agent):
        """Should handle special characters"""
        result = agent.analyze("What are your Python/JavaScript skills?")

        assert result['relevant'] == True
        assert result['type'] == 'SKILLS'

    def test_mixed_case_question(self, agent):
        """Should handle mixed case (patterns are case-insensitive)"""
        result = agent.analyze("What PROJECTS have you WORKED on?")

        assert result['relevant'] == True
        assert result['type'] == 'SKILLS'

    # ========================================
    # LLM Fallback Tests (Ambiguous Cases)
    # ========================================

    def test_llm_fallback_ambiguous_question(self, agent):
        """Should fall back to LLM for ambiguous questions"""
        # This doesn't match any pattern clearly
        result = agent.analyze("Can you elaborate on TC's capabilities?")

        # LLM should handle this
        assert 'relevant' in result
        assert 'type' in result
        # Confidence may be lower for LLM fallback
        assert 0 <= result['confidence'] <= 1

    def test_llm_fallback_returns_valid_structure(self, agent):
        """LLM fallback should return valid structure"""
        result = agent.analyze("Explain TC's technical background")

        # Check all required fields exist
        assert 'relevant' in result
        assert 'type' in result
        assert 'confidence' in result
        assert 'reason' in result

        # Type should be one of the expected values
        assert result['type'] in ['SKILLS', 'BEHAVIORAL', 'IRRELEVANT']

    # ========================================
    # Rejection Message Tests
    # ========================================

    def test_rejection_message_format(self, agent):
        """Should return proper rejection message"""
        msg = agent.get_rejection_message()

        assert 'contact page' in msg.lower()
        assert '/contact' in msg
        # Should be markdown link format
        assert '[contact page]' in msg

    def test_rejection_message_no_bullet_list(self, agent):
        """Rejection message should NOT have old bullet list format"""
        msg = agent.get_rejection_message()

        # Should not have the old format with multiple bullet points
        assert msg.count('•') == 0 or msg.count('•') <= 1
        assert 'Technical skills' not in msg  # Old format text

    # ========================================
    # Classification Accuracy Tests
    # ========================================

    @pytest.mark.parametrize("question,expected_type", [
        # SKILLS questions
        ("What programming languages do you know?", "SKILLS"),
        ("List your AI projects", "SKILLS"),
        ("Tell me about your AWS experience", "SKILLS"),
        ("What's in your tech stack?", "SKILLS"),

        # BEHAVIORAL questions
        ("How do you approach problem-solving?", "BEHAVIORAL"),
        ("Describe a time you failed", "BEHAVIORAL"),
        ("Tell me about your leadership style", "BEHAVIORAL"),
        ("How do you handle conflicts?", "BEHAVIORAL"),

        # IRRELEVANT questions
        ("What's your favorite color?", "IRRELEVANT"),
        ("Tell me about your family", "IRRELEVANT"),
        ("Write code to reverse a string", "IRRELEVANT"),
        ("What's the weather like?", "IRRELEVANT"),
    ])
    def test_classification_accuracy(self, agent, question, expected_type):
        """Test classification accuracy across question types"""
        result = agent.analyze(question)

        assert result['type'] == expected_type, f"Question '{question}' misclassified as {result['type']}, expected {expected_type}"

    # ========================================
    # Performance Tests
    # ========================================

    def test_pattern_matching_is_fast(self, agent, benchmark):
        """Pattern matching should be sub-millisecond"""
        # Only run if pytest-benchmark is available
        try:
            result = benchmark(agent.analyze, "What are your Python projects?")
            assert result['type'] == 'SKILLS'
        except NameError:
            # pytest-benchmark not installed, skip
            pytest.skip("pytest-benchmark not installed")

    # ========================================
    # Integration Tests
    # ========================================

    def test_multiple_questions_same_agent(self, agent):
        """Should handle multiple questions correctly"""
        questions = [
            "What are your AI projects?",
            "How do you handle failure?",
            "What's your favorite hobby?"
        ]

        results = [agent.analyze(q) for q in questions]

        assert results[0]['type'] == 'SKILLS'
        assert results[1]['type'] == 'BEHAVIORAL'
        assert results[2]['type'] == 'IRRELEVANT'

    def test_result_has_reason_field(self, agent):
        """All results should include reason for transparency"""
        result = agent.analyze("What are your Python skills?")

        assert 'reason' in result
        assert len(result['reason']) > 0
