from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Footer, Header, Static

from fakeptz.config import CropMode

MODE_LABELS = {
    CropMode.ESQUERDA: "1 - ESQUERDA",
    CropMode.CENTRO: "2 - CENTRO",
    CropMode.DIREITA: "3 - DIREITA",
}

MODE_BUTTON_IDS = {
    CropMode.ESQUERDA: "btn-esquerda",
    CropMode.CENTRO: "btn-centro",
    CropMode.DIREITA: "btn-direita",
}


class CropperApp(App):
    # Paleta adaptada de DESIGN-starbucks.md (ver Global Constraints para o
    # mapeamento completo de tokens web -> terminal).
    CSS = """
    $canvas: #f2f0eb;
    $card: #ffffff;
    $starbucks-green: #006241;
    $accent-green: #00754A;
    $house-green: #1E3932;
    $gold: #cba258;
    $error-red: #c82014;

    Screen {
        background: $canvas;
    }

    Header {
        background: $house-green;
        color: white;
    }

    Footer {
        background: $house-green;
        color: white 70%;
    }

    #status-panel {
        background: $card;
        color: black 87%;
        border: round $starbucks-green;
        height: 3;
        padding: 0 2;
    }

    .mode-button {
        background: $card;
        color: $accent-green;
        border: round $accent-green;
        width: 1fr;
        text-style: bold;
    }

    .mode-button:hover {
        background: #d4e9e2;
    }

    .mode-button.active {
        background: $accent-green;
        color: white;
        border: round white;
    }
    """

    BINDINGS = [
        ("1", "set_mode('ESQUERDA')", "Esquerda"),
        ("2", "set_mode('CENTRO')", "Centro"),
        ("3", "set_mode('DIREITA')", "Direita"),
        ("q", "quit", "Sair"),
    ]

    def __init__(self):
        super().__init__()
        self.title = "CROPPER VIRTUAL TUI"
        self.active_mode = CropMode.CENTRO

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(id="status-panel")
        with Horizontal():
            for mode in (CropMode.ESQUERDA, CropMode.CENTRO, CropMode.DIREITA):
                yield Button(
                    MODE_LABELS[mode],
                    id=MODE_BUTTON_IDS[mode],
                    classes="mode-button",
                )
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_active_button()
        self._refresh_status_panel()

    def action_set_mode(self, mode_value: str) -> None:
        self.active_mode = CropMode(mode_value)
        self._refresh_active_button()
        self._refresh_status_panel()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        for mode, button_id in MODE_BUTTON_IDS.items():
            if button_id == event.button.id:
                self.action_set_mode(mode.value)
                break

    def _refresh_active_button(self) -> None:
        for mode, button_id in MODE_BUTTON_IDS.items():
            button = self.query_one(f"#{button_id}", Button)
            button.set_class(mode == self.active_mode, "active")

    def _refresh_status_panel(self) -> None:
        status_panel = self.query_one("#status-panel", Static)
        status_panel.update(
            f"STATUS: [bold #cba258]TRANSMITINDO[/] | "
            f"MODO ATIVO: [bold #006241]{self.active_mode.value}[/]"
        )
