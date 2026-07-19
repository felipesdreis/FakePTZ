import pytest

from fakeptz.app import CropperApp
from fakeptz.config import CropMode


class FakePipeline:
    def __init__(self):
        self.mode = CropMode.CENTRO
        self.status = "ONLINE"
        self.current_fps = 30.0
        self.set_mode_calls = []

    def set_mode(self, mode):
        self.mode = mode
        self.set_mode_calls.append(mode)

    async def run(self, on_error):
        return None


@pytest.mark.asyncio
async def test_pressing_1_sets_esquerda_mode():
    app = CropperApp(pipeline=FakePipeline())
    async with app.run_test() as pilot:
        await pilot.press("1")
        assert app.active_mode == CropMode.ESQUERDA
        assert "active" in app.query_one("#btn-esquerda").classes
        assert "active" not in app.query_one("#btn-centro").classes


@pytest.mark.asyncio
async def test_clicking_direita_button_sets_direita_mode():
    app = CropperApp(pipeline=FakePipeline())
    async with app.run_test() as pilot:
        await pilot.click("#btn-direita")
        assert app.active_mode == CropMode.DIREITA


def test_q_key_is_bound_to_quit():
    binding_keys = {binding[0] for binding in CropperApp.BINDINGS}
    assert "q" in binding_keys
