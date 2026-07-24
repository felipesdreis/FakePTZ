# FakePTZ

Simulador de câmera PTZ (Pan/Tilt/Zoom) por software: captura sua webcam, recorta/redimensiona o frame em tempo real e transmite o resultado para uma câmera virtual (compatível com Zoom, OBS, etc.), controlado por uma TUI (interface de terminal).

## Requisitos

- Windows (o driver de câmera virtual usado, Unity Capture, é um filtro DirectShow).
- Python 3.8+
- Uma câmera virtual registrada com o nome `virtual_cam_ptz`, usando o driver Unity Capture já incluído em [`driver-unity-capture.zip`](driver-unity-capture.zip) — veja [`docs/setup-virtual-camera.md`](docs/setup-virtual-camera.md) para o passo a passo de instalação.

## Instalação

```bash
pip install -r requirements.txt
```

Para rodar os testes, instale também as dependências de desenvolvimento:

```bash
pip install -r requirements-dev.txt
```

## Uso

```bash
python main.py
```

A TUI abre, inicia a captura da webcam (índice 0) e começa a transmitir para a câmera virtual `virtual_cam_ptz`. Selecione essa câmera como fonte de vídeo no Zoom (ou outro app de videoconferência).

### Controles

| Tecla / Botão | Ação |
|---|---|
| `1` / `2` / `3` | Preset de enquadramento: Esquerda / Centro / Direita |
| `←` `→` | Pan (deslocamento horizontal contínuo) |
| `↑` `↓` | Tilt (deslocamento vertical contínuo) |
| `+` / `-` | Zoom in / out |
| `q` | Sair |

Todos os controles também têm botão correspondente na TUI. Mudanças de enquadramento (preset, pan, tilt, zoom) são aplicadas com uma transição suave (~300ms), não em corte seco.

## Rodando os testes

```bash
python -m pytest -q
```

## Gerando executável

Para distribuir o FakePTZ em outra máquina Windows sem instalar Python nem as dependências:

```bash
pip install -r requirements-dev.txt
pyinstaller --name FakePTZ --console main.py
```

Isso gera a pasta `dist/FakePTZ/` com `FakePTZ.exe` e as DLLs necessárias — copie a pasta inteira para a máquina de destino e rode o `.exe` de dentro dela.

O executável **não** inclui nem instala o driver de câmera virtual — isso continua sendo um pré-requisito separado em cada máquina de destino, veja [`docs/setup-virtual-camera.md`](docs/setup-virtual-camera.md). A câmera de captura usada também continua fixa no índice 0 (sem opção de escolher outra na TUI/CLI).

## Estrutura do projeto

```
fakeptz/
  config.py   # constantes e a matemática pura de crop (zoom/pan/tilt)
  video.py    # pipeline de captura/processamento/envio de frames
  app.py      # TUI (Textual)
tests/        # testes automatizados (pytest)
docs/         # documentação complementar (setup da câmera virtual, roadmap)
main.py       # ponto de entrada
```

## Documentação adicional

- [`docs/setup-virtual-camera.md`](docs/setup-virtual-camera.md) — instalação e registro do driver de câmera virtual.
- [`docs/plano-de-evolucao-ptz.md`](docs/plano-de-evolucao-ptz.md) — roadmap de evolução (PTZ real, presets, face tracking).
- [`Especificação Técnica (SRS_SDD).md`](<Especificação Técnica (SRS_SDD).md>) — requisitos funcionais e não-funcionais do projeto.
