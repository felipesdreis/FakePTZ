import asyncio
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Static, Button


class MinimalScreen(App):
    CSS = """
    #card {
        background: white;
        border: round green;
        padding: 1 3;
        width: auto;
        height: auto;
    }

    #art {
        width: auto;
        max-width: 40;
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="card"):
            yield Static(
                "Esta e uma frase bem longa sem quebras de linha que deveria quebrar sozinha quando o width for limitado",
                id="art",
            )
        yield Button("close")


async def main():
    app = MinimalScreen()
    async with app.run_test() as pilot:
        static = app.query_one("#art")
        card = app.query_one("#card")
        with open("_debug_minimal_out.txt", "w", encoding="utf-8") as f:
            f.write(f"static.region={static.region} card.region={card.region}\n")
            f.write(f"static.content={static.content!r}\n")


asyncio.run(main())
