"""Tests for the email notification module."""

from unittest.mock import patch, MagicMock

from app.notifications import send_match_email


class TestSendMatchEmail:

    @patch("app.notifications.resend")
    def test_send_success(self, mock_resend):
        mock_resend.Emails.send.return_value = {"id": "email-123"}

        result = send_match_email("user@stu.pku.edu.cn")
        assert result is True
        mock_resend.Emails.send.assert_called_once()

        call_args = mock_resend.Emails.send.call_args[0][0]
        assert call_args["to"] == ["user@stu.pku.edu.cn"]
        assert "match" in call_args["subject"].lower()

    @patch("app.notifications.resend")
    def test_send_failure_does_not_raise(self, mock_resend):
        mock_resend.Emails.send.side_effect = Exception("API error")

        result = send_match_email("user@stu.pku.edu.cn")
        assert result is False  # Fire-and-forget — returns False, doesn't raise

    @patch("app.notifications.Config")
    def test_skip_when_no_api_key(self, mock_config):
        mock_config.RESEND_API_KEY = ""
        mock_config.APP_URL = "http://localhost:8765"

        result = send_match_email("user@stu.pku.edu.cn")
        assert result is False
