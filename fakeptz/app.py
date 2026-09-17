from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Center, Grid, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Static

from fakeptz import macros
from fakeptz.config import CropMode, MACRO_SLOTS
from fakeptz.remote import RemoteServer, build_qr_ascii
from fakeptz.video import VideoPipeline

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

MACRO_BUTTON_IDS = {
    "M1": "btn-macro-1",
    "M2": "btn-macro-2",
    "M3": "btn-macro-3",
}

MACRO_LABELS = {
    "M1": "4 - M1",
    "M2": "5 - M2",
    "M3": "6 - M3",
}

SAVE_BUTTON_ID = "btn-save-macro"

PAN_ROW = [
    ("btn-pan-minus", "◀", "nudge_pan", -1),
    ("btn-pan-plus", "▶", "nudge_pan", 1),
]
TILT_ROW = [
    ("btn-tilt-minus", "▲", "nudge_tilt", -1),
    ("btn-tilt-plus", "▼", "nudge_tilt", 1),
]
ZOOM_ROW = [
    ("btn-zoom-minus", "Zoom −", "nudge_zoom", -1),
    ("btn-zoom-plus", "Zoom +", "nudge_zoom", 1),
]
PTZ_BUTTON_ROWS = [PAN_ROW, TILT_ROW, ZOOM_ROW]
PTZ_BUTTON_ACTIONS = {
    button_id: (method, direction)
    for row in PTZ_BUTTON_ROWS
    for button_id, _, method, direction in row
}

REMOTE_QR_BUTTON_ID = "btn-remote-qr"


