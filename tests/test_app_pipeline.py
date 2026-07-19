from unittest.mock import patch

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
async def test_mode_switch_forwards_to_pipeline():
    pipeline = FakePipeline()
    app = CropperApp(pipeline=pipeline)
    async with app.run_test() as pilot:
        await pilot.press("3")
        assert pipeline.set_mode_calls == [CropMode.DIREITA]


@pytest.mark.asyncio
async def test_status_panel_shows_pipeline_telemetry():
    pipeline = FakePipeline()
    app = CropperApp(pipeline=pipeline)
    async with app.run_test():
        status_panel = app.query_one("#status-panel")
        rendered = str(status_panel.content)
        assert "ONLINE" in rendered
        assert "30 FPS" in rendered


@pytest.mark.asyncio
async def test_pipeline_error_triggers_safe_exit():
    pipeline = FakePipeline()
    app = CropperApp(pipeline=pipeline)
    async with app.run_test():
        with patch.object(app, "exit") as mock_exit:
            app._handle_pipeline_error("driver ausente")
            mock_exit.assert_called_once_with(message="[ERRO] driver ausente")
