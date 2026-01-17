# File: backend/chatbot/tag_search_agent.py
"""
Tag Search Agent - Fast O(1) retrieval using MDX frontmatter tags

PURPOSE:
    Provides deterministic tag-based search as complement to semantic FAISS search
    Tags are explicit categorization - if someone asks about "AI", we want ALL
    AI-tagged content, not just semantically similar chunks

COST:
    $0.0005/query (keyword expansion with synonyms only)
    Tag lookup itself is free (dictionary lookup)

KEY INNOVATION:
    Tag index is built once at startup from MDX frontmatter
    Search is O(1) dictionary lookup by tag name
    Results include "matching_tags" for source attribution

ARCHITECTURE:
    1. Build tag index at init (tag → [documents])
    2. Extract keywords from question
    3. Expand keywords with synonyms ("ai" → ["ai", "ml", "machine learning"])
    4. Lookup matching documents by tag
    5. Return ranked results with matching tags

EXAMPLE:
    Question: "What are your AI projects?"
    → Keywords: ["ai", "projects"]
    → Expanded: ["ai", "ml", "machine learning", "chatbot", ...]
    → Tag lookup: tag_index["ai"] + tag_index["ml"] + ...
    → Result: All AI-tagged projects with matching tags highlighted
"""

import glob
import re
import os
from typing import List, Dict

