# Plano de Evolução: FakePTZ → PTZ real (zoom e controle de cena)

## Contexto

O FakePTZ hoje simula uma câmera PTZ através de **3 posições de crop fixas e discretas** (ESQUERDA/CENTRO/DIREITA), trocadas instantaneamente (sem transição), com o mesmo nível de ampliação nas três e sem movimento vertical. Uma câmera PTZ real oferece Pan/Tilt/Zoom **contínuos**, presets memorizáveis, transições suaves e controle granular.

Este documento mapeia o gap funcional, avalia a viabilidade de cada lacuna dentro das restrições de baixo consumo do projeto (RNF-001/002/003: CPU ≤8%, RAM ≤150MB, latência ≤33ms), e propõe uma priorização.

## 1. Lacunas identificadas

| # | Lacuna | Estado atual | PTZ real | Impacto no objetivo |
|---|--------|--------------|----------|---------------------|
| Z1 | Zoom variável | Fixo (crop sempre 2/3 do frame) | Óptico ou digital, contínuo | **Crítico** — metade da identidade "PTZ" |
| P1 | Pan contínuo | 3 posições discretas (saltos) | Movimento fluido em qualquer ângulo | **Crítico** — versatilidade de enquadramento |
| T1 | Tilt (vertical) | Inexistente | Movimento vertical | **Alto** — completa os 3 eixos |
| UX1 | Transições animadas | Corte abrupto, frame a frame | Interpolação suave entre presets | **Médio** — profissionalismo visual |
| UX2 | Presets de cena | Hardcoded (3 modos fixos no código) | Ilimitados, nomeáveis, salvos pelo usuário | **Médio-Alto** — workflows multi-câmera |
| UX3 | Granularidade de controle | 3 opções | Grid ou joystick analógico | **Médio** — depende do fluxo de uso |
| UX4 | Feedback visual | Só o modo ativo em texto | Coordenadas de pan/tilt/zoom no painel | **Baixo-Médio** — UX/debug |
| F1 | Rastreamento automático de rosto | Não existe | Face/pessoa tracking | **Crítico como feature, mas alto risco técnico** |

## 2. Viabilidade técnica por lacuna

### Z1 — Zoom variável (digital)
Reduzir a janela de crop antes do resize final (crop menor = mais zoom).

```python
def crop_coords_for(width, height, mode, zoom_level=1.0):
    crop_h = int(height * 2 / 3 / zoom_level)
    crop_w = int(width * 2 / 3 / zoom_level)
    # ... resto da lógica de centralização
```

**Custo**: negligenciável — mesma quantidade de processamento (janela menor = menos dados), 0ms de latência adicional. **Sem risco de estourar RNFs.**

### P1 — Pan contínuo
Mover o crop horizontalmente via estado `pan_offset_x` (0–100%), atualizado a cada frame a partir de input de teclado/mouse na TUI (Textual já suporta bem captura de setas).

**Custo**: negligenciável (<1% CPU, <1ms/frame) — é só aritmética de offset. **Sem risco.**

### T1 — Tilt (movimento vertical)
Extensão trivial de P1: mesmo mecanismo, eixo Y (`tilt_offset_y`, setas cima/baixo).

**Custo**: idêntico ao pan, reaproveita a lógica. **Sem risco.**

### UX1 — Transições suaves (easing)
Ao trocar de modo/preset, interpolar linearmente as coordenadas de crop ao longo de ~0.3s em vez de saltar direto.

```python
class VideoPipeline:
    def __init__(self):
        self.target_mode = CropMode.CENTRO
        self.current_crop_coords = crop_coords_for(...)
        self.animating = False
        self.animation_duration = 0.3  # segundos

    def process_frame(self, raw_frame):
        if self.target_mode != self.mode:
            self.start_animation(self.target_mode)
        if self.animating:
            self.current_crop_coords = self.interpolate_coords()
        cropped = crop_frame_with_coords(raw_frame, self.current_crop_coords)
        return resize_frame(cropped)
```

**Custo**: muito baixo — lerp é O(1) por frame. **Sem risco.**

### UX2 — Presets configuráveis
Usuário salva/nomeia combinações de (pan, tilt, zoom) em `presets.json` local, carregáveis por hotkey ou menu na TUI.

**Custo**: baixo — I/O de JSON + modal de UI. **Sem risco.**

### UX3 — Granularidade de controle (grid 5×5 ou joystick)
Alternativa/complemento ao pan contínuo puro: grid de 25 posições pré-calculadas, ou captura de input analógico mapeado para coordenadas.

**Custo**: baixo — mapeamento simples. **Sem risco.**

### UX4 — Feedback visual
Widget na TUI mostrando `Zoom: 1.5x | Pan: 60% | Tilt: 40%`, atualizado junto com o FPS já exibido.

**Custo**: negligenciável — só renderização de texto. **Sem risco.**

