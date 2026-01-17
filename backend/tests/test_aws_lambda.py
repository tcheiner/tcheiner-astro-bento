#!/usr/bin/env python3
"""
Test script for AWS Lambda multi-agent chatbot endpoint

Tests the production Lambda deployment at:
https://5f3ysv93x1.execute-api.us-east-1.amazonaws.com/prod/ask

Usage:
    python test_aws_lambda.py
"""

import requests
import json
import sys
from typing import Dict, Any

# AWS Lambda endpoint
LAMBDA_ENDPOINT = "https://5f3ysv93x1.execute-api.us-east-1.amazonaws.com/prod/ask"


def test_lambda_endpoint(question: str, test_name: str) -> Dict[str, Any]:
    """
    Test a question against the Lambda endpoint

    Args:
        question: The question to ask
        test_name: Descriptive name for the test

    Returns:
        Response data or error information
    """
    print(f"\n{'─' * 80}")
    print(f"Test: {test_name}")
    print(f"Question: {question}")
    print(f"{'─' * 80}")

    try:
        response = requests.post(
            LAMBDA_ENDPOINT,
            json={"question": question},
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        print(f"\n✅ Response Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()

            # Display results
            print(f"\n📊 Response Details:")
            print(f"   Answer Length: {len(result.get('answer', ''))} characters")
            print(f"   Sources: {len(result.get('sources', []))} documents")

            # Show full answer
            print(f"\n💬 Answer:")
            print(f"   {result.get('answer', 'No answer provided')}\n")

            # Show sources
            sources = result.get('sources', [])
            if sources:
                print(f"   📚 Source URLs:")
                for source_url in sources[:5]:
                    print(f"   - {source_url}")
                if len(sources) > 5:
                    print(f"   ... and {len(sources) - 5} more")

            return {
                "success": True,
                "status_code": response.status_code,
                "answer": result.get('answer'),
                "sources": sources
            }
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text
            }

    except requests.exceptions.Timeout:
        print(f"❌ Request timed out after 30 seconds")
        return {"success": False, "error": "Timeout"}

    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return {"success": False, "error": str(e)}

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return {"success": False, "error": str(e)}


def main():
    """Run test suite against AWS Lambda endpoint"""
    print("=" * 80)
    print("AWS LAMBDA MULTI-AGENT CHATBOT TEST")
    print("=" * 80)
    print(f"\nEndpoint: {LAMBDA_ENDPOINT}\n")

    # Test cases
    test_cases = [
        {
            "name": "SKILLS - AI Projects",
            "question": "What are your AI projects?",
            "expected": "Should return AI-related projects"
        },
        {
            "name": "SKILLS - Python Experience",
            "question": "Tell me about your Python experience",
            "expected": "Should return Python work experience"
        },
        {
            "name": "BEHAVIORAL - Growth",
            "question": "Give me examples of how you demonstrate growth",
            "expected": "Should return behavioral response with blog examples"
        },
        {
            "name": "FILTERING - Hobby (should reject)",
            "question": "What is your favorite hobby?",
            "expected": "Should reject with contact page referral"
        },
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'═' * 80}")
        print(f"TEST {i}/{len(test_cases)}")
        print(f"{'═' * 80}")

        result = test_lambda_endpoint(
            question=test_case['question'],
            test_name=test_case['name']
        )

        result['test_name'] = test_case['name']
        result['expected'] = test_case['expected']
        results.append(result)

    # Summary
    print(f"\n{'═' * 80}")
    print("TEST SUMMARY")
    print(f"{'═' * 80}\n")

    passed = sum(1 for r in results if r.get('success'))
    failed = len(results) - passed

    print(f"✅ Passed: {passed}/{len(results)}")
    print(f"❌ Failed: {failed}/{len(results)}")

    if failed > 0:
        print(f"\n⚠️  Failed Tests:")
        for r in results:
            if not r.get('success'):
                print(f"   - {r['test_name']}: {r.get('error', 'Unknown error')}")

    print(f"\n{'═' * 80}")
    print("🎯 Testing complete!")
    print(f"{'═' * 80}\n")

    # Return exit code
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
