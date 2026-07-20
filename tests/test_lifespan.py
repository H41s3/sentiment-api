from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI

from app.main import lifespan


@pytest.fixture
def mock_service():
    service = MagicMock()
    service.is_loaded = False
    return service


@pytest.mark.anyio
async def test_lifespan_loads_model(mock_service):
    app = FastAPI()
    with patch("app.main.get_sentiment_service", return_value=mock_service):
        with patch("app.main.MODEL_LOADED") as gauge:
            async with lifespan(app):
                mock_service.load.assert_called_once()
                gauge.set.assert_any_call(1)


@pytest.mark.anyio
async def test_lifespan_warms_up_after_load(mock_service):
    app = FastAPI()
    call_order = []
    mock_service.load.side_effect = lambda: call_order.append("load")
    mock_service.warm_up.side_effect = lambda: call_order.append("warm_up")
    with patch("app.main.get_sentiment_service", return_value=mock_service):
        with patch("app.main.MODEL_LOADED"):
            async with lifespan(app):
                pass
    assert call_order == ["load", "warm_up"]


@pytest.mark.anyio
async def test_lifespan_unloads_on_shutdown(mock_service):
    app = FastAPI()
    with patch("app.main.get_sentiment_service", return_value=mock_service):
        with patch("app.main.MODEL_LOADED") as gauge:
            async with lifespan(app):
                pass
    mock_service.unload.assert_called_once()
    gauge.set.assert_any_call(0)


@pytest.mark.anyio
async def test_lifespan_sets_gauge_to_zero_on_shutdown(mock_service):
    app = FastAPI()
    gauge_values = []
    with patch("app.main.get_sentiment_service", return_value=mock_service):
        with patch("app.main.MODEL_LOADED") as gauge:
            gauge.set.side_effect = lambda v: gauge_values.append(v)
            async with lifespan(app):
                pass
    assert gauge_values == [1, 0]