class TagSearchAgent:
    """
    Search MDX files using frontmatter tags

    Strategy:
    1. Extract keywords from question
    2. Expand keywords to synonyms/related terms
    3. Search tag index for matches
    4. Return ranked results with matching tags
    """

    def __init__(self):
        self.tag_index = self._build_tag_index()
        self.synonym_map = self._load_synonyms()

    def _build_tag_index(self) -> Dict[str, List[dict]]:
        """
        Build searchable tag index from all MDX files

        INDEX STRUCTURE:
            {
                "ai": [doc1, doc2, ...],       # All docs tagged "ai"
                "python": [doc3, doc4, ...],   # All docs tagged "python"
                ...
            }

        PERFORMANCE:
            - Built once at agent initialization
            - O(n) build time where n = number of MDX files
            - O(1) lookup time during queries

        Returns:
            Dictionary mapping tag names to lists of documents
        """
        tag_index = {}

        # Get absolute path to content directory
        # Assumes structure: backend/chatbot/ → ../../src/content/
        current_dir = os.path.dirname(__file__)
        content_dir = os.path.abspath(os.path.join(current_dir, "../../src/content"))

        if not os.path.exists(content_dir):
            print(f"Warning: Content directory not found at {content_dir}")
            return tag_index

        # Find all MDX files recursively (posts, projects, experiences)
        mdx_files = glob.glob(f"{content_dir}/**/*.mdx", recursive=True)
        print(f"TagSearchAgent: Indexing {len(mdx_files)} MDX files")

        for mdx_path in mdx_files:
            # Parse frontmatter to extract tags and metadata
            metadata = self._parse_frontmatter(mdx_path)

            # Index by each tag (one doc can be under multiple tags)
            for tag in metadata['tags']:
                tag_lower = tag.lower()  # Case-insensitive matching
                if tag_lower not in tag_index:
                    tag_index[tag_lower] = []
                tag_index[tag_lower].append(metadata)

        print(f"TagSearchAgent: Built index with {len(tag_index)} unique tags")
        return tag_index

    def _parse_frontmatter(self, mdx_path: str) -> dict:
        """Extract frontmatter metadata from MDX file"""
        try:
            with open(mdx_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Warning: Could not read {mdx_path}: {e}")
            return {'path': mdx_path, 'tags': [], 'title': '', 'slug': ''}

        # Match YAML frontmatter
        match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if not match:
            return {'path': mdx_path, 'tags': [], 'title': '', 'slug': ''}

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

        # Determine content type
        if '/projects/' in mdx_path:
            content_type = 'project'
        elif '/experiences/' in mdx_path:
            content_type = 'experience'
        elif '/posts/' in mdx_path:
            content_type = 'post'
        else:
            content_type = 'other'

        return {
            'path': mdx_path,
            'tags': tags,
            'slug': slug_match.group(1) if slug_match else '',
            'title': title_match.group(1) if title_match else '',
            'content_type': content_type
        }

    def _load_synonyms(self) -> dict:
        """
        Map keywords to related tags

        Example:
        "ai" → ["ai", "machine learning", "ml", "chatbot", "openai", "llm"]
        """
        return {
            # AI/ML
            "ai": ["ai", "artificial intelligence", "machine learning", "ml", "deep learning"],
            "chatbot": ["chatbot", "conversational ai", "chat", "bot"],
            "nlp": ["nlp", "natural language processing", "language model", "llm"],
            "computer vision": ["computer vision", "cv", "image recognition"],
            "generative ai": ["generative ai", "gen ai", "stable diffusion", "diffusion"],

            # Languages
            "python": ["python", "py", "fastapi", "django", "flask"],
            "javascript": ["javascript", "js", "typescript", "ts", "node", "react"],
            "go": ["go", "golang"],

            # Cloud
            "cloud": ["cloud", "aws", "serverless", "lambda"],
            "aws": ["aws", "amazon web services", "ec2", "s3", "lambda"],
            "devops": ["devops", "ci/cd", "docker", "kubernetes", "k8s"],

            # Databases
            "database": ["database", "sql", "nosql", "postgres", "redis"],

            # Concepts
            "rag": ["rag", "retrieval augmented generation", "vectorstore", "faiss"],
            "api": ["api", "rest", "graphql", "api gateway"],
        }

    def search(self, question: str, limit: int = 10) -> List[dict]:
        """
        Search tags for relevant documents

        Returns:
            [
                {
                    "path": str,
                    "title": str,
                    "tags": list,
                    "matching_tags": list,  # Which tags matched
                    "score": float,
                    "content_type": str,
                    "slug": str
                },
                ...
            ]
        """

        # Extract and expand keywords
        keywords = self._extract_keywords(question)
        expanded = self._expand_keywords(keywords)

        # Search tag index
        matches = {}  # path -> match data

        for keyword in expanded:
            keyword_lower = keyword.lower()
            if keyword_lower in self.tag_index:
                for doc in self.tag_index[keyword_lower]:
                    path = doc['path']
                    if path not in matches:
                        matches[path] = {
                            'metadata': doc,
                            'matching_tags': [],
                            'score': 0
                        }

                    matches[path]['matching_tags'].append(keyword_lower)
                    matches[path]['score'] += 1

        # Convert to list and add metadata
        results = []
        for path, match_data in matches.items():
            results.append({
                'path': path,
                'title': match_data['metadata']['title'],
                'tags': match_data['metadata']['tags'],
                'matching_tags': match_data['matching_tags'],
                'score': match_data['score'],
                'content_type': match_data['metadata']['content_type'],
                'slug': match_data['metadata']['slug'],
                'source': 'tag_search'
            })

        # Sort by score, then by content type preference
        def sort_key(r):
            type_weight = {'project': 3, 'experience': 2, 'post': 1, 'other': 0}
            return (r['score'], type_weight.get(r['content_type'], 0))

        results.sort(key=sort_key, reverse=True)

        return results[:limit]

    def _extract_keywords(self, question: str) -> List[str]:
        """Extract meaningful keywords from question"""
        # Remove stop words and extract 4+ char words
        words = re.findall(r'\b\w{4,}\b', question.lower())

        # Filter common stop words
        stop_words = {'what', 'your', 'tell', 'about', 'have', 'does', 'this', 'that', 'with'}
        keywords = [w for w in words if w not in stop_words]

        return keywords

    def _expand_keywords(self, keywords: List[str]) -> List[str]:
        """Expand keywords using synonym map"""
        expanded = set(keywords)

        for keyword in keywords:
            # Check if keyword matches any synonym group
            for base_term, synonyms in self.synonym_map.items():
                if keyword in synonyms or keyword == base_term:
                    expanded.update(synonyms)

        return list(expanded)
