import pytest

from fakeptz.app import CropperApp
from fakeptz.config import CropMode


@pytest.mark.asyncio
async def test_app_starts_with_centro_active_and_shows_three_buttons():
    app = CropperApp()
    async with app.run_test():
        assert app.active_mode == CropMode.CENTRO
        assert app.query_one("#btn-esquerda")
        assert app.query_one("#btn-centro")
        assert app.query_one("#btn-direita")
        assert "active" in app.query_one("#btn-centro").classes
