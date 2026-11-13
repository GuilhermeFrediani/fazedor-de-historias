# RELATÓRIO A/B — VEDA SPARSE (T1 executado sob autorização T0) — 19/10/2026

## RESULTADO: REJEITADO NESTA CONFIGURAÇÃO (mecanismo suportado) • INCONCLUSIVO quanto ao ganho

O kernel Veda **não roda** no WanGP desta máquina pelo mecanismo oficialmente suportado:
o seletor de modos de atenção do WanGP exclui explicitamente HIP/ROCm. O braço B não
gerou vídeo (falha ruidosa e correta — sem fallback silencioso para SDPA, exatamente
como o upstream projeta: "never silently off").

## 1. Estado inicial e integridade (verificado antes e depois)

| Arquivo | Hash antes | Hash depois |
|---|---|---|
| `gen_test.py` (harness) | F1A2E714… | alterado POR AUTORIZAÇÃO IMPLÍCITA DO TESTE: correção do filtro de log (ver §2) — backup `LOGS\gen_test.py.pre_VEDA_AB.backup` |
| `wgp_config.json` | 7862EFD1… | **7862EFD1… INALTERADO** (strict mantido) |
| `sparse_int8.py` | F52FD796… | **F52FD796… INALTERADO** (nenhum patch aplicado) |
| Vídeos T1/T2/T3/P3 | no manifesto | intactos |

## 2. Correção do próprio harness (documentada, testada, com backup)

**Diff** (`ev_stream`): o filtro anti-eco da missão noturna descartava TODO evento
`[stdout]` — o que apagaria o print de ativação do Veda (nossa prova de kernel).
Correção: bloquear apenas cadeias aninhadas (`[stream]` ou múltiplos `[stdout]`);
adicionar "veda/attention/sparse" aos marcadores. Testes: `test_filtro_veda.py`
**6/6 PASS** (print do Veda capturado; ecos bloqueados) + watchdog **23/23 PASS** +
compilação OK. Efeito: só logging; geração idêntica.

## 3. Configurações A e B efetivamente utilizadas

| | A (baseline) | B (Veda) |
|---|---|---|
| settings | `test1_settings.json` (produção, byte-idêntico) | `test1_veda_settings.json` — **diff verificado: exatamente 2 chaves** (`model_type`→veda, `output_filename`) |
| execução | completa ( vídeo `teste_01(2).mp4`) | **abortada pelo próprio WanGP na carga** (22,9 s) |

## 4. Evidências do que aconteceu no braço B

1. Evento `info` nos logs (a mensagem decisiva, capturada pelo filtro corrigido):
   > "You have selected attention mode 'veda'. However it is **not installed or supported on your system**. You should either install it or switch to the default 'sdpa' attention."
2. `GenerationResult(success=True, **generated_files=[]**)` — nenhum vídeo; tarefa encerrada sem output.
3. **Causa raiz (código-fonte), `shared/attention.py:35-38`:**
   ```python
   ATTENTION_MODE_AVAILABILITY = {
       ...
       "veda": {
           "installed": triton_installed,
           "supported": triton_installed and major >= 8 and not torch.version.hip,  # ← EXCLUI AMD/ROCm
       },
   }
   ```
   No nosso ambiente `torch.version.hip = "7.15.26333"` → `supported=False` → recusa.
4. **Nenhum print de ativação** `[MiniMax H3] Veda Triton Attention…` (o `begin_forward`
   do kernel nunca foi chamado) — corroborado pela duração de 22,9 s.
5. Predictor **baixado** durante a carga do modelo (267,7 MB — dentro da autorização;
   apagável no rollback; o bf16 NÃO baixou).

## 5. Errata do P4 (correção honesta do meu relatório anterior)

