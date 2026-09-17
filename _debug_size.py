import asyncio
from fakeptz.app import CropperApp
from fakeptz.config import CropMode


class FakePipeline:
    def __init__(self):
        self.mode = CropMode.CENTRO
        self.status = "ONLINE"
        self.current_fps = 30.0
        self.zoom, self.pan, self.tilt = 1.0, 0.5, 0.5

    def set_mode(self, mode):
        pass

    def set_target(self, **kw):
        pass

    def nudge_pan(self, d):
        pass

    def nudge_tilt(self, d):
        pass

    def nudge_zoom(self, d):
        pass

    async def run(self, on_error):
        return None


async def test_size(w, h, out):
    app = CropperApp(pipeline=FakePipeline())
    async with app.run_test(size=(w, h)) as pilot:
        await pilot.press("r")
        screen = app.screen
        try:
            static = screen.query_one("#remote-qr-art")
            card = screen.query_one("#remote-qr-card")
            out.write(
                f"size=({w},{h}) static.region={static.region} "
                f"card.region={card.region} content_len={len(static.content)}\n"
            )
        except Exception as e:
            out.write(f"size=({w},{h}) ERROR {type(e).__name__}: {e}\n")
        app._remote_server.stop()


async def main():
    with open("_debug_size_out.txt", "w", encoding="utf-8") as out:
        for w, h in [(80, 24), (60, 20), (40, 15), (30, 10)]:
            await test_size(w, h, out)


asyncio.run(main())
