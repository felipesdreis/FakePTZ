import pytest

from fakeptz.app import CropperApp, RemoteQRScreen
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
async def test_remote_qr_button_exists():
    app = CropperApp(pipeline=FakePipeline())
    async with app.run_test():
        assert app.query_one("#btn-remote-qr")


@pytest.mark.asyncio
async def test_pressing_r_pushes_remote_qr_screen():
    app = CropperApp(pipeline=FakePipeline())
    async with app.run_test() as pilot:
        await pilot.press("r")
        assert isinstance(app.screen, RemoteQRScreen)
        app._remote_server.stop()


@pytest.mark.asyncio
async def test_remote_qr_content_is_actually_rendered_with_nonzero_size():
    # Regressão: um Static sem width/height explícitos colapsa para 0x0
    # dentro de um container width:auto/height:auto (variação do gotcha de
    # dimensionamento do Textual já documentado no CLAUDE.md deste projeto).
    app = CropperApp(pipeline=FakePipeline())
    async with app.run_test() as pilot:
        await pilot.press("r")
        art = app.screen.query_one("#remote-qr-art")
        assert art.region.width > 0
        assert art.region.height > 0
        app._remote_server.stop()


@pytest.mark.asyncio
async def test_escape_dismisses_remote_qr_screen():
    app = CropperApp(pipeline=FakePipeline())
    async with app.run_test() as pilot:
        await pilot.press("r")
        await pilot.press("escape")
        assert not isinstance(app.screen, RemoteQRScreen)
        app._remote_server.stop()