### F1 — Rastreamento automático de rosto (face tracking)
Detectar o rosto (YOLO nano, MediaPipe, ou Haar Cascade) e mover o crop automaticamente.

**Custo**: **crítico** — viola os RNFs do projeto:
- YOLO nano: ~50–100ms/frame em CPU (estoura RNF-003, latência ≤33ms)
- MediaPipe Lite: ~30–50ms (marginal)
- Haar Cascade: ~10–20ms (mais rápido, menos acurado)
- Modelos leves ainda somam +50–200MB de RAM (pressiona RNF-002, limite de 150MB)
- Estimativa de CPU adicional: 8–15%, sozinho já estouraria RNF-001 (≤8% total)

Mitigação possível (rodar detecção a cada N frames, downsampling do frame antes do detector) reduz CPU mas ainda arrisca violar a latência. **Recomendação: não incluir na v1** — tratar como experimento opcional futuro, com aviso explícito de que não garante os RNFs.

## 3. Priorização (RICE)

| Lacuna | Reach | Impact | Confidence | Effort | RICE | Prioridade |
|---|---|---|---|---|---|---|
| Z1 — Zoom variável | 9 | 10 | 10 | 1 | 90.0 | 🔴 P0 |
| P1 — Pan contínuo | 9 | 10 | 9 | 3 | 27.0 | 🔴 P0 |
| UX1 — Transições suaves | 8 | 7 | 10 | 1 | 56.0 | 🟠 P1 |
| T1 — Tilt | 7 | 8 | 10 | 1.5 | 37.3 | 🟠 P1 |
| UX4 — Feedback visual | 5 | 5 | 10 | 0.5 | 50.0 | 🟡 P2 |
| UX3 — Grid 5×5 / joystick | 7 | 7 | 8 | 1.5 | 26.3 | 🟡 P2 |
| UX2 — Presets | 6 | 7 | 9 | 2 | 18.9 | 🟡 P2 |
| F1 — Face tracking | 9 | 10 | 5 | 5 | 9.0 | 🔵 Não priorizado |

## 4. Roadmap recomendado

### Fase 1 — Quick wins (1–2 sprints)
Entrega: **"FakePTZ v1.1 — Pan/Tilt/Zoom contínuo + transições suaves"**

1. Zoom digital + pan contínuo (implementar juntos, mesma frente de trabalho)
2. Tilt (extensão imediata do pan)
3. Transições suaves (polish de UX, mata o "corte seco" digital)

Viabilidade técnica: 100%. Impacto no objetivo: crítico. Risco de estourar RNF: nenhum.

### Fase 2 — Profissionalização (2–3 sprints depois)
Entrega: **"FakePTZ v1.2 — Presets + grid de posições + monitoração"**

1. Feedback visual (painel com zoom/pan/tilt atuais)
2. Presets configuráveis (JSON + modal na TUI)
3. Granularidade de controle (grid 5×5 ou joystick, se o pan contínuo puro for difícil de operar via teclado)

### Fase 3+ — Inovação (avaliar só depois de validar Fases 1 e 2)
1. Face tracking — manter como feature experimental/opcional, fora do escopo padrão, só se houver demanda explícita e disposição para relaxar os RNFs (ou um modo "degradado" separado).

## 5. Riscos e trade-offs a mitigar

| Decisão | Risco | Mitigação |
|---|---|---|
| Pan/tilt contínuo sem limites | Crop pode sair dos limites do frame (área preta na imagem) | Clampar coordenadas aos limites do frame |
| Zoom muito alto (ex: 10x) | Perda de qualidade (crop pequeno + resize grande = imagem borrada) | Documentar/limitar teto recomendado (ex: 1x–3x) |
| Face tracking em CPU limitada | App fica lento/inutilizável | Se implementado no futuro, fallback automático que desativa o tracking se CPU > limite |
| Presets em JSON local | Sem backup/sincronização entre máquinas | Documentar como local-only; sync fica fora de escopo por ora |
| Transições suaves | Duração longa demais pode parecer "lenta" | Default de 300ms, com possibilidade de ajuste futuro |

## 6. Métricas de sucesso pós Fase 1

- Taxa de uso de zoom vs pan vs tilt (qual feature é mais acionada)
- Bugs relacionados a boundary conditions (crop fora dos limites, travamentos)
- CPU% e latência reais em diferentes resoluções de webcam (480p/720p/1080p)
- Feedback qualitativo: "parece mais natural agora?"

## 7. Conclusão

**Prioridade imediata**: Fase 1 (zoom + pan/tilt contínuo + transições suaves) — viabilidade técnica total, impacto crítico no objetivo do produto, esforço baixo, risco zero de estourar os requisitos não-funcionais que motivaram o projeto.

**Fora de escopo por ora**: rastreamento automático de rosto — tecnicamente viável, mas conflita diretamente com a razão de existir do FakePTZ (rodar leve o suficiente para não competir com o Zoom por CPU/GPU).
