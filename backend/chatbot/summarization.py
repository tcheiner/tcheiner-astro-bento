"""Response summarization focused on skills and leadership."""
from langchain_openai import ChatOpenAI

def summarize_response(response_text: str, openai_key: str) -> str:
    """Summarize response focusing on skills, critical thinking, and leadership without adding information."""
    try:
        client = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,  # Low temperature to avoid making things up
            max_tokens=200,
            openai_api_key=openai_key
        )
        
        summarization_prompt = f"""Summarize the following response to be more concise, focusing specifically on:
- Hard technical skills (languages, frameworks, tools, technologies)
- Soft skills (communication, collaboration, problem-solving)
- Critical thinking and decision-making examples
- Leadership and mentoring experiences

Keep it to 150-180 tokens. Stay in first person as TC Heiner. Only use information that is explicitly stated - do not add or infer anything not mentioned:

{response_text}

Skills-focused summary:"""
        
        summary = client.invoke([{"role": "user", "content": summarization_prompt}])
        return summary.content.strip()
    except Exception as e:
        print(f"Summarization failed: {e}")
        # Fallback: return original response if summarization fails
        return response_text