"""
API Test Script
Test various question types and validate responses.

Usage:
    python scripts/test_api.py
    python scripts/test_api.py --base-url http://localhost:8000
"""

import argparse
import httpx
import json
import time
from typing import Optional


class KanhaAPITester:
    """Test the Kanha API with various question types."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=120.0)
        self.results = []

    def test_health(self) -> bool:
        """Test health endpoint."""
        print("\n" + "="*60)
        print("HEALTH CHECK")
        print("="*60)

        try:
            response = self.client.get(f"{self.base_url}/health")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"Error: {e}")
            return False

    def test_chat(
        self,
        message: str,
        language: str = "english",
        category: str = "general"
    ) -> Optional[dict]:
        """Test chat endpoint with a message."""
        print(f"\n{'='*60}")
        print(f"TESTING: {category.upper()}")
        print(f"{'='*60}")
        print(f"Question: {message}")
        print(f"Language: {language}")
        print("-"*60)

        try:
            start_time = time.time()

            response = self.client.post(
                f"{self.base_url}/chat",
                json={
                    "message": message,
                    "language": language,
                    "top_k": 5
                }
            )

            elapsed = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                print(f"\nKrishna's Response:\n{data['response']}")
                print(f"\n📚 Sources ({len(data.get('sources', []))} verses):")
                for src in data.get('sources', [])[:3]:
                    print(f"  - Chapter {src.get('chapter')}, Verse {src.get('verse')}")
                print(f"\n⏱️ Response time: {elapsed:.2f}s")

                self.results.append({
                    "category": category,
                    "question": message,
                    "success": True,
                    "time": elapsed,
                    "sources_count": len(data.get('sources', []))
                })
                return data
            else:
                print(f"Error: {response.status_code}")
                print(f"Response: {response.text}")
                self.results.append({
                    "category": category,
                    "question": message,
                    "success": False,
                    "error": response.text
                })
                return None

        except Exception as e:
            print(f"Error: {e}")
            self.results.append({
                "category": category,
                "question": message,
                "success": False,
                "error": str(e)
            })
            return None

    def run_all_tests(self):
        """Run comprehensive test suite."""

        # Test cases by category
        test_cases = [
            # Existential questions
            ("What is the purpose of life?", "english", "existential"),
            ("Why do we suffer?", "english", "existential"),

            # Practical guidance
            ("How can I deal with stress at work?", "english", "practical"),
            ("I feel stuck in my career. What should I do?", "english", "practical"),

            # Emotional support
            ("I am feeling very anxious and scared about the future.", "english", "emotional"),
            ("I lost someone close to me. How do I cope?", "english", "emotional"),

            # Philosophical inquiry
            ("What is the nature of the soul?", "english", "philosophical"),
            ("How does karma work?", "english", "philosophical"),

            # Devotional questions
            ("How can I feel closer to God?", "english", "devotional"),
            ("What is the best form of worship?", "english", "devotional"),

            # Hindi questions
            ("मुझे शांति कैसे मिलेगी?", "hindi", "hindi_test"),
            ("कर्म योग क्या है?", "hindi", "hindi_test"),

            # Verse-specific
            ("Tell me about Chapter 2, Verse 47", "english", "verse_specific"),
            ("What does Krishna say about duty?", "english", "verse_specific"),

            # Modern problems
            ("How do I balance work and family life?", "english", "modern"),
            ("Is it okay to be ambitious?", "english", "modern"),
        ]

        print("\n" + "="*60)
        print("KANHA API TEST SUITE")
        print("="*60)
        print(f"Base URL: {self.base_url}")
        print(f"Total test cases: {len(test_cases)}")

        # Health check first
        if not self.test_health():
            print("\n❌ Health check failed. Is the server running?")
            return

        # Run all test cases
        for message, language, category in test_cases:
            self.test_chat(message, language, category)
            time.sleep(1)  # Brief pause between requests

        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)

        successful = [r for r in self.results if r.get('success')]
        failed = [r for r in self.results if not r.get('success')]

        print(f"✅ Passed: {len(successful)}/{len(self.results)}")
        print(f"❌ Failed: {len(failed)}/{len(self.results)}")

        if successful:
            avg_time = sum(r['time'] for r in successful) / len(successful)
            print(f"⏱️ Average response time: {avg_time:.2f}s")

        if failed:
            print("\nFailed tests:")
            for r in failed:
                print(f"  - {r['category']}: {r['question'][:50]}...")

        # By category
        print("\nResults by category:")
        categories = set(r['category'] for r in self.results)
        for cat in sorted(categories):
            cat_results = [r for r in self.results if r['category'] == cat]
            cat_success = sum(1 for r in cat_results if r.get('success'))
            print(f"  {cat}: {cat_success}/{len(cat_results)}")


def main():
    parser = argparse.ArgumentParser(description="Test Kanha API")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="API base URL"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick test (fewer questions)"
    )
    parser.add_argument(
        "--question",
        type=str,
        help="Test a single question"
    )

    args = parser.parse_args()

    tester = KanhaAPITester(base_url=args.base_url)

    if args.question:
        tester.test_health()
        tester.test_chat(args.question, "english", "custom")
    elif args.quick:
        tester.test_health()
        tester.test_chat("How can I find peace?", "english", "quick_test")
        tester.test_chat("मुझे शांति कैसे मिलेगी?", "hindi", "quick_test_hindi")
        tester.print_summary()
    else:
        tester.run_all_tests()


if __name__ == "__main__":
    main()
