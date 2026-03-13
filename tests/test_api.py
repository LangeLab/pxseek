"""Tests for pxscraper.api module."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from pxscraper.api import (
    DATASET_XML_URL,
    SUMMARY_URL,
    _session,
    fetch_dataset_xml,
    fetch_summary,
)
from pxscraper.models import USER_AGENT

# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------


class TestSession:
    def test_user_agent_set(self):
        s = _session()
        assert s.headers["User-Agent"] == USER_AGENT

    def test_returns_session_instance(self):
        s = _session()
        assert isinstance(s, requests.Session)


# ---------------------------------------------------------------------------
# fetch_summary
# ---------------------------------------------------------------------------


MOCK_TSV = (
    "Dataset Identifier\tTitle\tRepos\n"
    "PXD000001\tTest\tPRIDE\n"
)


class TestFetchSummary:
    def test_returns_text(self):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = MOCK_TSV
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        result = fetch_summary(session=mock_session)
        assert result == MOCK_TSV
        mock_session.get.assert_called_once_with(SUMMARY_URL, timeout=60)
        mock_resp.raise_for_status.assert_called_once()

    def test_raises_on_http_error(self):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_session.get.return_value = mock_resp

        with pytest.raises(requests.HTTPError):
            fetch_summary(session=mock_session)

    def test_creates_own_session_if_none(self):
        with patch("pxscraper.api._session") as mock_session_fn:
            mock_session = MagicMock()
            mock_resp = MagicMock()
            mock_resp.text = MOCK_TSV
            mock_resp.raise_for_status = MagicMock()
            mock_session.get.return_value = mock_resp
            mock_session_fn.return_value = mock_session

            result = fetch_summary()
            assert result == MOCK_TSV
            mock_session_fn.assert_called_once()


# ---------------------------------------------------------------------------
# fetch_dataset_xml
# ---------------------------------------------------------------------------


MOCK_XML = '<?xml version="1.0"?><ProteomeXchangeDataset id="PXD000001"/>'


class TestFetchDatasetXml:
    def test_returns_xml(self):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = MOCK_XML
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        result = fetch_dataset_xml("PXD000001", session=mock_session, delay=0)
        assert result == MOCK_XML
        expected_url = DATASET_XML_URL.format(dataset_id="PXD000001")
        mock_session.get.assert_called_once_with(expected_url, timeout=60)

    def test_applies_delay(self):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = MOCK_XML
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        with patch("pxscraper.api.time.sleep") as mock_sleep:
            fetch_dataset_xml("PXD000001", session=mock_session, delay=0.5)
            mock_sleep.assert_called_once_with(0.5)

    def test_no_delay_when_zero(self):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = MOCK_XML
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        with patch("pxscraper.api.time.sleep") as mock_sleep:
            fetch_dataset_xml("PXD000001", session=mock_session, delay=0)
            mock_sleep.assert_not_called()

    def test_raises_on_http_error(self):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("404")
        mock_session.get.return_value = mock_resp

        with pytest.raises(requests.HTTPError):
            fetch_dataset_xml("PXD000001", session=mock_session, delay=0)
