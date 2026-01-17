# Multi-Agent Chatbot Architecture - Miro Diagram Specification

**Instructions**: Copy this text into Miro AI and ask it to create a flowchart diagram

---

## System Overview

Create a flowchart showing the multi-agent chatbot architecture with the following components:

### Top Level: User Input
- **Node**: "User Question" (oval, blue)
- Arrow pointing down to Filter+Classifier Agent

---

### Level 1: Filter and Classification

**Agent**: Filter+Classifier Agent (rectangle, yellow)
- **Inputs**: User Question
- **Outputs**:
  - relevant: true/false
  - type: SKILLS | BEHAVIORAL | IRRELEVANT
  - confidence: 0-1

**Decision Diamond** (below agent):
- "Relevant?"
  - NO → "Rejection Message" (rectangle, red) → End
  - YES → "Question Type?" (diamond)

**Second Decision Diamond**:
- "Question Type?"
  - SKILLS → SKILLS Pipeline (right branch)
  - BEHAVIORAL → BEHAVIORAL Pipeline (left branch)

---

### Level 2A: SKILLS Pipeline (Right Branch)

**Parallel Execution** (show side-by-side):

1. **Tag Search Agent** (rectangle, green)
   - Input: Question
   - Process:
     - Extract keywords
     - Expand with synonyms
     - Lookup tag index
   - Output: 10 documents with matching tags

2. **FAISS Agent** (rectangle, green)
   - Input: Question
   - Process:
     - Generate embedding
     - Similarity search
   - Output: 10 documents with scores

**Both arrows converge to:**

**Heuristic Scorer Agent** (rectangle, orange)
- Input: Tag results + FAISS results
- Process:
  - Merge & deduplicate
  - Apply tag boost (1.2x)
  - Apply project boost (1.3x)
- Output: Top 5 ranked documents

**Arrow to:**

**Response Generator** (rectangle, purple)
- Input: Question + Top 5 documents
- Process:
  - GPT-4o-mini generates answer
  - Add inline citations [1], [2]
  - Format source URLs
- Output: Answer with sources

**Arrow to:**

**Final Response** (oval, blue)
- Answer text with citations
- Source URLs with tags
- Cost: ~$0.002/query

---

### Level 2B: BEHAVIORAL Pipeline (Left Branch)

**Behavioral Agent** (large rectangle, teal, containing sub-processes)

**Sub-process 1: Intent Extraction**
- Input: Question
- Process: Map question to relevant tags
  - "failure" → ["failure", "learning", "mistake"]
  - "growth" → ["growth", "learning", "reflection"]
- Output: Intent + relevant tags

**Sub-process 2: Tag-Based Blog Selection**
- Input: Intent + relevant tags
- Process:
  - Search blog posts by tags
  - Apply 3x boost for matching tags
  - Apply recency boost
  - Apply special tags boost (favorite, pride)
- Output: Top 25 relevant blogs

**Sub-process 3: Theme Extraction (Claude Sonnet Pass 1)**
- Input: Question + 15 top blogs
- Process:
  - Extract direct examples
  - Identify patterns over time
  - Analyze values & motivations
  - Find failures & learnings
- Output: Themes JSON

**Sub-process 4: STAR Synthesis (Claude Sonnet Pass 2)**
- Input: Question + Themes + 10 top blogs
- Process:
  - Craft STAR format response
  - Add inline citations [1], [2]
  - Include specific examples
  - Show growth/evolution
- Output: STAR response with sources

**Sub-process 5: Quality Verification (Claude Sonnet Pass 3 - Optional)**
- Input: Question + Response + Themes
- Process:
  - Score directness, specificity, growth, authenticity
  - If any score < 8, improve response
- Output: Verified response
- Note: Only runs for critical questions (growth, leadership, values)

**Arrow to:**

**Final Response** (oval, teal)
- STAR format answer with citations
- Blog post URLs with matching tags
- Cost: $0.015 (2-pass) or $0.022 (3-pass)

---

### Level 3: Source Attribution (Both Pipelines)

**Source Formatter** (rectangle, purple)
- Input: Response + Source documents
- Process:
  - Convert file paths to URLs
  - Format as markdown links
  - Include matching tags
- Output: Complete response with attribution

---

## Visual Styling Guidelines

### Colors:
- **Blue**: Input/Output nodes
- **Yellow**: Filter/Classifier
- **Red**: Rejection path
- **Green**: Tag and FAISS agents (parallel)
- **Orange**: Scoring/ranking
- **Purple**: Response generation
- **Teal**: Behavioral pipeline

### Shapes:
- **Ovals**: Start/end points
- **Rectangles**: Processes/agents
- **Diamonds**: Decision points
- **Rounded rectangles**: Sub-processes

### Arrows:
- **Solid**: Main flow
- **Dashed**: Conditional paths
- **Double arrows**: Parallel execution

