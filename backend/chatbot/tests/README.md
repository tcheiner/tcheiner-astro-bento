# Chatbot Component Tests

Comprehensive unit and integration tests for the multi-agent chatbot system.

## Test Structure

```
backend/chatbot/tests/
├── __init__.py
├── pytest.ini                      # Pytest configuration
├── README.md                       # This file
├── test_filter_classifier.py       # Filter & classification tests
├── test_tag_search_agent.py        # Tag-based retrieval tests
├── test_faiss_agent.py            # Vector search tests
├── test_heuristic_scorer.py       # Result scoring tests
├── test_orchestrator.py           # Multi-agent orchestration tests
├── test_api_endpoints.py          # FastAPI endpoint tests
└── test_sources.py                # Source formatting tests
```

## Running Tests

### Run all tests
```bash
cd backend/chatbot/tests
pytest
```

### Run specific test file
```bash
pytest test_filter_classifier.py
pytest test_orchestrator.py
```

### Run specific test class
```bash
pytest test_filter_classifier.py::TestFilterClassifierAgent
```

### Run specific test
```bash
pytest test_filter_classifier.py::TestFilterClassifierAgent::test_pattern_irrelevant_hobby
```

### Run with verbose output
```bash
pytest -v
```

### Run with output capture disabled (see print statements)
```bash
pytest -s
```

### Run only fast tests (skip slow/integration)
```bash
pytest -m "not slow"
```

### Run with coverage report
```bash
pytest --cov=chatbot --cov-report=html
```

## Test Categories

### Unit Tests (Fast, Isolated)
- `test_filter_classifier.py` - Pattern matching, LLM fallback, classification
- `test_tag_search_agent.py` - Tag indexing, keyword expansion, search
- `test_faiss_agent.py` - Vector search, similarity scoring
- `test_heuristic_scorer.py` - Result scoring, deduplication
- `test_sources.py` - URL conversion, slug handling

### Integration Tests (May require external resources)
- `test_orchestrator.py` - Multi-agent coordination, pipeline execution
- `test_api_endpoints.py` - FastAPI endpoints, request/response handling

## Test Coverage

### Filter/Classifier (test_filter_classifier.py)
- ✅ Pattern matching (free path) - 60% hit rate
- ✅ LLM fallback (paid path) - 40% edge cases
- ✅ SKILLS vs BEHAVIORAL classification
- ✅ Irrelevant question filtering
- ✅ Rejection message format
- ✅ Edge cases (empty, special chars, mixed case)

### Tag Search (test_tag_search_agent.py)
- ✅ Tag index building from MDX files
- ✅ Frontmatter parsing (tags, slug, title)
- ✅ Keyword extraction and expansion
- ✅ Synonym mapping (AI → ML, machine learning)
- ✅ Search result structure and scoring
- ✅ Content type preference (projects > experiences > posts)
- ✅ Performance (O(1) tag lookup)

### FAISS Agent (test_faiss_agent.py)
- ✅ Vectorstore loading
- ✅ Semantic similarity search
- ✅ Score thresholding
- ✅ k parameter (result limiting)
- ✅ Metadata preservation
- ✅ Error handling (missing vectorstore)

### Heuristic Scorer (test_heuristic_scorer.py)
- ✅ Tag result scoring (base + boosts)
- ✅ FAISS result scoring (normalization)
- ✅ Deduplication (by source path)
- ✅ Highest score preference
- ✅ Result ranking (descending score)
- ✅ Content type boosting

### Orchestrator (test_orchestrator.py)
- ✅ Agent initialization
- ✅ Question filtering and routing
- ✅ SKILLS pipeline (tag + FAISS parallel)
- ✅ BEHAVIORAL pipeline (Claude STAR format)
- ✅ Response structure and formatting
- ✅ HTML link generation
- ✅ Slug handling
- ✅ Cost estimation
- ✅ Error handling and fallback
- ✅ Concurrent question handling

### API Endpoints (test_api_endpoints.py)
- ✅ POST /ask endpoint
- ✅ Request/response validation
- ✅ CORS headers
- ✅ User API key support
- ✅ Error handling (missing/invalid input)
- ✅ Multi-agent system integration
- ✅ Performance benchmarks

### Source Formatting (test_sources.py)
- ✅ Path to URL conversion
- ✅ Custom slug handling
- ✅ URL encoding
- ✅ Content type routing
- ✅ HTML link formatting
- ✅ Deduplication
- ✅ Display name generation

## Requirements

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Optional: Coverage reporting
pip install pytest-cov

# Optional: Benchmarking
pip install pytest-benchmark
```

## Environment Setup

Tests require:
- OpenAI API key (set in .env or environment)
- FAISS index built (run `python -c "from chatbot.services import rebuild_vectorstore; rebuild_vectorstore()"`)
- MDX content files in `../../src/content/`

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Chatbot Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements-clean.txt
          pip install pytest pytest-asyncio
      - name: Run tests
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          cd backend/chatbot/tests
          pytest --tb=short
```

## Writing New Tests

### Test Naming Convention
- Files: `test_<component>.py`
- Classes: `Test<ComponentName>`
- Methods: `test_<what_it_tests>`

### Example Test Template
```python
import pytest
from chatbot.my_component import MyComponent

class TestMyComponent:
    """Test suite for MyComponent"""

    @pytest.fixture
    def component(self):
        """Create component instance for testing"""
        return MyComponent()

    def test_basic_functionality(self, component):
        """Should do basic thing correctly"""
        result = component.do_thing("input")

        assert result is not None
        assert result['status'] == 'success'

    @pytest.mark.asyncio
    async def test_async_functionality(self, component):
        """Should handle async operations"""
        result = await component.async_operation()

        assert result['completed'] == True
```

### Best Practices
1. **Isolate tests** - Each test should be independent
2. **Use fixtures** - Share setup code with pytest fixtures
3. **Test edge cases** - Empty input, None, special characters
4. **Mock external calls** - Don't rely on live APIs in unit tests
5. **Clear assertions** - Use descriptive assert messages
6. **Fast tests** - Unit tests should run in milliseconds

## Troubleshooting

### "FAISS index not available" warnings
```bash
# Build FAISS index
cd backend
python -c "from chatbot.services import rebuild_vectorstore; rebuild_vectorstore()"
```

### "OpenAI API key not found" errors
```bash
# Set API key
export OPENAI_API_KEY=sk-your-key-here

# Or add to .env file
echo "OPENAI_API_KEY=sk-your-key-here" >> backend/.env
```

### Import errors
```bash
# Ensure you're in the correct directory
cd backend/chatbot/tests

# Or run from backend directory
cd backend
python -m pytest chatbot/tests/
```

### Async test warnings
```bash
# Install pytest-asyncio
pip install pytest-asyncio
```

## Performance Benchmarks

Expected test execution times:
- **Unit tests**: <100ms each
- **Integration tests**: 1-5 seconds each
- **Full suite**: ~30-60 seconds

If tests are significantly slower, check:
- FAISS index size
- Network latency (API calls)
- Cold start overhead

## Next Steps

After running component tests, run the baseline quality tests:
```bash
cd backend/tests
python test_runner.py
```

See `backend/tests/README.md` for baseline testing documentation.
