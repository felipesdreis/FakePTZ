# FakePTZ

## Testes
- `python -m pytest -q` (raiz do repo) — `pytest.ini` já tem `asyncio_mode = auto`, não precisa marcar `@pytest.mark.asyncio` manualmente nem configurar plugin.
- Testes de TUI usam `async with app.run_test() as pilot: await pilot.press("...")` / `pilot.click("#id")` (Textual). Cada arquivo de teste de app duplica uma classe `FakePipeline` fake — não existe `conftest.py` compartilhado ainda (decisão deliberada, ver histórico).

## Gotcha: Textual `width: 1fr` quebra silenciosamente
- Muitos widgets `width: 1fr` num mesmo `Horizontal` falham silenciosamente se a soma dos `min-width` padrão (16 cols cada) exceder a largura do container (comum em terminal de teste 80 cols) — cada widget acaba recebendo a largura cheia do container em vez de dividir, e cliques em `pilot.click()` erram com `OutOfBounds`. Ao ultrapassar ~5 botões numa linha, separe em múltiplas `Horizontal` ao invés de depurar o cálculo de `fr`.


## `crop_coords_for` (fakeptz/config.py)
- Pan/tilt são frações contínuas 0.0–1.0 do espaço de deslocamento disponível; os 3 modos legados (ESQUERDA/CENTRO/DIREITA) mapeiam exatamente para pan 0.0/0.5/1.0 via `MODE_PAN_TILT`. `OUTPUT_WIDTH/HEIGHT` é derivado de `CAPTURE_WIDTH/HEIGHT * 2 // 3` (mesma proporção do crop) — não hardcode um valor separado, ou os dois podem divergir.
