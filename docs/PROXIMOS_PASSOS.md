# PRÓXIMOS PASSOS — Após os 3 testes concluídos (18/10/2026)

## O que foi alcançado nesta sessão

1. **Pagefile fixo 32 GB aplicado** (autorizado; rollback em LOGS\ROLLBACK_PAGEFILE.txt)
   → limite de commit 18,04 → **47,16 GB** medidos.
2. **3 vídeos válidos gerados** (mesma config/seed 7001): 10,125 s / 12,25 s / **18,79 s
   com 2 janelas emendadas** — todos íntegros, H.264/AAC, fala pt-BR no meio, margem de
   commit sempre ≥ 9,3 GB.
3. **Bug AMD corrigido**: `kernel_precision:"strict"` (kernel CUTLASS CUDA-only no VAE
   encode do overlap; ver TESTE_03\RELATORIO_TESTE_03_TENTATIVA1_FALHA.md + PATCHES_DIFF.md).

## Suas pendências (avaliação subjetiva — este agente não processa imagens/áudio)

1. Assistir aos 3 vídeos e verificar: personagem consistente, anatomia/mãos, sincronia
   labial, fala inteligível em pt-BR, **emenda das janelas em ~15 s no Teste 3** (frames
   extras ao redor da emenda em TESTE_03\ANALISE\).
2. Aprovar (ou não) a base de configuração para a produção.

## Passos técnicos futuros (na ordem recomendada)

1. **Watchdog de VRAM** (correção minha pendente): estender gen_test.py para abortar
   também em VRAM reservada > 15 GB e driver free ~0 (critérios da missão que não estavam
   automatizados — a ultrapassagem transitória do Teste 3 está documentada).
2. **Testar RIFE ×2** (24→48 fps) como pós-processamento sobre um vídeo aprovado
   (temporal_upsampling — nunca sobre o original antes de avaliá-lo).
3. **Teste de duração intermediária** (30–60 s) antes de atacar 5 minutos — valida o
   comportamento com mais emendas e o acúmulo de checkpoints por janela.
4. **Encoder Quanto INT8** (mais rápido: encode ~3–4 it/s vs 1 do GGUF) agora que há
   margem de commit — testar comparativamente a qualidade.

## Extrapolação CAUTELA para 5 minutos (dados medidos; 3 testes não validam geração longa)

Medido: 83,6 s de geração por s de vídeo (10 s) → 90,6 (12 s) → 99,3 (18,79 s, 2 janelas).
O custo cresce porque cada janela processa 362 frames para adicionar ~89 únicos (overlap).

Para 300 s (5 min, ~7.200 frames): ≈ **21 janelas** × ~11–17 min/janela (difusão + decode
+ encode do overlap) ≈ **4–6 horas de difusão** + saves/checkpoints → estimativa total
**~5 a 7,5 horas** — dentro da janela de 6–8 h desejada, mas **NÃO COMPROVADO**: riscos
acima dos testados incluem acúmulo de checkpoints em disco, desgaste de margem em janelas
sucessivas e deriva de consistência após muitas emendas. O teste de 30–60 s (passo 3)
reduz essa incerteza antes do compromisso completo.

## Comandos prontos (nada baixa de novo; modelos todos locais)

```
cd "C:\Users\Guilherme\Documents\Projeto Padrão"
& "C:\pinokio\api\wan2gp-amd\app\env\Scripts\python.exe" gen_test.py --settings testN_settings.json --tag TESTE_NN
# pós-teste:
& "C:\pinokio\api\wan2gp-amd\app\env\Scripts\python.exe" analyze_video.py <video> <pasta> --times <s>
```
