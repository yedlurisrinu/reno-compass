"""Eval: grounding tool compiles under the unified google-genai SDK.

Reno Compass now uses a single google-genai client for both Vertex AI and
Google AI Studio (see src/agents/base.py). Modern Gemini grounding uses the
google_search tool on both backends, replacing the legacy split between
Vertex's google_search and AI Studio's deprecated google_search_retrieval.
"""

from google.genai import types


def test_grounding_tool_compilation():
    """The google_search grounding tool builds and nests into a request config."""
    tool = types.Tool(google_search=types.GoogleSearch())
    assert tool is not None
    assert tool.google_search is not None

    config = types.GenerateContentConfig(
        system_instruction="Test system instruction",
        tools=[tool],
    )
    assert config.tools and len(config.tools) == 1


def test_ungrounded_config_compilation():
    """A config with no tools (used for structured extraction) builds cleanly."""
    config = types.GenerateContentConfig(
        system_instruction="Extract JSON only",
        tools=None,
    )
    assert config is not None
