"""Content filtering functions for chatbot queries."""
import re

def is_question_about_tc(question: str) -> bool:
    """
    Filter to ensure questions are about TC Heiner and his work experience.
    Prevents abuse of API key for unrelated questions.
    """
    question_lower = question.lower()
    
    # Blocked topics/patterns - only block obviously unrelated content
    blocked_patterns = [
        # Weather, news, general knowledge
        r'\b(weather|news|current events|stock|price|recipe|joke|story)\b',
        # Mathematical/computational requests not about work
        r'\b(calculate|solve)\s+\d+|what is \d+',
        # Code requests without context
        r'write.*code|create.*function|generate.*script(?!.*tc|.*work|.*project)',
    ]
    
    # Check for blocked patterns
    for pattern in blocked_patterns:
        if re.search(pattern, question_lower, re.IGNORECASE):
            return False
    
    # Allowed topics/patterns about TC - be more permissive
    allowed_patterns = [
        # Direct mentions (most important)
        r'\b(tc|heiner|you|your)\b',
        # Basic introduction questions
        r'\b(tell me about|who is|who are you|about you|introduce)\b',
        # Professional topics
        r'\b(experience|work|job|career|project|skill|background|education|resume|cv)\b',
        # Technical topics
        r'\b(development|engineering|coding|programming|software|technical|ai|machine learning|data|architect)\b',
        # Interview/hiring context
        r'\b(hire|hiring|interview|candidate|qualification|position|role)\b',
        # Generic professional questions
        r'\b(what do you do|what is your)\b',
        # Personality and cultural fit topics
        r'\b(personality|character|traits|values|culture|cultural|fit|working style|work style|communication|collaborate|collaboration|team|leadership|manage|management)\b',
        r'\b(motivation|motivated|drive|driven|passion|passionate|interest|interests|approach|philosophy|mindset|attitude)\b',
        r'\b(problem.solving|decision.making|conflict|stress|pressure|challenge|adapt|adaptable|flexible|creativity|creative)\b',
        r'\b(mentor|mentoring|learn|learning|grow|growth|feedback|improve|improvement|strengths|weaknesses|development)\b',
        r'\b(behavior|behavioral|situation|situational|example|tell me about a time|describe a time|how do you|how would you)\b',
    ]
    
    # Must match at least one allowed pattern
    for pattern in allowed_patterns:
        if re.search(pattern, question_lower, re.IGNORECASE):
            return True
    
    return False