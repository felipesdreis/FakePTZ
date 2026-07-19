import pytest

from fakeptz.app import CropperApp
from fakeptz.config import CropMode


@pytest.mark.asyncio
async def test_pressing_1_sets_esquerda_mode():
    app = CropperApp()
    async with app.run_test() as pilot:
        await pilot.press("1")
        assert app.active_mode == CropMode.ESQUERDA
        assert "active" in app.query_one("#btn-esquerda").classes
        assert "active" not in app.query_one("#btn-centro").classes


@pytest.mark.asyncio
async def test_clicking_direita_button_sets_direita_mode():
    app = CropperApp()
    async with app.run_test() as pilot:
        await pilot.click("#btn-direita")
        assert app.active_mode == CropMode.DIREITA


def test_q_key_is_bound_to_quit():
    binding_keys = {binding[0] for binding in CropperApp.BINDINGS}
    assert "q" in binding_keys
