import json
from pathlib import Path
from typing import Dict, Tuple

from fakeptz.config import DEFAULT_MACRO_POSITION, MACRO_SLOTS

MACROS_PATH = Path.home() / ".fakeptz" / "macros.json"


def load_macros(path: Path = MACROS_PATH) -> Dict[str, Tuple[float, float, float]]:
    defaults = {slot: DEFAULT_MACRO_POSITION for slot in MACRO_SLOTS}
    try:
        raw = json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return defaults
    return {slot: tuple(raw.get(slot, defaults[slot])) for slot in MACRO_SLOTS}


def save_macro(slot: str, pan: float, tilt: float, zoom: float, path: Path = MACROS_PATH) -> None:
    macros = load_macros(path)
    macros[slot] = (pan, tilt, zoom)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({k: list(v) for k, v in macros.items()}))
