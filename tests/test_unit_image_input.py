#!/usr/bin/env python
"""Unit tests for multi-image markdown feature."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processing.markdown_parser import extract_all_image_urls, extract_prompt_text


def test_extract_prompt_text():
    """Test prompt extraction from first line."""
    content = "A detective in a newspaper office.\n\n![image](https://example.com/1.png)\n\n![image](https://example.com/2.png)"
    result = extract_prompt_text(content)
    assert result == "A detective in a newspaper office."
    print("✅ Prompt correctly extracted from line 1")


def test_extract_single_image():
    """Test extraction of single image URL."""
    content = "A prompt.\n\n![image](https://example.com/ref.png)"
    urls = extract_all_image_urls(content)
    assert len(urls) == 1
    assert urls[0] == "https://example.com/ref.png"
    print("✅ Single image URL correctly extracted")


def test_extract_multiple_images():
    """Test extraction of multiple image URLs in order."""
    content = "A prompt.\n\n![image](https://example.com/first.png)\n\n![image](https://example.com/second.png)\n\n![image](https://example.com/third.png)"
    urls = extract_all_image_urls(content)
    assert len(urls) == 3
    assert urls[0] == "https://example.com/first.png"
    assert urls[1] == "https://example.com/second.png"
    assert urls[2] == "https://example.com/third.png"
    print("✅ Multiple image URLs extracted in correct order")


def test_extract_raw_urls():
    """Test extraction of raw URLs (not markdown syntax)."""
    content = "A prompt.\nhttps://example.com/raw.png\nhttps://example.com/another.png"
    urls = extract_all_image_urls(content)
    assert len(urls) == 2
    assert urls[0] == "https://example.com/raw.png"
    assert urls[1] == "https://example.com/another.png"
    print("✅ Raw URLs correctly extracted")


def test_mixed_formats():
    """Test extraction of mixed markdown and raw URLs."""
    content = "A prompt.\n![image](https://example.com/md.png)\nhttps://example.com/raw.png"
    urls = extract_all_image_urls(content)
    assert len(urls) == 2
    assert urls[0] == "https://example.com/md.png"
    assert urls[1] == "https://example.com/raw.png"
    print("✅ Mixed formats correctly extracted")


def test_no_images_raises_error():
    """Test that missing images raises ValueError."""
    content = "Just a prompt, no images."
    try:
        extract_all_image_urls(content)
        assert False, "Should have raised ValueError"
    except ValueError:
        print("✅ Correctly raises ValueError when no images found")


def main():
    """Run all unit tests."""
    print("=" * 50)
    print("Multi-Image Markdown Feature Unit Tests")
    print("=" * 50)

    try:
        test_extract_prompt_text()
        test_extract_single_image()
        test_extract_multiple_images()
        test_extract_raw_urls()
        test_mixed_formats()
        test_no_images_raises_error()

        print("\n" + "=" * 50)
        print("All unit tests passed!")
        return 0
    except AssertionError as e:
        print(f"\nTest failed: {e}")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
