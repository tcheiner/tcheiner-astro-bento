"""Confidence scoring for chatbot responses."""

def calculate_confidence_score(sources, question: str) -> tuple[str, str]:
    """Calculate confidence score based on source quality and question specificity."""
    if not sources:
        return "Low", "No relevant sources found"
    
    score = 0
    total_possible = 100
    
    # Source quantity factor (0-30 points)
    num_sources = len(sources)
    if num_sources >= 3:
        score += 30
    elif num_sources == 2:
        score += 20
    elif num_sources == 1:
        score += 10
    
    # Question specificity factor (0-40 points)
    question_lower = question.lower()
    specific_terms = [
        'manaburn', 'myndsens', 'wells fargo', 'stealth', 'chatbot', 'ai',
        'python', 'fastapi', 'aws', 'lambda', 'react', 'astro',
        'project', 'experience', 'skill', 'technology'
    ]
    
    specific_matches = sum(1 for term in specific_terms if term in question_lower)
    if specific_matches >= 3:
        score += 40
    elif specific_matches >= 2:
        score += 25
    elif specific_matches >= 1:
        score += 15
    
    # Source relevance factor (0-30 points) 
    # This is simplified - in practice you'd check similarity scores
    score += min(30, num_sources * 10)
    
    # Determine confidence level and explanation
    if score >= 75:
        level = "High"
        explanation = "Multiple relevant sources with specific question"
    elif score >= 50:
        level = "Medium"  
        explanation = "Some relevant sources found"
    elif score >= 25:
        level = "Low-Medium"
        explanation = "Limited sources or broad question"
    else:
        level = "Low"
        explanation = "Few sources or very general question"
    
    return level, explanation