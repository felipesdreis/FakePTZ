import pytest

from fakeptz.app import CropperApp
from fakeptz.config import CropMode


class FakePipeline:
    def __init__(self):
        self.mode = CropMode.CENTRO
        self.status = "ONLINE"
        self.current_fps = 30.0
        self.zoom, self.pan, self.tilt = 1.0, 0.5, 0.5
        self.set_mode_calls = []
        self.nudge_pan_calls = []
        self.nudge_tilt_calls = []
        self.nudge_zoom_calls = []

    def set_mode(self, mode):
        self.mode = mode
        self.set_mode_calls.append(mode)

    def nudge_pan(self, direction):
        self.nudge_pan_calls.append(direction)

    def nudge_tilt(self, direction):
        self.nudge_tilt_calls.append(direction)

    def nudge_zoom(self, direction):
        self.nudge_zoom_calls.append(direction)

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


@pytest.mark.asyncio
async def test_arrow_keys_nudge_pan_and_tilt():
    pipeline = FakePipeline()
    app = CropperApp(pipeline=pipeline)
    async with app.run_test() as pilot:
        await pilot.press("left")
        await pilot.press("right")
        await pilot.press("up")
        await pilot.press("down")
        assert pipeline.nudge_pan_calls == [-1, 1]
        assert pipeline.nudge_tilt_calls == [-1, 1]


@pytest.mark.asyncio
async def test_plus_minus_keys_nudge_zoom():
    pipeline = FakePipeline()
    app = CropperApp(pipeline=pipeline)
    async with app.run_test() as pilot:
        await pilot.press("+")
        await pilot.press("-")
        assert pipeline.nudge_zoom_calls == [1, -1]


@pytest.mark.asyncio
async def test_nudging_pan_clears_active_preset_button():
    pipeline = FakePipeline()
    app = CropperApp(pipeline=pipeline)
    async with app.run_test() as pilot:
        await pilot.press("left")
        assert "active" not in app.query_one("#btn-centro").classes


@pytest.mark.asyncio
async def test_ptz_buttons_nudge_pipeline():
    pipeline = FakePipeline()
    app = CropperApp(pipeline=pipeline)
    async with app.run_test() as pilot:
        await pilot.click("#btn-pan-minus")
        await pilot.click("#btn-pan-plus")
        await pilot.click("#btn-tilt-minus")
        await pilot.click("#btn-tilt-plus")
        await pilot.click("#btn-zoom-minus")
        await pilot.click("#btn-zoom-plus")
        assert pipeline.nudge_pan_calls == [-1, 1]
        assert pipeline.nudge_tilt_calls == [-1, 1]
        assert pipeline.nudge_zoom_calls == [-1, 1]
