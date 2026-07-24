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
async def test_app_starts_with_centro_active_and_shows_three_buttons():
    app = CropperApp(pipeline=FakePipeline())
    async with app.run_test():
        assert app.active_mode == CropMode.CENTRO
        assert app.query_one("#btn-esquerda")
        assert app.query_one("#btn-centro")
        assert app.query_one("#btn-direita")
        assert "active" in app.query_one("#btn-centro").classes


@pytest.mark.asyncio
async def test_app_shows_three_macro_buttons_and_save_button():
    app = CropperApp(pipeline=FakePipeline())
    async with app.run_test():
        assert app.query_one("#btn-macro-1")
        assert app.query_one("#btn-macro-2")
        assert app.query_one("#btn-macro-3")
        assert app.query_one("#btn-save-macro")
        assert "armed" not in app.query_one("#btn-save-macro").classes
