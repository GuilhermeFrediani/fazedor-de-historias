# CHANGELOG v4 — do "renderizável" ao "engraçado"

Data: 13/11/2026 · base: v3 (commit do repo público)

## Motivo

A fumaça v3 (`operacao_ralo_exato_v3_fumaca_6clipes.mp4`, 60,8 s) ficou tecnicamente
correta e sem graça. Medi o arquivo para achar a causa em vez de opinar:

| Medida | v3 |
|---|---|
| planos por clipe | 1 (fixo) em 6 de 6 |
| ar morto (bonecos plantados) | ~24 s de 60 s |
| áudio médio / pico | −38,5 dB / −7,3 dB |
| trilha musical | nenhuma |
| cliente militar em cena | 4 s, só no último clipe |

Conclusão: **não era problema de piada escrita, era problema de montagem.** A v3
otimizou contra o riso em três pontos: pediu "reação seca" (invisível em plano geral),
zerou os murmúrios (matou o som de boca) e escreveu a ação num parágrafo único (o modelo
gasta a atenção num movimento e nunca recebe ordem de cortar).

## Mudanças

### `regras_v4.py` (novo)
- `PROMPT_MESTRE_V4` com três camadas obrigatórias: RENDERIZÁVEL → ENGRAÇADO → EDITÁVEL.
- **LEI DO CORTE**: 2–3 planos por clipe, com hora de corte no formato oficial do H3
  (`[Shot 2] At 00:03.500, the camera cuts to ...`). Estrutura fixa de 10 s:
  inserto (0–3,5) → plano geral de ação (3,5–7) → close de reação (7–10).
- **LEI DO CORPO INTEIRO**: reação de meia-linha do corpo (coluna, ombros, joelhos, mãos),
  mínimo 2 s em close. Proíbe "olham um para o outro".
- **LEI DO SOM**: 4–6 eventos concretos (material + verbo + intensidade) + 2 sons de boca
  por clipe. Proíbe hum/drone/buzz.
- **LEI DO AR MORTO**: nenhum plano descreve alguém parado; o clipe termina em movimento.
- **CLIENTE ABRE E FECHA**: aparece no 1º e no último clipe (a assinatura da série — a nota
  fiscal — existia no dossiê v3 e não existia na tela).
- **NEGATIVOS APOSENTADOS**: `NEGATIVOS_APOSENTADOS` registra a lista retirada. Em cfg 1
  não há ramo negativo, e a lista entra como conceito (foi o que trouxe contorno de cartoon).
- **MÚSICA OBRIGATÓRIA**: `non_diegetic_music` com instrumento **e** ritmo + parada seca
  no impacto.
- `TEO_CURTO` / `JUCA_CURTO`: âncoras de identidade em ~30 palavras (antes ~1.900).
- `montar_prompt_v4()`: monta no formato oficial `integrated_multimodal_description` com
  os cortes datados, `overall_soundscape` e `non_diegetic_music`. Saída 2.100–2.450 chars.
- `validar_montagem()`: validador novo — reprova plano único, reação sem corpo, soundscape
  sem som de boca, cena sem objeto de gag, cliente fora das pontas, negativo reintroduzido.

### `pipeline/pos_producao.py` (novo)
A camada que nenhum prompt resolve: `freezedetect` para achar ar morto, `volumedetect`
para medir, `loudnorm` para −14 LUFS, corte do rabo morto, punch-in de 1,25× no meio de
cada clipe (corte seco sem regerar), cama musical a −26 dB, concat com `+faststart`.
`--analisar` só mede. Custo: ~40 s de CPU, 0 GPU.

### `fazedor_app/fazedor_app.py`
- prompt mestre → `regras_v4.PROMPT_MESTRE_V4`
- montagem → `regras_v4.montar_prompt_v4`
- `_com_action()`: deriva o campo `action` do **plano do meio** (o de ação) para os
  checadores de física da v3 medirem UM movimento, não a soma dos três planos.
- `validar_dossie()` agora compõe `0,30 humor + 0,35 render + 0,35 montage` (era
  `0,35/0,65`, que dava 9,0/10 para um slideshow).
- Três regras da v2 aposentadas quando o episódio tem `planos`: trilha obrigatória
  (não `N/A`), `beats` 3–4, e ação de 300–900 chars.

### `fazedor_app/aplicar_v4.py` (novo)
Patch idempotente; grava `fazedor_app.py.v3.bak` antes de mexer.

### `fazedor_app/fumaca_v4.py` (novo)
Os 6 clipes de OPERAÇÃO RALO EXATO reescritos em 3 planos, com som de boca, música e
continuidade explícita (telefone no chão, grelha plantada no 1 e paga no 2, buraco aberto
do 2 ao 5, água crescendo seco→molhado→alagado, cliente na cortina no 1 e no 6).

### `DOSSIE_v4.md`, `LEIA_PRIMEIRO_v4.txt`, `CHECKLIST_QUALIDADE.md`

## Resultado do teste seco (`python fumaca_v4.py --seco`)

```
NOTA: 9.3/10  · humor 9 · render 10 · montage 10
ok - corte datado dentro de todos os clipes
ok - reacao de corpo inteiro em todos
ok - som com corpo e som de boca
ok - objeto de gag nomeado
ok - cliente abre e fecha o episodio
ok - orçamento de física / objeto móvel / dois corpos / estado emendado / física possível
0 erro(s)
6 settings escritos · prompts 2.202–2.395 chars · 3 planos cada
```

## Custo

| | v3 | v4 |
|---|---|---|
| fumaça 6 clipes | ~90 min GPU | ~90 min GPU (idêntico) |
| episódio 30 clipes | ~7,3 h | ~7,3 h |
| pós-produção | 0 | ~40 s CPU |
| validação | `--seco` | `--seco` (0 GPU) |

Nenhum render extra foi disparado nesta versão.