class RemoteQRScreen(ModalScreen):
    CSS = """
    RemoteQRScreen {
        align: center middle;
    }

    #remote-qr-card {
        background: #ffffff;
        border: round #006241;
        padding: 1 3;
        width: auto;
        height: auto;
        max-height: 100%;
        overflow-y: auto;
    }

    #remote-qr-art {
        width: auto;
        max-width: 60;
        height: auto;
        color: black;
        margin-bottom: 1;
    }
    """

    BINDINGS = [("escape", "dismiss", "Fechar")]

    def __init__(self, url: str, ascii_art: str):
        super().__init__()
        self._url = url
        self._ascii_art = ascii_art

    def compose(self) -> ComposeResult:
        with Vertical(id="remote-qr-card"):
            yield Static(
                f"{self._ascii_art}\n\n{self._url}\n\n"
                "Firewall do Windows pode pedir permissão — clique em Permitir.\n"
                "Desative a VPN se o celular não conectar.",
                id="remote-qr-art",
            )
        yield Button("Fechar (ESC)", id="btn-close-remote-qr")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-close-remote-qr":
            self.dismiss()


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

    .ptz-button {
        background: $card;
        color: $house-green;
        border: round $house-green;
        width: 1fr;
    }

    .ptz-button:hover {
        background: #d4e9e2;
    }

    #dpad {
        grid-size: 3 3;
        grid-gutter: 0;
        width: 27;
        height: 9;
    }

    .dpad-btn {
        width: 100%;
        height: 100%;
    }

    .dpad-empty {
        background: $canvas;
    }

    .dpad-hub {
        background: $card;
        color: $house-green;
        content-align: center middle;
        border: round $house-green;
    }

    .save-button {
        background: $card;
        color: $error-red;
        border: round $error-red;
        width: 1fr;
        text-style: bold;
    }

    .save-button:hover {
        background: #f6dcd9;
    }

    .save-button.armed {
        background: $error-red;
        color: white;
        border: round white;
    }
    """

    BINDINGS = [
        ("1", "set_mode('ESQUERDA')", "Esquerda"),
        ("2", "set_mode('CENTRO')", "Centro"),
        ("3", "set_mode('DIREITA')", "Direita"),
        ("4", "recall_or_save_macro('M1')", "Macro 1"),
        ("5", "recall_or_save_macro('M2')", "Macro 2"),
        ("6", "recall_or_save_macro('M3')", "Macro 3"),
        ("s", "toggle_save_armed", "Salvar"),
        ("left", "nudge_pan(-1)", "Pan -"),
        ("right", "nudge_pan(1)", "Pan +"),
        ("up", "nudge_tilt(-1)", "Tilt -"),
        ("down", "nudge_tilt(1)", "Tilt +"),
        ("+", "nudge_zoom(1)", "Zoom +"),
        ("-", "nudge_zoom(-1)", "Zoom -"),
        ("q", "quit", "Sair"),
        ("r", "show_remote_qr", "QR Remoto"),
    ]

    def __init__(self, pipeline: Optional[VideoPipeline] = None):
        super().__init__()
        self.title = "CROPPER VIRTUAL TUI"
        self.pipeline = pipeline or VideoPipeline()
        self.active_mode = self.pipeline.mode
        self.macros = macros.load_macros()
        self._save_armed = False
        self._remote_server: Optional[RemoteServer] = None

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
        with Horizontal():
            for slot in MACRO_SLOTS:
                yield Button(
                    MACRO_LABELS[slot],
                    id=MACRO_BUTTON_IDS[slot],
                    classes="mode-button",
                )
            yield Button("S - SALVAR", id=SAVE_BUTTON_ID, classes="save-button")
        with Center():
            with Grid(id="dpad"):
                yield Static(classes="dpad-empty")
                yield Button(TILT_ROW[0][1], id=TILT_ROW[0][0], classes="ptz-button dpad-btn")
                yield Static(classes="dpad-empty")
                yield Button(PAN_ROW[0][1], id=PAN_ROW[0][0], classes="ptz-button dpad-btn")
                yield Static("●", classes="dpad-hub")
                yield Button(PAN_ROW[1][1], id=PAN_ROW[1][0], classes="ptz-button dpad-btn")
                yield Static(classes="dpad-empty")
                yield Button(TILT_ROW[1][1], id=TILT_ROW[1][0], classes="ptz-button dpad-btn")
                yield Static(classes="dpad-empty")
        with Horizontal():
            for button_id, label, _method, _direction in ZOOM_ROW:
                yield Button(label, id=button_id, classes="ptz-button")
        with Horizontal():
            yield Button("R - QR REMOTO", id=REMOTE_QR_BUTTON_ID, classes="ptz-button")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_active_button()
        self._refresh_status_panel()
        self.run_worker(self.pipeline.run(self._handle_pipeline_error), exclusive=True)
        self.set_interval(0.5, self._refresh_status_panel)

    def on_unmount(self) -> None:
        if self._remote_server is not None:
            self._remote_server.stop()

    def action_set_mode(self, mode_value: str) -> None:
        self.active_mode = CropMode(mode_value)
        self.pipeline.set_mode(self.active_mode)
        self._refresh_active_button()
        self._refresh_status_panel()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        for mode, button_id in MODE_BUTTON_IDS.items():
            if button_id == event.button.id:
                self.action_set_mode(mode.value)
                return

        for slot, button_id in MACRO_BUTTON_IDS.items():
            if button_id == event.button.id:
                self.action_recall_or_save_macro(slot)
                return

        if event.button.id == SAVE_BUTTON_ID:
            self.action_toggle_save_armed()
            return

        if event.button.id in PTZ_BUTTON_ACTIONS:
            method, direction = PTZ_BUTTON_ACTIONS[event.button.id]
            getattr(self, f"action_{method}")(direction)
            return

        if event.button.id == REMOTE_QR_BUTTON_ID:
            self.action_show_remote_qr()

    def action_toggle_save_armed(self) -> None:
        self._save_armed = not self._save_armed
        self._refresh_save_button()

    def action_recall_or_save_macro(self, slot: str) -> None:
        if self._save_armed:
            macros.save_macro(slot, self.pipeline.pan, self.pipeline.tilt, self.pipeline.zoom)
            self.macros[slot] = (self.pipeline.pan, self.pipeline.tilt, self.pipeline.zoom)
            self._save_armed = False
            self._refresh_save_button()
        else:
            pan, tilt, zoom = self.macros[slot]
            self.pipeline.set_target(zoom=zoom, pan=pan, tilt=tilt)
            self.active_mode = None
            self._refresh_active_button()
            self._refresh_status_panel()

    def action_nudge_pan(self, direction: int) -> None:
        self.pipeline.nudge_pan(direction)
        self.active_mode = None
        self._refresh_active_button()
        self._refresh_status_panel()

    def action_nudge_tilt(self, direction: int) -> None:
        self.pipeline.nudge_tilt(direction)
        self.active_mode = None
        self._refresh_active_button()
        self._refresh_status_panel()

    def action_nudge_zoom(self, direction: int) -> None:
        self.pipeline.nudge_zoom(direction)
        self._refresh_status_panel()

    def action_show_remote_qr(self) -> None:
        if self._remote_server is None:
            self._remote_server = RemoteServer(self)
        try:
            url = self._remote_server.start()
        except OSError as exc:
            self.notify(f"Não foi possível iniciar o servidor remoto: {exc}", severity="error")
            return
        self.push_screen(RemoteQRScreen(url, build_qr_ascii(url)))

    def _handle_pipeline_error(self, message: str) -> None:
        self.exit(message=f"[ERRO] {message}")

    def _refresh_active_button(self) -> None:
        for mode, button_id in MODE_BUTTON_IDS.items():
            button = self.query_one(f"#{button_id}", Button)
            button.set_class(mode == self.active_mode, "active")

    def _refresh_save_button(self) -> None:
        button = self.query_one(f"#{SAVE_BUTTON_ID}", Button)
        button.set_class(self._save_armed, "armed")

    def _refresh_status_panel(self) -> None:
        status_panel = self.query_one("#status-panel", Static)
        # Gold é reservado para o estado "ONLINE" (momento cerimonial, per
        # DESIGN-starbucks.md); erro usa o vermelho semântico do doc.
        status_color = "#cba258" if self.pipeline.status == "ONLINE" else "#c82014"
        modo_label = self.active_mode.value if self.active_mode else "LIVRE"
        status_panel.update(
            f"STATUS: [bold {status_color}]{self.pipeline.status}[/] "
            f"({self.pipeline.current_fps:.0f} FPS) | "
            f"Z:{self.pipeline.zoom:.1f}x P:{self.pipeline.pan:.0%} T:{self.pipeline.tilt:.0%} | "
            f"MODO ATIVO: [bold #006241]{modo_label}[/]"
        )
