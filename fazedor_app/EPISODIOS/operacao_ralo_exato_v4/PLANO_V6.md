# PLANO v6 — fechar continuidade ≥8 (o resíduo do v5)

## Diagnóstico v5 (medido)
- causalidade_narrativa: **8/10** ✅ (portão da causalidade aberto)
- continuidade_visual: **6/10** ❌ — resíduo = drift de SET intra-clipe
  (teto vira céu 51–56 s; rolo de papel, pedal, extintor, saco entram sem plantio)
- causa raiz: cadeia pixel pina só o 1º frame; o modelo re-imagina o cenário
  nos frames seguintes. NÃO é mais problema de edição de keyframe (image_end
  já estava morto na cadeia v2 — pivô 5c22ae1).

## O que já foi implementado (0 GPU) — commit desta fase
1. **Registro de props no gate de âncora** (`qc_visao.py --props`):
   - PROVADO: âncora do c04 REPROVADA citando `telephone, tape measure,
     control panel` (o telefone pendurado = drift real apontado no resumo).
   - PROVADO: âncora limpa do c05 APROVADA (todos objetos casaram com registro).
   - lição: a lista deve cobrir TODO o cenário fixo, senão falso positivo
     (painel/gauges entraram no registro após o teste).
2. **PROPS completo em cadeia_v2.py** (plantados + cenário fixo; extintor,
   rolo de papel e urso ficam deliberadamente FORA — se o modelo pintar, cai).

## Plano de render v6 (ControlNet-Union "set-plate")
- Arquitetura: âncora → **plate** → clipe.
  - `plate` = 1 clipe de 5 s renderizado DO anchor frame (bonecos parados,
    câmera lenta) — é a "placa de set" com teto/paredes/piso congelados.
  - cada clipe do episódio = `minimax_h3_control_pruned` com
    `video_guide` = plate, `video_prompt_type: "SV"` (soft shapes) e
    `control_net_weight ~0.4`, MAIS `image_start` = âncora (que casa com o
    plate por construção — handler exige que âncoras casem com o controle).
  - o prompt dirige a ação; o plate segura a arquitetura do set em TODOS os
    frames (mata o teto-vira-céu).
- Custo: download do módulo Control-Union (uma vez) + plate ~7 min +
  6 clipes ~18–22 min cada (overhead do controle) ≈ **2,0–2,3 h GPU**.
- Fallback por clipe: se o gate reprovar 3× com controle, renderiza o clipe
  sem controle (caminho atual) e o gate de props decide.

## Correções de texto junto (sem GPU)
- Cliente MILITAR aparece na CHEGADA (canon: abre e fecha) — reforçar
  visibilidade no estado/ação do c02 (o v5 pode não tê-lo mostrado claro).
- Conexões presas/soltas (gancho→barril) entram no estado como qualquer prop.
- Trim de ar morto por PLANO no pos_producao (freezedetect intra-clipe).

## Portão para 300 s
2 episódios de 60 s seguidos com continuidade ≥8 E causalidade ≥8.
