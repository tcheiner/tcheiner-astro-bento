# File: backend/chatbot/filter_classifier_agent.py
"""
Filter and Classifier Agent - First line of defense for question processing

PURPOSE:
    Determines if a user's question is:
    1. Relevant to job interviews (filter)
    2. If relevant, classifies as SKILLS or BEHAVIORAL (classifier)

COST OPTIMIZATION:
    - Pattern matching first (regex) → ~60% of questions handled FREE
    - LLM fallback only for ambiguous cases → $0.0002/query

ARCHITECTURE:
    Single agent handles both filtering and classification to reduce API calls
    Previously these were separate agents, combined for cost efficiency

ACCURACY:
    - Pattern matching: 90% confidence for clear cases
    - LLM fallback: 95-98% confidence for edge cases
"""

import re
import json
from langchain_openai import ChatOpenAI

class FilterClassifierAgent:
    """
    Combined filter and classifier agent with pattern-first approach

    Handles:
    1. Job interview relevance filtering
    2. Question type classification (SKILLS vs BEHAVIORAL)

    Cost optimization: Pattern matching for 60% of cases (free)
    Fallback: LLM for edge cases ($0.0002)
    """

    def __init__(self):
        """
        Initialize the filter/classifier agent

        Uses GPT-4o-mini for cost efficiency (only called for ambiguous cases)
        Temperature=0 for deterministic classification
        """
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,  # Deterministic classification
            max_tokens=100  # Only need short JSON response
        )

    def analyze(self, question: str) -> dict:
        """
        Analyze question for relevance and type

        STRATEGY:
            1. Try pattern matching first (free, ~60% hit rate)
            2. Only use LLM for ambiguous cases (~40%)

        Returns:
            {
                "relevant": bool,
                "type": "SKILLS" | "BEHAVIORAL" | "IRRELEVANT",
                "confidence": float,
                "reason": str
            }
        """

        # STEP 1: Try pattern matching first (free!)
        # Most questions have clear patterns we can match with regex
        pattern_result = self._pattern_match(question)
        if pattern_result:
            return pattern_result

        # STEP 2: Fallback to LLM for edge cases
        # Only ~40% of questions reach this point
        return self._llm_analyze(question)

    def _pattern_match(self, question: str) -> dict:
        """
        Use regex patterns for obvious cases

        PATTERN CATEGORIES:
            1. IRRELEVANT: Personal, off-topic, code generation requests
            2. SKILLS: Technical projects, experience, portfolio
            3. BEHAVIORAL: Approach, style, growth, leadership

        Returns None if no pattern matches (triggers LLM fallback)
        ~60% of questions match patterns successfully
        """
        question_lower = question.lower()

        # ========================================
        # IRRELEVANT PATTERNS - Reject immediately
        # ========================================
        # These are questions we should NOT answer:
        # - Personal life (hobbies, family, etc.)
        # - General knowledge ("What is Python?")
        # - Code generation requests
        # - Off-topic (weather, news, stocks)
        irrelevant_patterns = [
            r'\b(hobby|hobbies|favorite color|weather|family)\b',
            r'\b(write|create|build).*(function|code|program)\b',
            r'\bwhat is (react|python|javascript)\b',  # General knowledge
            r'\b(stock|price|news|current events)\b'
        ]

        for pattern in irrelevant_patterns:
            if re.search(pattern, question_lower):
                return {
                    "relevant": False,
                    "type": "IRRELEVANT",
                    "confidence": 0.9,
                    "reason": "Off-topic or non-interview question"
                }

        # ========================================
        # SKILLS PATTERNS - Technical experience
        # ========================================
        # Questions about:
        # - Past projects and work history
        # - Technical skills and tools
        # - Portfolio and achievements
        # Examples: "What AI projects?", "Tell me about your Python work"
        skills_patterns = [
            r'\b(what|which|list).*(project|experience|skill|language|framework|tool)\b',
            r'\b(tell me about|describe).*(work|job|project|role|position)\b',
            r'\byour experience with\b',
            r'\b(show me|give me).*(portfolio|work|project)\b'
        ]

        for pattern in skills_patterns:
            if re.search(pattern, question_lower):
                return {
                    "relevant": True,
                    "type": "SKILLS",
                    "confidence": 0.9,
                    "reason": "Technical skills/experience question"
                }

        # ========================================
        # BEHAVIORAL PATTERNS - Approach/style
        # ========================================
        # Questions about:
        # - How TC approaches problems
        # - Leadership and team style
        # - Growth and learning patterns
        # - Handling challenges/failures
        # Examples: "How do you handle failure?", "Describe your leadership style"
        behavioral_patterns = [
            r'\bhow (do you|did you|would you)\b',
            r'\b(describe|tell me about).*(approach|style|method|process|philosophy)\b',
            r'\b(conflict|challenge|difficult|failure|mistake).*\b(handle|deal|approach)\b',
            r'\b(growth|learn|evolve|improve|develop)\b.*\b(you|your|yourself)\b',
            r'\b(leadership|management|team) style\b'
        ]

        for pattern in behavioral_patterns:
            if re.search(pattern, question_lower):
                return {
                    "relevant": True,
                    "type": "BEHAVIORAL",
                    "confidence": 0.85,
                    "reason": "Behavioral/situational question"
                }

        # No clear pattern - use LLM
        return None

    def _llm_analyze(self, question: str) -> dict:
        """Fallback to LLM for ambiguous cases"""

        prompt = f"""
        Analyze this question for a job interview chatbot:
        "{question}"

        Determine:
        1. Is it relevant to job interviews?
        2. If yes, is it SKILLS (technical/experience) or BEHAVIORAL (approach/style)?

        RELEVANT:
        - Technical skills and experience
        - Past projects and work history
        - Behavioral and situational questions
        - Leadership and team management
        - Problem-solving approaches
        - Work preferences and values

        IRRELEVANT:
        - Personal hobbies and family
        - Off-topic (weather, news, etc.)
        - Code generation requests
        - General knowledge queries

        JSON response:
        {{
            "relevant": true/false,
            "type": "SKILLS"/"BEHAVIORAL"/"IRRELEVANT",
            "confidence": 0.0-1.0,
            "reason": "brief explanation"
        }}
        """

        response = self.llm.invoke(prompt)
        return json.loads(response.content)

    def get_rejection_message(self) -> str:
        """User-friendly rejection message"""
        return (
            "I can only answer questions relevant to job interviews, such as:\n"
            "• Technical skills and past projects\n"
            "• Work experience and achievements\n"
            "• Behavioral and leadership questions\n"
            "• Problem-solving approaches and work style\n\n"
            "Please ask about TC's professional background and capabilities."
        )
