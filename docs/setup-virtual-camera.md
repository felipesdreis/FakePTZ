# Setup: câmera virtual "virtual_cam_ptz" (Unity Capture)

O FakePTZ espera encontrar uma câmera virtual chamada exatamente **`virtual_cam_ptz`** (constante `VIRTUAL_CAM_DEVICE` em `fakeptz/config.py`). Se o dispositivo com esse nome não existir no Windows, `pyvirtualcam.Camera(...)` falha, o pipeline entra em `status="ERRO"` e a TUI encerra com segurança (RNF-004).

## Por que Unity Capture, e não OBS Virtual Camera

O backend **OBS** do `pyvirtualcam` sempre registra o dispositivo com o nome fixo `OBS Virtual Camera` — não dá pra renomear. O backend **Unity Capture** permite registrar o filtro com um nome customizado, então é o que usamos para ter `virtual_cam_ptz` na lista de câmeras do Windows/Zoom.

## Pré-requisitos

- Windows (o filtro é um DirectShow COM DLL, 32 e 64 bits).
- Privilégios de Administrador (o instalador pede elevação via UAC).

## Passo a passo

Já deixei o repositório baixado e extraído em `C:\Tools\UnityCapture\` — é um local permanente, então não precisa (e não deve) mover essa pasta depois: `regsvr32` registra o **caminho absoluto** do DLL, e mover/apagar a pasta quebra a câmera depois de instalada.

1. Abra `C:\Tools\UnityCapture\Install` no Explorer.
2. Registre o filtro com o nome customizado. Duas formas equivalentes:

   **Opção A — clique duplo:**
   - Clique com o botão direito em `InstallCustomName.bat` → "Executar como administrador".
   - Confirme o UAC.
   - Quando pedir o nome (`Enter a custom filter name to register as (default is 'Unity Video Capture')`), digite exatamente:
     ```
     virtual_cam_ptz
     ```
   - Pressione Enter. Deve aparecer uma confirmação de `DllRegisterServer succeeded` para os dois DLLs (32 e 64 bits).

   **Opção B — terminal elevado (evita digitação manual/erro de digitação):**
   - Abra um Prompt de Comando ou PowerShell como Administrador.
   - `cd C:\Tools\UnityCapture\Install`
   - Rode:
     ```
     regsvr32 "UnityCaptureFilter32.dll" "/i:UnityCaptureName=virtual_cam_ptz"
     regsvr32 "UnityCaptureFilter64.dll" "/i:UnityCaptureName=virtual_cam_ptz"
     ```

## Verificação

- Abra o app "Câmera" do Windows, o OBS (Fontes → Dispositivo de Captura de Vídeo) ou o seletor de câmera do Zoom, e confirme que **`virtual_cam_ptz`** aparece na lista (ela só mostra imagem quando o FakePTZ estiver rodando e enviando frames).
- Rode `python main.py` no FakePTZ — se o nome não bater exatamente (case-sensitive, sem espaços extras), o pipeline mostra `Câmera virtual indisponível: ...` no painel e encerra.

## Desinstalar

Na mesma pasta `Install`, rode `Uninstall.bat` como Administrador (ou `regsvr32 /u` nos dois DLLs) para remover o filtro do sistema.

## Observação

Ter o OBS Virtual Camera instalado ao mesmo tempo não causa conflito — o `pyvirtualcam` só usa o backend cujo dispositivo tem o nome configurado (`virtual_cam_ptz`), então o backend OBS simplesmente falha a checagem de nome e é ignorado.
