# FakePTZ

## Testes
- `python -m pytest -q` (raiz do repo) — `pytest.ini` já tem `asyncio_mode = auto`, não precisa marcar `@pytest.mark.asyncio` manualmente nem configurar plugin.
- Testes de TUI usam `async with app.run_test() as pilot: await pilot.press("...")` / `pilot.click("#id")` (Textual). Cada arquivo de teste de app duplica uma classe `FakePipeline` fake — não existe `conftest.py` compartilhado ainda (decisão deliberada, ver histórico).
- Ao adicionar método novo na interface pública do `VideoPipeline` (ex.: `set_target`), replique-o nas 3 classes `FakePipeline` duplicadas (`test_app_input.py`, `test_app_layout.py`, `test_app_pipeline.py`) — elas não compartilham base, esquecer uma quebra só aquele arquivo de teste.

## Persistência em disco
- Não há dependência de config/serialização (`pydantic`, `platformdirs`, etc.) — módulos como `fakeptz/macros.py` usam só `json`+`pathlib`, com o caminho do arquivo como parâmetro default (`path: Path = ALGO_PATH`) em vez de global fixo, pra ficar testável com `tmp_path` sem monkeypatch.

## Gotcha: Textual `width: 1fr` quebra silenciosamente
- Muitos widgets `width: 1fr` num mesmo `Horizontal` falham silenciosamente se a soma dos `min-width` padrão (16 cols cada) exceder a largura do container (comum em terminal de teste 80 cols) — cada widget acaba recebendo a largura cheia do container em vez de dividir, e cliques em `pilot.click()` erram com `OutOfBounds`. Ao ultrapassar ~5 botões numa linha, separe em múltiplas `Horizontal` ao invés de depurar o cálculo de `fr`.


## `crop_coords_for` (fakeptz/config.py)
- Pan/tilt são frações contínuas 0.0–1.0 do espaço de deslocamento disponível; os 3 modos legados (ESQUERDA/CENTRO/DIREITA) mapeiam exatamente para pan 0.0/0.5/1.0 via `MODE_PAN_TILT`. `OUTPUT_WIDTH/HEIGHT` é derivado de `CAPTURE_WIDTH/HEIGHT * 2 // 3` (mesma proporção do crop) — não hardcode um valor separado, ou os dois podem divergir.
