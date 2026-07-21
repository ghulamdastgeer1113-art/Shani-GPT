import pytest

from utils import is_image_prompt, clean_image_prompt, allowed_file


def test_is_image_prompt_detects_image_requests():
    assert is_image_prompt("Generate an image of a sunset")
    assert is_image_prompt("draw a portrait")
    assert not is_image_prompt("Tell me a story")


def test_clean_image_prompt_removes_keywords_and_stop_words():
    prompt = "Generate a beautiful picture of a forest with fog"
    cleaned = clean_image_prompt(prompt)
    assert "forest" in cleaned
    assert "generate" not in cleaned
    assert "picture" not in cleaned


def test_allowed_file_verifies_extensions():
    assert allowed_file("document.pdf", {"pdf"})
    assert not allowed_file("archive.zip", {"pdf"})
