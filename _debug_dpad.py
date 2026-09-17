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


async def main():
    app = CropperApp(pipeline=FakePipeline())
    async with app.run_test() as pilot:
        ids = [
            "btn-tilt-minus",
            "btn-pan-minus",
            "btn-pan-plus",
            "btn-tilt-plus",
        ]
        with open("_debug_dpad_out.txt", "w", encoding="utf-8") as f:
            grid = app.query_one("#dpad")
            f.write(f"grid.region={grid.region}\n")
            for wid in ids:
                w = app.query_one(f"#{wid}")
                f.write(f"{wid}.region={w.region}\n")


asyncio.run(main())