O P4 classificou o gate como "CONFIRMADO (passa numericamente)" olhando o código do
KERNEL (`veda/attention.py:131`, capability 12≥8). **Incompleto**: o gate do SELETOR
(`shared/attention.py:37`) vem antes e exige `not torch.version.hip` — exclusivo
NVIDIA. O rótulo do handler ("Triton, NVIDIA SM80+") era fiel ao gate real; o upstream
suporta RDNA3/4 (e validou o kernel na nossa GPU), mas a INTEGRAÇÃO WanGP restringiu a
disponibilidade a NVIDIA. Consequência para as projeções: os cenários "Veda strict/patch"
do P4 (5,4–6,7 h para 5 min) ficam **condicionados a um patch de disponibilidade** —
não alcançáveis por configuração.

## 6. Braço A (medição válida do baseline de hoje)

| Métrica | Valor |
|---|---|
| Total | **837,0 s** (T1: 846 s • P3: 836,4 s — consistente) |
| Difusão | ~681 s (idêntica a T1/P3 dentro do ruído) |
| Vídeo | `teste_01(2).mp4` — íntegro, decodifica sem erros |
| Watchdog | 0 eventos |
| Memória | pico reservada ~7,9-8,8 GB; margem commit ≥ ~22 GB |

O A serve de baseline intrassessão para qualquer teste futuro do Veda (passo-âncora
~170 s @ 45k tokens). **Comparação de ganho A×B: impossível — B não executou.**

## 7. Classificação (critérios da Fase T3)

| Categoria | Veredito |
|---|---|
| APROVADO COM STRICT | ✗ — kernel nunca rodou |
| PATCH JUSTIFICADO (warps) | ✗ — moot: nem a seleção é possível |
| **REJEITADO NESTA CONFIGURAÇÃO** | ✓ **(mecanismo suportado recusa AMD)** |
| INCONCLUSIVO (ganho) | ✓ — nenhuma medição de desempenho foi possível |

## 8. Estado final e rollback

- Pipeline de produção: **INTACTO** (A prova: 837 s consistentes; hashes conferidos).
- `wgp_config.json` / `sparse_int8.py` / watchdog v2: inalterados.
- Itens novos (todos reversíveis): `test1_veda_settings.json` (arquivo), predictor
  267,7 MB (apagável), vídeo A do dia (`LOGS\VEDA_A_baseline_video.mp4`), correção do
  filtro do harness (mantida — corrige um defeito de logging de qualquer teste futuro).
- Rollback completo: apagar settings veda + predictor; restaurar gen_test.py do backup
  se desejar (não recomendado — o filtro corrigido é melhor).

## 9. Caminhos possíveis (todos exigem sua decisão explícita)

| Opção | O que seria | Custo | Risco |
|---|---|---|---|
| **(a) Aceitar o veredito e seguir sem Veda** | Pipeline atual (medido: ~90 s/s de vídeo) | zero | zero — Piloto B no cenário [M] 6,9 h de geração 1ª passada |
| **(b) Patch de DISPONIBILIDADE** (novo; ≠ patch de warps) | `shared/attention.py:37`: remover `and not torch.version.hip` (1 linha) | backup+diff+re-teste B (~30 min) | Médio-alto: liberar o modo não garante que o kernel compila no nosso triton 3.7.1 (upstream validou no 3.8.0); se compilar, ainda faltaria o patch de WARPS (2º patch) para o ganho pleno |
| (c) Upstream/issue | Reportar ao WanGP (o upstream Veda suporta RDNA4 documentadamente) | espera por terceiros | baixo |

**Recomendação:** manter o pipeline como está (**a**) e iniciar o Piloto B pelos gates
criativos (sua leitura do roteiro + stills G1). O Veda só voltaria ao radar com a
combinação (b)+warps validada — uma decisão de risco, não de configuração.

## 10. Fatos × hipóteses × projeções (deste relatório)

- **Fatos:** eventos B + linha de código 37 + predictor 267,7 MB + A 837,0 s íntegro +
  hashes inalterados + filtro 6/6 + watchdog 23/23.
- **Hipótese:** com patch de disponibilidade, o kernel compilaria no triton 3.7.1
  (não verificada — nunca testada).
- **Projeções:** os cenários de tempo do P4 com Veda permanecem TEÓRICOS e agora
  condicionais ao patch; a única linha de tempo COMPROVADA para o Piloto B é a [M].
