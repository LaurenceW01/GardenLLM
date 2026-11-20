"""Verify retired OpenAI models are no longer sent on live calls."""

import unittest
from unittest.mock import Mock, patch

from config import CARE_MODEL, CHAT_MODEL
from query_analyzer import analyze_query
from chat_response import generate_fallback_ai_response


class TestOpenAIModelMigration(unittest.TestCase):
    def test_model_constants(self):
        self.assertEqual(CHAT_MODEL, "gpt-5.6-terra")
        self.assertEqual(CARE_MODEL, "gpt-5.6-sol")

    @patch("query_analyzer.openai_client.chat.completions.create")
    def test_query_analysis_uses_chat_model(self, mock_create):
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = (
            '{"plant_references": ["tomato"], "query_type": "CARE", "confidence": 0.9}'
        )
        mock_create.return_value = mock_response

        analyze_query("How do I care for my tomato?", ["tomato"])

        kwargs = mock_create.call_args.kwargs
        self.assertEqual(kwargs["model"], CHAT_MODEL)
        self.assertEqual(kwargs["reasoning_effort"], "none")
        self.assertEqual(kwargs["max_completion_tokens"], 500)
        self.assertNotIn("temperature", kwargs)
        self.assertNotIn("max_tokens", kwargs)

    @patch("chat_response.openai_client.chat.completions.create")
    def test_fallback_chat_uses_chat_model(self, mock_create):
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Water deeply once a week."
        mock_create.return_value = mock_response

        result = generate_fallback_ai_response("How often should I water?")

        self.assertEqual(result, "Water deeply once a week.")
        kwargs = mock_create.call_args.kwargs
        self.assertEqual(kwargs["model"], CHAT_MODEL)
        self.assertEqual(kwargs["reasoning_effort"], "none")
        self.assertEqual(kwargs["max_completion_tokens"], 300)
        self.assertNotIn("temperature", kwargs)
        self.assertNotIn("max_tokens", kwargs)


if __name__ == "__main__":
    unittest.main()
