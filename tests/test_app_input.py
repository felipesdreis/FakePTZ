from unittest.mock import patch

import pytest

from fakeptz.app import CropperApp
from fakeptz.config import CropMode, DEFAULT_MACRO_POSITION


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
        self.set_target_calls = []

    def set_mode(self, mode):
        self.mode = mode
        self.set_mode_calls.append(mode)

    def set_target(self, *, zoom=None, pan=None, tilt=None):
        self.set_target_calls.append({"zoom": zoom, "pan": pan, "tilt": tilt})
        if zoom is not None:
            self.zoom = zoom
        if pan is not None:
            self.pan = pan
        if tilt is not None:
            self.tilt = tilt

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


DEFAULT_MACROS = {"M1": DEFAULT_MACRO_POSITION, "M2": DEFAULT_MACRO_POSITION, "M3": DEFAULT_MACRO_POSITION}


@pytest.mark.asyncio
async def test_clicking_macro_button_recalls_saved_position():
    pipeline = FakePipeline()
    with patch("fakeptz.app.macros.load_macros", return_value=dict(DEFAULT_MACROS)):
        app = CropperApp(pipeline=pipeline)
    async with app.run_test() as pilot:
        await pilot.click("#btn-macro-1")
        pan, tilt, zoom = DEFAULT_MACRO_POSITION
        assert pipeline.set_target_calls[-1] == {"zoom": zoom, "pan": pan, "tilt": tilt}


@pytest.mark.asyncio
async def test_pressing_4_without_save_armed_recalls_macro():
    pipeline = FakePipeline()
    with patch("fakeptz.app.macros.load_macros", return_value=dict(DEFAULT_MACROS)):
        app = CropperApp(pipeline=pipeline)
    async with app.run_test() as pilot:
        await pilot.press("4")
        assert pipeline.set_target_calls
        assert app._save_armed is False


@pytest.mark.asyncio
async def test_arming_save_then_clicking_macro_saves_current_position():
    pipeline = FakePipeline()
    pipeline.zoom, pipeline.pan, pipeline.tilt = 2.0, 0.1, 0.9
    with patch("fakeptz.app.macros.load_macros", return_value=dict(DEFAULT_MACROS)), \
            patch("fakeptz.app.macros.save_macro") as mock_save:
        app = CropperApp(pipeline=pipeline)
        async with app.run_test() as pilot:
            await pilot.press("s")
            assert app._save_armed is True
            assert "armed" in app.query_one("#btn-save-macro").classes

            await pilot.click("#btn-macro-2")
            mock_save.assert_called_once_with("M2", 0.1, 0.9, 2.0)
            assert app._save_armed is False
            assert app.macros["M2"] == (0.1, 0.9, 2.0)
            assert "armed" not in app.query_one("#btn-save-macro").classes


@pytest.mark.asyncio
async def test_pressing_s_twice_disarms_save_without_saving():
    pipeline = FakePipeline()
    with patch("fakeptz.app.macros.load_macros", return_value=dict(DEFAULT_MACROS)), \
            patch("fakeptz.app.macros.save_macro") as mock_save:
        app = CropperApp(pipeline=pipeline)
        async with app.run_test() as pilot:
            await pilot.press("s")
            await pilot.press("s")
            assert app._save_armed is False
            mock_save.assert_not_called()
