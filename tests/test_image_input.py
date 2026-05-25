#!/usr/bin/env python
"""Test script for multi-image markdown feature."""

import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_dry_run_with_multi_image():
    """Test dry run with markdown files containing multiple images."""
    print("Testing multi-image markdown feature with dry-run...")

    cmd = [sys.executable, "-m", "src.main", "--dry-run", "--no-progress"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            print(f"Test failed with return code: {result.returncode}")
            print(f"STDERR:\n{result.stderr}")
            return False

        print("✅ Multi-image dry run passed")
        return True

    except subprocess.TimeoutExpired:
        print("Test timed out")
        return False
    except Exception as e:
        print(f"Test error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 50)
    print("Multi-Image Markdown Feature Tests")
    print("=" * 50)

    tests_passed = 0
    tests_total = 1

    if test_dry_run_with_multi_image():
        tests_passed += 1

    print("\n" + "=" * 50)
    print(f"Results: {tests_passed}/{tests_total} tests passed")

    if tests_passed == tests_total:
        print("All tests passed!")
        return 0
    else:
        print(f"{tests_total - tests_passed} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