### Annotations:
Add cost and performance metrics as small text boxes:
- Filter+Classifier: "$0.0002 | 60% free via patterns"
- Tag Search: "$0.0005 | O(1) lookup"
- FAISS: "$0.00077 | Semantic search"
- Heuristic Scorer: "$0 | No LLM"
- SKILLS Response: "$0.0003 | GPT-4o-mini"
- Behavioral Theme: "$0.007 | Claude Sonnet"
- Behavioral STAR: "$0.008 | Claude Sonnet"
- Behavioral Verify: "$0.007 | Claude Sonnet (optional)"

---

## Key Callout Boxes

Add three callout boxes on the side:

**Box 1: Key Innovations** (top right)
- Tag-based retrieval (100% recall)
- Parallel Tag + FAISS execution
- Heuristic scoring (zero cost)
- Intent-to-tag mapping for behavioral

**Box 2: Accuracy** (middle right)
- SKILLS: 95-98%
- BEHAVIORAL: 95-98%
- Filtering: 90%+

**Box 3: Cost Breakdown** (bottom right)
- SKILLS (80%): $1.60/1000 queries
- BEHAVIORAL (15%): $2.25/1000 queries
- BEHAVIORAL Critical (5%): $1.10/1000 queries
- **Total: $4.95/1000 queries**

---

## Data Stores (Show as cylinders)

**Tag Index** (cylinder, green)
- Built at startup
- 42 unique tags
- O(1) lookup
- Connected to Tag Search Agent

**FAISS Vectorstore** (cylinder, green)
- 2.5MB index
- 79 MDX documents
- Semantic embeddings
- Connected to FAISS Agent

**MDX Content** (cylinder, blue)
- 56 blog posts
- 12 projects
- 6 experiences
- 6,818 lines
- Connected to both Tag Index and FAISS

---

## Example Flow (Show as dotted path overlay)

**Example 1: SKILLS Question**
1. "What are your AI projects?" → Filter+Classifier
2. → Relevant: YES, Type: SKILLS
3. → PARALLEL: Tag Search (finds 3) + FAISS (finds 7)
4. → Heuristic Scorer (merges to top 5)
5. → Response Generator (GPT-4o-mini)
6. → "I have several AI projects... [1], [2], [3]"

**Example 2: BEHAVIORAL Question**
1. "How do you demonstrate growth?" → Filter+Classifier
2. → Relevant: YES, Type: BEHAVIORAL
3. → Behavioral Agent: Intent = "growth"
4. → Tags: ["learning", "growth", "reflection"]
5. → Select 25 blogs (3x boost for matching tags)
6. → Theme extraction (Pass 1)
7. → STAR synthesis (Pass 2)
8. → "I demonstrate growth through... [1], [2], [3]"

---

## Timing Diagram (Optional bottom section)

Show timeline bars:
- SKILLS Pipeline: 0ms → Filter (100ms) → Parallel (800ms) → Score (10ms) → Response (500ms) = **1.4s total**
- BEHAVIORAL Pipeline: 0ms → Filter (100ms) → Select (200ms) → Theme (4s) → STAR (5s) → Verify (3s optional) = **9.3s (critical) or 6.3s (regular)**

---

## Legend

Add a legend box:
- **Yellow boxes** = Classification/routing
- **Green boxes** = Retrieval agents
- **Orange boxes** = Scoring/ranking
- **Purple boxes** = LLM generation
- **Teal boxes** = Multi-pass behavioral analysis
- **Red paths** = Rejection/error
- **Solid arrows** = Main flow
- **Dashed arrows** = Conditional
- **Double arrows** = Parallel execution

---

## Title and Footer

**Title**: "Multi-Agent Chatbot Architecture: Tag-First RAG with Behavioral Analysis"

**Footer**:
- "Cost: $4.95/1000 queries | Accuracy: 95-98% | Latency: 1.4s (SKILLS) / 6.3-9.3s (BEHAVIORAL)"
- "Stack: FastAPI + LangChain + OpenAI + Anthropic + FAISS + MDX Tags"

---

## Alternative: Simplified 3-Level View

If the above is too complex, create a simplified 3-level view:

**Level 1**: User Question → Filter (Relevant?) → Reject or Continue

**Level 2**: Question Type?
- SKILLS → Tag + FAISS (parallel) → Score → GPT Response
- BEHAVIORAL → Tag-based Blog Selection → Claude Multi-Pass → STAR Response

**Level 3**: Both paths merge → Source Attribution → Final Response

---

## Miro Import Command

Copy this entire specification and use Miro's AI feature:

**Prompt for Miro AI**:
"Create a detailed flowchart diagram showing a multi-agent chatbot architecture with the components and flow described below. Use the specified colors, shapes, and annotations. Include callout boxes for key innovations, accuracy, and cost breakdown. Show parallel execution paths and decision diamonds. Add timing diagrams at the bottom."

Then paste this entire document.
