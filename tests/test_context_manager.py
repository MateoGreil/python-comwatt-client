from unittest.mock import patch

import pytest

from comwatt_client import ComwattClient


def test_enter_returns_same_client_instance(client):
    with client as c:
        assert isinstance(c, ComwattClient)
        assert c is client


def test_close_calls_session_close(client):
    with patch.object(client.session, "close") as mock_close:
        client.close()

        mock_close.assert_called_once()


def test_close_is_idempotent(client):
    with patch.object(client.session, "close") as mock_close:
        client.close()
        client.close()

        assert mock_close.call_count == 2


def test_exiting_with_block_calls_close(client):
    with patch.object(client.session, "close") as mock_close:
        with client:
            mock_close.assert_not_called()

        mock_close.assert_called_once()


def test_exception_in_with_block_propagates_and_still_closes(client):
    with patch.object(client.session, "close") as mock_close:
        with pytest.raises(ValueError):
            with client:
                raise ValueError("boom")

        mock_close.assert_called_once()
