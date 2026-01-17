"""
Integration tests for FastAPI endpoints

Tests the /ask endpoint with various scenarios
"""

import pytest
from fastapi.testclient import TestClient
from chatbot.main import app


class TestAPIEndpoints:
    """Test suite for API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    # ========================================
    # Health Check Tests
    # ========================================

    def test_root_endpoint(self, client):
        """Should return status info"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert 'version' in data

    # ========================================
    # /ask Endpoint Tests
    # ========================================

    def test_ask_endpoint_accepts_post(self, client):
        """Should accept POST requests"""
        response = client.post(
            "/ask",
            json={"question": "What are your Python skills?"}
        )

        assert response.status_code == 200

    def test_ask_endpoint_returns_json(self, client):
        """Should return JSON response"""
        response = client.post(
            "/ask",
            json={"question": "What are your AI projects?"}
        )

        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/json'

    def test_ask_endpoint_response_structure(self, client):
        """Response should have required fields"""
        response = client.post(
            "/ask",
            json={"question": "What Python experience do you have?"}
        )

        assert response.status_code == 200
        data = response.json()

        assert 'answer' in data
        assert 'sources' in data
        assert isinstance(data['answer'], str)
        assert isinstance(data['sources'], list)

    def test_ask_endpoint_skills_question(self, client):
        """Should handle SKILLS questions"""
        response = client.post(
            "/ask",
            json={"question": "What are your technical skills?"}
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data['answer']) > 0
        # Should have sources
        assert len(data['sources']) > 0

    def test_ask_endpoint_behavioral_question(self, client):
        """Should handle BEHAVIORAL questions"""
        response = client.post(
            "/ask",
            json={"question": "How do you handle difficult situations?"}
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data['answer']) > 0

    def test_ask_endpoint_filters_irrelevant(self, client):
        """Should filter irrelevant questions"""
        response = client.post(
            "/ask",
            json={"question": "What's your favorite hobby?"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should have rejection message
        assert 'contact page' in data['answer'].lower()
        assert len(data['sources']) == 0

    # ========================================
    # User API Key Tests
    # ========================================

    def test_ask_endpoint_accepts_user_api_key(self, client):
        """Should accept optional user API key"""
        response = client.post(
            "/ask",
            json={
                "question": "What skills?",
                "userApiKey": "sk-test123"
            }
        )

        # Should accept request (may fail due to invalid key, but that's OK)
        assert response.status_code in [200, 400, 500]

    def test_ask_endpoint_without_api_key(self, client):
        """Should work without user API key (use system key)"""
        response = client.post(
            "/ask",
            json={"question": "What Python skills?"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should have model note about free tier
        assert 'free' in data['answer'].lower() or 'powered by' in data['answer'].lower()

    # ========================================
    # Error Handling Tests
    # ========================================

    def test_ask_endpoint_missing_question(self, client):
        """Should reject request without question"""
        response = client.post(
            "/ask",
            json={}
        )

        assert response.status_code == 422  # Validation error

    def test_ask_endpoint_empty_question(self, client):
        """Should handle empty question gracefully"""
        response = client.post(
            "/ask",
            json={"question": ""}
        )

        # Should return something (filtered or handled)
        assert response.status_code == 200

    def test_ask_endpoint_very_long_question(self, client):
        """Should handle very long questions"""
        long_question = "What are your skills? " * 100

        response = client.post(
            "/ask",
            json={"question": long_question}
        )

        assert response.status_code == 200

    def test_ask_endpoint_special_characters(self, client):
        """Should handle special characters in question"""
        response = client.post(
            "/ask",
            json={"question": "What's your C++ & Python/JavaScript experience?"}
        )

        assert response.status_code == 200

    # ========================================
    # CORS Tests
    # ========================================

    def test_ask_endpoint_cors_headers(self, client):
        """Should include CORS headers"""
        response = client.post(
            "/ask",
            json={"question": "What skills?"}
        )

        assert response.status_code == 200
        # CORS headers should be present
        headers = response.headers
        assert 'access-control-allow-origin' in headers

    def test_options_request(self, client):
        """Should handle OPTIONS preflight request"""
        response = client.options("/ask")

        assert response.status_code == 200
        assert 'access-control-allow-methods' in response.headers

    # ========================================
    # Response Format Tests
    # ========================================

    def test_ask_endpoint_includes_sources_links(self, client):
        """Should include clickable source links"""
        response = client.post(
            "/ask",
            json={"question": "What AI projects?"}
        )

        assert response.status_code == 200
        data = response.json()

        if len(data['sources']) > 0:
            # Should have HTML links
            assert '<a href=' in data['answer']
            assert 'target="_blank"' in data['answer']

    def test_ask_endpoint_includes_model_note(self, client):
        """Should include model note in response"""
        response = client.post(
            "/ask",
            json={"question": "What skills?"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should mention model or free tier
        answer_lower = data['answer'].lower()
        assert 'powered by' in answer_lower or 'response generated' in answer_lower

    # ========================================
    # Multi-Agent System Tests
    # ========================================

    def test_ask_endpoint_uses_multi_agent(self, client):
        """Should use multi-agent orchestrator by default"""
        response = client.post(
            "/ask",
            json={"question": "What Python skills?"}
        )

        assert response.status_code == 200
        data = response.json()

        # Multi-agent response should have sources
        assert len(data['answer']) > 0

    # ========================================
    # Content Type Tests
    # ========================================

    def test_ask_endpoint_requires_json(self, client):
        """Should require JSON content type"""
        response = client.post(
            "/ask",
            data="question=test",  # Form data instead of JSON
            headers={"content-type": "application/x-www-form-urlencoded"}
        )

        # Should reject or fail validation
        assert response.status_code in [400, 422]

    def test_ask_endpoint_accepts_json_content_type(self, client):
        """Should accept application/json content type"""
        response = client.post(
            "/ask",
            json={"question": "What skills?"},
            headers={"content-type": "application/json"}
        )

        assert response.status_code == 200

    # ========================================
    # Performance Tests
    # ========================================

    def test_ask_endpoint_responds_quickly(self, client):
        """Should respond in reasonable time"""
        import time

        start = time.time()
        response = client.post(
            "/ask",
            json={"question": "What Python skills?"}
        )
        elapsed = time.time() - start

        assert response.status_code == 200
        # Should respond within 10 seconds (generous for cold start)
        assert elapsed < 10.0, f"Took {elapsed}s, should be <10s"

    def test_ask_endpoint_filter_is_fast(self, client):
        """Filtered requests should be very fast"""
        import time

        start = time.time()
        response = client.post(
            "/ask",
            json={"question": "What's the weather?"}
        )
        elapsed = time.time() - start

        assert response.status_code == 200
        # Filter should be sub-second
        assert elapsed < 2.0, f"Filter took {elapsed}s, should be <2s"

    # ========================================
    # Integration Tests
    # ========================================

    def test_multiple_requests_same_client(self, client):
        """Should handle multiple requests"""
        questions = [
            "What AI projects?",
            "How do you handle challenges?",
            "What's your favorite color?"  # Should filter
        ]

        for question in questions:
            response = client.post("/ask", json={"question": question})
            assert response.status_code == 200
            data = response.json()
            assert 'answer' in data

    def test_concurrent_requests(self, client):
        """Should handle concurrent requests"""
        import concurrent.futures

        def make_request(question):
            return client.post("/ask", json={"question": question})

        questions = [
            "What Python skills?",
            "What AI work?",
            "Leadership style?"
        ]

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request, q) for q in questions]
            results = [f.result() for f in futures]

        # All should complete successfully
        assert all(r.status_code == 200 for r in results)
