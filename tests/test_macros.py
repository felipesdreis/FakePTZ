from fakeptz.config import DEFAULT_MACRO_POSITION, MACRO_SLOTS
from fakeptz.macros import load_macros, save_macro


def test_load_macros_returns_defaults_when_file_missing(tmp_path):
    path = tmp_path / "macros.json"
    assert load_macros(path) == {slot: DEFAULT_MACRO_POSITION for slot in MACRO_SLOTS}


def test_load_macros_returns_defaults_when_file_corrupted(tmp_path):
    path = tmp_path / "macros.json"
    path.write_text("not valid json")
    assert load_macros(path) == {slot: DEFAULT_MACRO_POSITION for slot in MACRO_SLOTS}


def test_save_macro_persists_and_round_trips(tmp_path):
    path = tmp_path / "nested" / "macros.json"
    save_macro("M1", pan=0.2, tilt=0.8, zoom=2.5, path=path)

    macros = load_macros(path)
    assert macros["M1"] == (0.2, 0.8, 2.5)
    assert macros["M2"] == DEFAULT_MACRO_POSITION
    assert macros["M3"] == DEFAULT_MACRO_POSITION


def test_save_macro_preserves_other_slots(tmp_path):
    path = tmp_path / "macros.json"
    save_macro("M1", pan=0.2, tilt=0.8, zoom=2.5, path=path)
    save_macro("M2", pan=0.9, tilt=0.1, zoom=1.5, path=path)

    macros = load_macros(path)
    assert macros["M1"] == (0.2, 0.8, 2.5)
    assert macros["M2"] == (0.9, 0.1, 1.5)
