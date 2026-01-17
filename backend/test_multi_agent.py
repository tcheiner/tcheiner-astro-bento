#!/usr/bin/env python3
"""
Test script for multi-agent chatbot system

Usage:
    python test_multi_agent.py

Requirements:
    - OPENAI_API_KEY environment variable
    - ANTHROPIC_API_KEY environment variable (for behavioral questions)
    - FastAPI server running (or test directly via orchestrator)
"""

import os
import asyncio
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_environment():
    """Verify required environment variables"""
    missing = []

    if not os.getenv("OPENAI_API_KEY"):
        missing.append("OPENAI_API_KEY")

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  Warning: ANTHROPIC_API_KEY not set - behavioral questions will fail")

    if missing:
        print(f"❌ Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)

    print("✅ Environment variables check passed\n")


async def test_direct():
    """Test orchestrator directly (without FastAPI)"""
    print("=" * 80)
    print("DIRECT ORCHESTRATOR TEST")
    print("=" * 80)

    try:
        from chatbot.orchestrator import MultiAgentOrchestrator

        orchestrator = MultiAgentOrchestrator()
        print("✅ Orchestrator initialized successfully\n")

        # Test cases
        test_cases = [
            {
                "name": "SKILLS - AI Projects",
                "question": "What are your AI projects?",
                "expected_type": "SKILLS"
            },
            {
                "name": "SKILLS - Python Experience",
                "question": "Tell me about your Python experience",
                "expected_type": "SKILLS"
            },
            {
                "name": "BEHAVIORAL - Growth",
                "question": "Give me examples of how you demonstrate growth",
                "expected_type": "BEHAVIORAL"
            },
            {
                "name": "FILTERING - Hobby (should reject)",
                "question": "What is your favorite hobby?",
                "expected_type": "IRRELEVANT"
            },
        ]

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'─' * 80}")
            print(f"Test {i}/{len(test_cases)}: {test_case['name']}")
            print(f"Question: {test_case['question']}")
            print(f"{'─' * 80}")

            try:
                result = await orchestrator.process_question(test_case['question'])

                # Display results
                print(f"\n✅ Response received:")
                print(f"   Type: {result['metadata'].get('question_type', 'N/A')}")
                print(f"   Agents: {', '.join(result['agents_used'])}")
                print(f"   Cost: ${result['cost_estimate']:.4f}")
                print(f"   Sources: {len(result['sources'])} documents")

                # Show first 300 characters of answer
                answer_preview = result['answer'][:300]
                if len(result['answer']) > 300:
                    answer_preview += "..."
                print(f"\n   Answer Preview:\n   {answer_preview}\n")

                # Show sources
                if result['sources']:
                    print(f"   Source URLs:")
                    for source_url in result['sources'][:3]:
                        print(f"   - {source_url}")
                    if len(result['sources']) > 3:
                        print(f"   ... and {len(result['sources']) - 3} more")

            except Exception as e:
                print(f"❌ Test failed: {e}")
                import traceback
                traceback.print_exc()

        print(f"\n{'=' * 80}")
        print("All tests completed!")
        print(f"{'=' * 80}\n")

    except Exception as e:
        print(f"❌ Failed to initialize orchestrator: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def test_api():
    """Test via FastAPI endpoint (server must be running)"""
    print("=" * 80)
    print("API ENDPOINT TEST (FastAPI must be running on port 8000)")
    print("=" * 80)

    try:
        import requests

        base_url = "http://127.0.0.1:8000"

        # Health check
        try:
            health = requests.get(f"{base_url}/")
            print(f"✅ Server is running: {health.json()}\n")
        except requests.exceptions.ConnectionError:
            print("❌ Server not running. Start with: uvicorn chatbot.main:app --reload")
            return

        # Test question
        test_question = "What are your AI projects?"
        print(f"Testing question: {test_question}")

        response = requests.post(
            f"{base_url}/ask",
            json={"question": test_question}
        )

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Response received:")
            print(f"   Answer length: {len(result['answer'])} characters")
            print(f"   Sources: {len(result['sources'])} documents")

            # Show answer preview
            answer_preview = result['answer'][:300]
            if len(result['answer']) > 300:
                answer_preview += "..."
            print(f"\n   Answer Preview:\n   {answer_preview}\n")

            # Show sources
            if result['sources']:
                print(f"   Source URLs:")
                for source_url in result['sources'][:3]:
                    print(f"   - {source_url}")
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   {response.text}")

    except ImportError:
        print("⚠️  requests module not installed. Install with: pip install requests")
        print("   Skipping API test...\n")


async def main():
    """Main test runner"""
    print("\n" + "=" * 80)
    print("MULTI-AGENT CHATBOT SYSTEM TEST")
    print("=" * 80 + "\n")

    check_environment()

    # Run direct orchestrator test
    await test_direct()

    # Run API test (optional - requires server running)
    try:
        await test_api()
    except Exception as e:
        print(f"API test skipped: {e}")

    print("\n✅ Testing complete!")
    print("\nTo run the FastAPI server:")
    print("   cd backend")
    print("   uvicorn chatbot.main:app --reload")
    print("\nTo test production endpoint:")
    print("   curl -X POST 'https://your-api-url/ask' \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"question\": \"What are your AI projects?\"}'")


if __name__ == "__main__":
    asyncio.run(main())
