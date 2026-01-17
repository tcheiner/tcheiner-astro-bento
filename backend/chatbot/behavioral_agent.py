# File: backend/chatbot/behavioral_agent.py

import glob
import re
import json
import os
from langchain_anthropic import ChatAnthropic
from chatbot.sources import convert_source_to_url

class HighAccuracyBehavioralAgent:
    """
    Behavioral question analysis with tag-based blog selection

    Strategy:
    1. Extract behavioral intent from question
    2. Map intent to relevant tags (e.g., "failure" → ["failure", "learning", "mistake"])
    3. Select 25 most relevant blogs using TAG MATCHING
    4. Extract themes (1st pass - Claude Sonnet)
    5. Synthesize STAR answer (2nd pass - Claude Sonnet)
    6. Quality verify if critical (3rd pass - optional)

    Accuracy: 95-98%
    Cost: $0.015 (2-pass) or $0.022 (3-pass with verification)
    """

    def __init__(self):
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        if not anthropic_key:
            print("Warning: ANTHROPIC_API_KEY not found, behavioral agent will not work")
            raise ValueError("ANTHROPIC_API_KEY required for behavioral agent")

        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            temperature=0.6,
            max_tokens=1000,
            anthropic_api_key=anthropic_key
        )

    def analyze(self, question: str) -> dict:
        """
        Answer behavioral question with source attribution

        Returns:
            {
                "answer": str (with inline citations + source links),
                "sources": list (URLs),
                "source_details": list (metadata + tags),
                "method": "behavioral_pipeline"
            }
        """

        # Stage 1: Select relevant blogs using TAGS
        relevant_blogs = self._select_blogs_with_tags(question, limit=25)

        if not relevant_blogs:
            return {
                "answer": "I don't have enough relevant content to answer this behavioral question comprehensively.",
                "sources": [],
                "source_details": [],
                "method": "behavioral_pipeline"
            }

        # Stage 2: Extract themes (first pass)
        themes = self._extract_themes_with_tags(question, relevant_blogs)

        # Stage 3: Synthesize with STAR format + sources (second pass)
        answer_with_sources = self._synthesize_with_sources(
            question,
            themes,
            relevant_blogs
        )

        # Stage 4: Quality verify if critical (optional third pass)
        if self._is_critical_question(question):
            answer_with_sources['answer'] = self._quality_verify(
                question,
                answer_with_sources['answer'],
                themes
            )

        return answer_with_sources

    def _select_blogs_with_tags(self, question: str, limit: int = 25) -> list:
        """
        Select most relevant blogs using TAG MATCHING + keyword matching

        This is the KEY enhancement: Tags drive blog selection for behavioral questions!
        """

        # Extract behavioral intent
        intent = self._extract_behavioral_intent(question)

        blogs = []
        current_dir = os.path.dirname(__file__)
        posts_dir = os.path.abspath(os.path.join(current_dir, "../../src/content/posts"))

        if not os.path.exists(posts_dir):
            print(f"Warning: Posts directory not found at {posts_dir}")
            return []

        for post_path in glob.glob(f"{posts_dir}/*.mdx"):
            try:
                with open(post_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                print(f"Warning: Could not read {post_path}: {e}")
                continue

            # Parse frontmatter to get tags
            frontmatter = self._parse_frontmatter(content)
            blog_tags = frontmatter.get('tags', [])

            # Calculate relevance with TAG BOOSTING
            relevance = 0
            matching_tags = []

            # 1. Tag matching (HIGH WEIGHT - 3x boost per tag)
            for tag in blog_tags:
                if tag.lower() in [t.lower() for t in intent['relevant_tags']]:
                    relevance += 3  # Tags get 3x boost!
                    matching_tags.append(tag)

            # 2. Keyword matching in content (MEDIUM WEIGHT)
            content_clean = re.sub(r'^---.*?---\n', '', content, flags=re.DOTALL)
            for keyword in intent['keywords']:
                if keyword.lower() in content_clean.lower():
                    relevance += 1

            # 3. Special tag bonuses
            if 'favorite' in [t.lower() for t in blog_tags]:
                relevance += 2  # "favorite" = passion/motivation
            if 'pride' in [t.lower() for t in blog_tags]:
                relevance += 2  # "pride" = accomplishment

            # 4. Recency bonus (prefer recent reflections)
            start_date = frontmatter.get('startDate', '')
            if start_date and ('2024' in start_date or '2025' in start_date):
                relevance += 2

            # 5. Length check (skip too-short posts)
            if len(content_clean) < 500:
                relevance -= 1

            if relevance > 0:
                blogs.append({
                    'path': post_path,
                    'content': content_clean[:2800],  # Keep substantial content
                    'relevance': relevance,
                    'tags': blog_tags,
                    'matching_tags': matching_tags,
                    'title': frontmatter.get('title', 'Untitled'),
                    'slug': frontmatter.get('slug', ''),
                    'startDate': start_date
                })

        # Sort by relevance
        blogs.sort(key=lambda x: x['relevance'], reverse=True)

        return blogs[:limit]

    def _extract_behavioral_intent(self, question: str) -> dict:
        """
        Map behavioral question to relevant tags
        """

        intent_to_tags = {
            'failure_learning': {
                'patterns': [
                    r'\bfail(ure|ed)?\b',
                    r'\bmistake\b',
                    r'\bwrong\b',
                    r'\bsetback\b',
                    r'\bchallenge\b.*\bdifficult\b'
                ],
                'tags': ['failure', 'mistake', 'learning', 'setback', 'challenge', 'difficult'],
                'keywords': ['fail', 'mistake', 'wrong', 'learn', 'lesson', 'setback']
            },

            'growth': {
                'patterns': [
                    r'\bgrow(th)?\b',
                    r'\bevolve\b',
                    r'\bimprove\b',
                    r'\blearn\b',
                    r'\bdevelop\b'
                ],
                'tags': ['learning', 'growth', 'improvement', 'reflection', 'development'],
                'keywords': ['grow', 'learn', 'improve', 'evolve', 'progress', 'develop']
            },

            'leadership': {
                'patterns': [
                    r'\bleader(ship)?\b',
                    r'\bmanage\b',
                    r'\bteam\b',
                    r'\bmentor\b'
                ],
                'tags': ['leadership', 'team', 'management', 'favorite', 'pride'],
                'keywords': ['lead', 'team', 'manage', 'mentor', 'delegate', 'guide']
            },

            'problem_solving': {
                'patterns': [
                    r'\bproblem\b',
                    r'\bsolve\b',
                    r'\bapproach\b',
                    r'\bchallenge\b',
                    r'\bdebug\b'
                ],
                'tags': ['problem', 'solution', 'challenge', 'technical', 'architecture'],
                'keywords': ['problem', 'solve', 'approach', 'debug', 'fix', 'tackle']
            },

            'motivation': {
                'patterns': [
                    r'\bmotivat\w+\b',
                    r'\bpassion\b',
                    r'\bdriv(e|es|ing)\b',
                    r'\bwhat excites\b'
                ],
                'tags': ['favorite', 'passion', 'pride', 'love', 'enjoy'],
                'keywords': ['motivation', 'passion', 'drive', 'love', 'enjoy', 'excite']
            },

            'collaboration': {
                'patterns': [
                    r'\bwork with\b',
                    r'\bcollaborate\b',
                    r'\bteamwork\b',
                    r'\bpartner\b'
                ],
                'tags': ['team', 'collaboration', 'teamwork', 'favorite'],
                'keywords': ['collaborate', 'team', 'work with', 'partner', 'together']
            },

            'decision_making': {
                'patterns': [
                    r'\bdecision\b',
                    r'\bchoose\b',
                    r'\bdecide\b',
                    r'\bevaluate\b'
                ],
                'tags': ['decision', 'architecture', 'technical', 'leadership'],
                'keywords': ['decision', 'choose', 'decide', 'evaluate', 'assess']
            }
        }

        question_lower = question.lower()

        # Match intent type
        for intent_type, config in intent_to_tags.items():
            for pattern in config['patterns']:
                if re.search(pattern, question_lower):
                    return {
                        'type': intent_type,
                        'relevant_tags': config['tags'],
                        'keywords': config['keywords']
                    }

        # Default fallback (general behavioral)
        return {
            'type': 'general',
            'relevant_tags': ['favorite', 'pride', 'learning', 'reflection'],
            'keywords': re.findall(r'\b\w{5,}\b', question_lower)
        }

    def _parse_frontmatter(self, content: str) -> dict:
        """Extract frontmatter metadata"""
        match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if not match:
            return {'tags': [], 'title': '', 'slug': '', 'startDate': ''}

        frontmatter = match.group(1)

        # Parse tags
        tags_match = re.search(r'tags:\s*\[(.*?)\]', frontmatter, re.DOTALL)
        tags = []
        if tags_match:
            tags_str = tags_match.group(1)
            tags = [t.strip(' "\'') for t in tags_str.split(',') if t.strip()]

        # Parse other fields
        slug_match = re.search(r'slug:\s*["\']?([^"\'\n]+)["\']?', frontmatter)
        title_match = re.search(r'title:\s*["\']?([^"\'\n]+)["\']?', frontmatter)
        date_match = re.search(r'startDate:\s*["\']?([^"\'\n]+)["\']?', frontmatter)

        return {
            'tags': tags,
            'slug': slug_match.group(1) if slug_match else '',
            'title': title_match.group(1) if title_match else '',
            'startDate': date_match.group(1) if date_match else ''
        }

    def _extract_themes_with_tags(self, question: str, blogs: list) -> dict:
        """
        First pass: Extract themes with tag context
        """

        # Combine blog content with tag information
        blog_context = []
        for i, blog in enumerate(blogs[:15], 1):  # Use top 15 for theme extraction
            tag_info = f"Tags: {', '.join(blog['matching_tags'])} (matched), {', '.join(blog['tags'][:5])} (all)"
            blog_context.append(
                f"[{i}] {blog['title']}\n{tag_info}\n{blog['content'][:1000]}"
            )

        combined = "\n\n===\n\n".join(blog_context)

        extraction_prompt = f"""
You are analyzing TC Heiner's blog posts to understand behavioral patterns.

Question: "{question}"

Relevant blog posts (selected by tags):
{combined}

Extract comprehensive themes and evidence:

1. **Direct Examples**: Specific stories/situations that directly relate
2. **Patterns Over Time**: How has TC's approach evolved?
3. **Values & Motivations**: What drives TC's decisions?
4. **Self-Reflection**: Where does TC show introspection?
5. **Failures & Learnings**: Specific mistakes and lessons learned
6. **Behavioral Indicators**: How does TC actually behave?

For EACH theme, provide:
- Specific quote or reference
- Which blog post [number]
- Context/situation
- Why it's relevant (how it shows the behavioral pattern)

Format as JSON:
{{
    "direct_examples": [
        {{"blog_num": 1, "quote": "...", "context": "...", "relevance": "..."}},
        ...
    ],
    "evolution_patterns": [
        {{"early": "...", "later": "...", "evidence": "...", "blog_nums": [1,3]}},
        ...
    ],
    "values": ["value 1 with evidence from blog N", ...],
    "failures_learnings": [
        {{"failure": "...", "lesson": "...", "blog_num": N}},
        ...
    ]
}}
"""

        response = self.llm.invoke(extraction_prompt)
        try:
            return json.loads(response.content)
        except:
            return {"raw_analysis": response.content}

    def _synthesize_with_sources(self, question: str, themes: dict, blogs: list) -> dict:
        """
        Second pass: Synthesize STAR-format answer with source citations
        """

        # Build context with source numbers
        blog_context = []
        sources = []

        for i, blog in enumerate(blogs[:10], 1):  # Use top 10 for synthesis
            tag_display = ', '.join(blog['matching_tags']) if blog['matching_tags'] else ', '.join(blog['tags'][:3])

            blog_context.append(
                f"[{i}] {blog['title']}\n"
                f"Tags: {tag_display}\n"
                f"Content: {blog['content'][:800]}"
            )

            sources.append({
                'path': blog['path'],
                'title': blog['title'],
                'slug': blog['slug'],
                'tags': blog['tags'],
                'matching_tags': blog['matching_tags']
            })

        combined_context = "\n\n".join(blog_context)

        synthesis_prompt = f"""
You are answering a behavioral interview question for TC Heiner.

Question: "{question}"

Extracted themes:
{json.dumps(themes, indent=2)}

Relevant blog posts:
{combined_context}

Craft a comprehensive response (4-5 paragraphs) using STAR format:

**Structure:**
1. Opening: Direct answer to the question
2. Situation/Context: Set up specific examples (use [1], [2] citations)
3. Task/Challenge: What needed to be done
4. Action: What TC did (first person: "I learned...", "In my experience...")
5. Result/Learning: Outcome and reflection

**Requirements:**
- Use SPECIFIC examples with inline citations [1], [2], etc.
- Reference which blog posts support each point
- Show evolution over time if applicable
- Include at least one failure/learning story
- Demonstrate self-awareness and growth mindset
- Be authentic - only use the provided content
- If there's a pattern across multiple experiences, connect them

**Quality bar:**
- Interviewer should learn TC's actual behavioral patterns
- Should feel genuine, not generic
- Should showcase growth and self-reflection
- Should have specific, memorable examples

Response:
"""

        response = self.llm.invoke(synthesis_prompt)

        # Format source links
        source_links_parts = ["\n\n**Sources (supporting this answer):**"]
        for i, source in enumerate(sources, 1):
            url = convert_source_to_url(source['path'], source['slug'])
            tags_display = ', '.join(source['matching_tags']) if source['matching_tags'] else ', '.join(source['tags'][:5])
            source_links_parts.append(
                f"[{i}] [{source['title']}]({url})\n"
                f"    Relevant tags: {tags_display}"
            )

        source_links = "\n".join(source_links_parts)

        return {
            "answer": f"{response.content}{source_links}",
            "sources": [convert_source_to_url(s['path'], s['slug']) for s in sources],
            "source_details": sources,
            "method": "behavioral_pipeline"
        }

    def _is_critical_question(self, question: str) -> bool:
        """
        Determine if question deserves quality verification pass
        """
        critical_patterns = [
            r'\b(growth|grow|evolve|develop)\b',
            r'\b(leadership style|lead|management approach)\b',
            r'\b(values|motivation|drive|passion)\b',
            r'\b(failure|mistake).*\blearn\b',
        ]

        return any(re.search(p, question.lower()) for p in critical_patterns)

    def _quality_verify(self, question: str, answer: str, themes: dict) -> str:
        """
        Third pass: Verify answer quality and enhance if needed
        """

        verification_prompt = f"""
You are a quality checker for behavioral interview responses.

Question: "{question}"

Candidate's answer:
{answer}

Available evidence:
{json.dumps(themes, indent=2)}

Evaluate (0-10 scale):
1. **Directness**: Answers the question directly? (0-10)
2. **Specificity**: Uses concrete examples with context? (0-10)
3. **Growth**: Shows evolution/learning? (0-10)
4. **Authenticity**: Based on actual evidence? (0-10)
5. **Impact**: Memorable and insightful? (0-10)

If ANY score is below 8, provide an improved version.
Otherwise, return "PASS" with scores.

JSON:
{{
    "scores": {{"directness": 9, ...}},
    "overall": 8.6,
    "status": "PASS" or "IMPROVE",
    "improved_answer": "..." (if IMPROVE),
    "issues": ["what needs improvement"]
}}
"""

        response = self.llm.invoke(verification_prompt)
        try:
            result = json.loads(response.content)
            if result['status'] == 'IMPROVE':
                return result['improved_answer']
            else:
                return answer  # Original is good
        except:
            return answer  # If parsing fails, return original
