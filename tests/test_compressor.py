"""
Tests for the Compressor Node.
Run with: pytest tests/
"""

import pytest
import tempfile
import os
from compressor import (
    CompressorNode,
    CompressionResult,
    ConversationTitleStrategy,
    NotificationDecisionStrategy,
    MemoryOpsStrategy,
    ReplyAndSummaryStrategy,
    TruncateStrategy,
    estimate_tokens,
    BLOCKED_CALL_SITES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_text(tokens: int) -> str:
    """Generate a fake string of approximately `tokens` tokens."""
    return "word " * (tokens * 4 // 5)  # ~1 token per 4 chars, 5 chars per "word "


# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------

class TestEstimateTokens:
    def test_empty_string(self):
        assert estimate_tokens("") == 0

    def test_known_length(self):
        assert estimate_tokens("abcd") == 1   # 4 chars = 1 token
        assert estimate_tokens("abcdefgh") == 2

    def test_long_text(self):
        text = "a" * 400
        assert estimate_tokens(text) == 100


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

class TestConversationTitleStrategy:
    def test_short_text_passthrough(self):
        strategy = ConversationTitleStrategy()
        short = "hello world"
        assert strategy.compress(short) == short

    def test_long_text_truncated(self):
        strategy = ConversationTitleStrategy()
        long_text = make_text(10000)
        result = strategy.compress(long_text)
        assert len(result) < len(long_text)
        assert "omitted" in result

    def test_preserves_head_and_tail(self):
        strategy = ConversationTitleStrategy()
        long_text = "START" + ("x" * 50000) + "END"
        result = strategy.compress(long_text)
        assert "START" in result
        assert "END" in result


class TestNotificationDecisionStrategy:
    def test_short_text_passthrough(self):
        strategy = NotificationDecisionStrategy()
        short = "notify me please"
        assert strategy.compress(short) == short

    def test_keeps_tail(self):
        strategy = NotificationDecisionStrategy()
        long_text = "OLD_STUFF " * 10000 + "RECENT_MESSAGE"
        result = strategy.compress(long_text)
        assert "RECENT_MESSAGE" in result

    def test_drops_head(self):
        strategy = NotificationDecisionStrategy()
        long_text = "ANCIENT_HISTORY " * 10000 + "recent stuff"
        result = strategy.compress(long_text)
        # Head should be gone given the compression
        assert len(result) < len(long_text)


class TestMemoryOpsStrategy:
    def test_short_text_passthrough(self):
        strategy = MemoryOpsStrategy()
        short = "file this memory"
        assert strategy.compress(short) == short

    def test_strips_soul_sections(self):
        strategy = MemoryOpsStrategy()
        # Text must exceed MAX_CHARS (12000) to trigger stripping logic
        # 49 chars * 300 reps = 14700 chars, safely over the limit
        soul_block = "## SOUL\n" + ("This is my personality and deep values and vibe. " * 300) + "\n\n"
        memory_block = "## Memory\nActual memory content to keep.\n"
        text = soul_block + memory_block
        assert len(text) > 12000  # guard: ensure we actually hit the stripping code path
        result = strategy.compress(text)
        assert "personality context omitted" in result or len(result) < len(text)

    def test_long_text_truncated(self):
        strategy = MemoryOpsStrategy()
        long_text = make_text(10000)
        result = strategy.compress(long_text)
        assert len(result) < len(long_text)


class TestReplyAndSummaryStrategy:
    def test_short_text_passthrough(self):
        strategy = ReplyAndSummaryStrategy(max_tokens=15000)
        short = "summarize this"
        assert strategy.compress(short) == short

    def test_long_text_compressed(self):
        strategy = ReplyAndSummaryStrategy(max_tokens=1000)
        long_text = make_text(10000)
        result = strategy.compress(long_text)
        assert len(result) < len(long_text)
        assert "omitted" in result

    def test_preserves_head_and_tail(self):
        strategy = ReplyAndSummaryStrategy(max_tokens=1000)
        long_text = "OPENING " + ("filler " * 20000) + " CLOSING"
        result = strategy.compress(long_text)
        assert "OPENING" in result
        assert "CLOSING" in result


class TestTruncateStrategy:
    def test_short_text_passthrough(self):
        strategy = TruncateStrategy(max_tokens=5000)
        short = "hello"
        assert strategy.compress(short) == short

    def test_truncates_at_limit(self):
        strategy = TruncateStrategy(max_tokens=100)
        long_text = make_text(10000)
        result = strategy.compress(long_text)
        assert estimate_tokens(result) <= 120  # buffer includes the truncation suffix (~14 tokens)
        assert "truncated" in result


# ---------------------------------------------------------------------------
# CompressorNode
# ---------------------------------------------------------------------------

class TestCompressorNode:

    def test_blocked_call_site_returns_blocked(self):
        compressor = CompressorNode()
        text = make_text(1000)
        result = compressor.compress(text, call_site="Reply Suggestion")
        assert result.blocked is True
        assert result.compressed_text == ""
        assert result.tokens_saved == result.original_tokens
        assert result.compression_ratio == 1.0

    def test_blocked_call_site_summary(self):
        compressor = CompressorNode()
        result = compressor.compress(make_text(500), call_site="Reply Suggestion")
        assert "BLOCKED" in result.summary()

    def test_known_call_site_compresses(self):
        compressor = CompressorNode()
        text = make_text(50000)
        result = compressor.compress(text, call_site="Conversation Title")
        assert result.blocked is False
        assert result.compressed_tokens < result.original_tokens
        assert result.tokens_saved > 0

    def test_unknown_call_site_uses_default(self):
        compressor = CompressorNode()
        text = make_text(50000)
        result = compressor.compress(text, call_site="Some Unknown Call Site")
        assert result.blocked is False
        assert isinstance(result, CompressionResult)

    def test_small_text_passthrough(self):
        compressor = CompressorNode()
        text = "tiny request"
        result = compressor.compress(text, call_site="Conversation Title")
        assert result.tokens_saved == 0
        assert result.strategy_applied == "passthrough (savings below threshold)"

    def test_disabled_compressor_passthrough(self):
        compressor = CompressorNode(enabled=False)
        text = make_text(50000)
        result = compressor.compress(text, call_site="Reply Suggestion")
        assert result.blocked is False
        assert result.strategy_applied == "disabled"
        assert result.compressed_text == text

    def test_custom_blocked_call_sites(self):
        compressor = CompressorNode(blocked_call_sites={"My Custom Site"})
        result = compressor.compress(make_text(1000), call_site="My Custom Site")
        assert result.blocked is True

    def test_reply_suggestion_in_default_blocked_set(self):
        assert "Reply Suggestion" in BLOCKED_CALL_SITES

    def test_compression_result_fields(self):
        compressor = CompressorNode()
        text = make_text(50000)
        result = compressor.compress(text, call_site="Conversation Title", task_type="title_gen")
        assert result.call_site == "Conversation Title"
        assert result.task_type == "title_gen"
        assert result.original_tokens > 0
        assert 0.0 <= result.compression_ratio <= 1.0


# ---------------------------------------------------------------------------
# from_config()
# ---------------------------------------------------------------------------

class TestFromConfig:
    def test_load_yaml_config(self, tmp_path):
        config_content = """
enabled: true
call_sites:
  "My Title Generator":
    strategy: head_tail
  "My Reply Bot":
    blocked: true
  "My Memory Agent":
    strategy: memory_ops
    max_tokens: 3000
"""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(config_content)

        compressor = CompressorNode.from_config(str(config_file))

        # blocked site
        result = compressor.compress(make_text(1000), call_site="My Reply Bot")
        assert result.blocked is True

        # compressed site
        result = compressor.compress(make_text(50000), call_site="My Title Generator")
        assert result.blocked is False
        assert result.tokens_saved > 0

    def test_load_json_config(self, tmp_path):
        import json
        config = {
            "enabled": True,
            "call_sites": {
                "My Agent": {"strategy": "truncate", "max_tokens": 1000},
                "My Blocker": {"blocked": True}
            }
        }
        config_file = tmp_path / "test_config.json"
        config_file.write_text(json.dumps(config))

        compressor = CompressorNode.from_config(str(config_file))

        result = compressor.compress(make_text(1000), call_site="My Blocker")
        assert result.blocked is True

    def test_invalid_strategy_raises(self, tmp_path):
        config_content = """
call_sites:
  "Bad Site":
    strategy: nonexistent_strategy
"""
        config_file = tmp_path / "bad_config.yaml"
        config_file.write_text(config_content)

        with pytest.raises(ValueError, match="Unknown strategy"):
            CompressorNode.from_config(str(config_file))

    def test_disabled_config(self, tmp_path):
        config_content = """
enabled: false
call_sites:
  "Reply Suggestion":
    blocked: true
"""
        config_file = tmp_path / "disabled_config.yaml"
        config_file.write_text(config_content)

        compressor = CompressorNode.from_config(str(config_file))
        # disabled = nothing gets blocked or compressed
        result = compressor.compress(make_text(1000), call_site="Reply Suggestion")
        assert result.blocked is False
        assert result.strategy_applied == "disabled"
