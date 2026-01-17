# File: backend/chatbot/orchestrator.py

import asyncio
import os
from chatbot.filter_classifier_agent import FilterClassifierAgent
from chatbot.tag_search_agent import TagSearchAgent
from chatbot.faiss_agent import FAISSAgent
from chatbot.heuristic_scorer_agent import HeuristicScorerAgent
from chatbot.sources import convert_source_to_url
from langchain_openai import ChatOpenAI

class MultiAgentOrchestrator:
    """
    Main orchestrator for multi-agent chatbot system

    Execution flow:
    1. Filter+Classifier → Check relevance and determine type
    2a. SKILLS path → Tag + FAISS parallel → Heuristic Scorer → Response with sources
    2b. BEHAVIORAL path → Tag-based blog selection → Theme extraction → STAR synthesis → Response with sources
    """

    def __init__(self):
        # Initialize agents
        self.filter_classifier = FilterClassifierAgent()
        self.tag_agent = TagSearchAgent()
        self.faiss_agent = FAISSAgent()
        self.scorer_agent = HeuristicScorerAgent()
        # Behavioral agent will be loaded lazily if needed

        # Response generator for SKILLS questions
        self.response_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.6,
            max_tokens=600
        )

    async def process_question(self, question: str) -> dict:
        """
        Main entry point - orchestrate all agents

        Returns:
            {
                "answer": str (with source links),
                "sources": list (URLs),
                "source_details": list (metadata),
                "agents_used": list,
                "cost_estimate": float,
                "metadata": dict
            }
        """

        # Stage 1: Filter and classify
        classification = self.filter_classifier.analyze(question)

        if not classification['relevant']:
            return {
                "answer": self.filter_classifier.get_rejection_message(),
                "sources": [],
                "agents_used": ["filter_classifier"],
                "cost_estimate": 0.0002,
                "metadata": {
                    "filtered": True,
                    "reason": classification['reason']
                }
            }

        # Stage 2: Route based on type
        if classification['type'] == 'BEHAVIORAL':
            # Behavioral path - import agent only when needed
            try:
                from chatbot.behavioral_agent import HighAccuracyBehavioralAgent
                if not hasattr(self, 'behavioral_agent'):
                    self.behavioral_agent = HighAccuracyBehavioralAgent()

                result = await self._handle_behavioral(question)
                return {
                    "answer": result['answer'],
                    "sources": result['sources'],
                    "source_details": result.get('source_details', []),
                    "agents_used": ["filter_classifier", "behavioral"],
                    "cost_estimate": 0.015,  # or 0.022 if critical
                    "metadata": {
                        "question_type": "BEHAVIORAL",
                        "confidence": classification['confidence']
                    }
                }
            except Exception as e:
                print(f"Error in behavioral pipeline: {e}")
                # Fallback to SKILLS pipeline
                classification['type'] = 'SKILLS'

        # Skills path
        result = await self._handle_skills(question)
        return {
            "answer": result['answer'],
            "sources": result['sources'],
            "source_details": result.get('source_details', []),
            "agents_used": ["filter_classifier", "tag", "faiss", "scorer"],
            "cost_estimate": 0.002,
            "metadata": {
                "question_type": "SKILLS",
                "confidence": classification['confidence']
            }
        }

    async def _handle_behavioral(self, question: str) -> dict:
        """Handle behavioral questions with tag-based blog selection"""
        if hasattr(self, 'behavioral_agent'):
            return self.behavioral_agent.analyze(question)
        else:
            # Fallback if behavioral agent not available
            return await self._handle_skills(question)

    async def _handle_skills(self, question: str) -> dict:
        """
        Handle skills/experience questions

        Parallel execution: Tag + FAISS search
        Then: Ensemble scoring and response generation with sources
        """

        # Execute tag and FAISS search in parallel
        tag_task = asyncio.create_task(
            asyncio.to_thread(self.tag_agent.search, question)
        )
        faiss_task = asyncio.create_task(
            asyncio.to_thread(self.faiss_agent.search, question)
        )

        # Wait for both
        tag_results, faiss_results = await asyncio.gather(tag_task, faiss_task)

        # Score and rank
        ranked_results = self.scorer_agent.score_results(
            question,
            tag_results,
            faiss_results
        )

        # Generate response with sources
        return self._generate_skills_response(question, ranked_results)

    def _generate_skills_response(self, question: str, ranked_results: list) -> dict:
        """
        Generate SKILLS response with inline citations and source links
        """

        # Build context from top results
        context_parts = []
        sources = []

        for i, result in enumerate(ranked_results[:5], 1):
            # Extract content
            if 'content' in result:
                content = result['content']
            else:
                # Tag result without content - use metadata
                tags_display = ', '.join(result.get('tags', []))
                content = f"{result.get('title', 'Unknown')}\nTags: {tags_display}"

            context_parts.append(f"[{i}] {content}")

            # Track source
            # Handle both tag results (slug at top level) and FAISS results (slug in metadata)
            slug = result.get('slug') or result.get('metadata', {}).get('slug', '')

            sources.append({
                'path': result.get('source') or result.get('path'),
                'title': result.get('title', 'Unknown'),
                'slug': slug,
                'tags': result.get('tags', []),
                'matching_tags': result.get('matching_tags', []),
                'content_type': result.get('content_type', '')
            })

        # Generate answer with citations
        prompt = f"""
Answer this technical interview question using the context below.

Question: "{question}"

Context (use inline citations [1], [2], etc.):
{chr(10).join(context_parts)}

Requirements:
- Use specific examples from the context
- Reference sources using [1], [2], etc. inline
- Be concise but comprehensive (3-4 paragraphs)
- Use first person ("I have experience with...")
- Highlight relevant technologies/skills
- Show depth of expertise

Answer:
"""

        response = self.response_llm.invoke(prompt)

        # Format source links
        source_links_parts = ["\n\n**Sources:**"]
        for i, source in enumerate(sources, 1):
            url = convert_source_to_url(source['path'], source['slug'])

            # Generate a better display name from the path
            path = source['path']
            if 'posts/' in path:
                display_name = "Blog Post"
            elif 'projects/' in path:
                # Extract project name from path
                filename = path.split('/')[-1].replace('.mdx', '')
                if 'genai' in filename.lower() or 'image-pipeline' in filename.lower():
                    display_name = "GenAI Image Pipeline"
                elif 'chatbot' in filename.lower():
                    display_name = "AI Chatbot Project"
                else:
                    display_name = filename.replace('-', ' ').title()
            elif 'experiences/' in path:
                filename = path.split('/')[-1].replace('.mdx', '')
                if 'manaburn' in filename.lower():
                    display_name = "ManaBurn Experience"
                elif 'myndsens' in filename.lower():
                    display_name = "Myndsens Experience"
                else:
                    display_name = filename.replace('-', ' ').title()
            else:
                display_name = source.get('title', 'Reference')

            source_links_parts.append(f'[{i}] <a href="{url}" target="_blank">{display_name}</a>')

        source_links = "\n".join(source_links_parts)

        return {
            "answer": f"{response.content}{source_links}",
            "sources": [convert_source_to_url(s['path'], s['slug']) for s in sources],
            "source_details": sources
        }
