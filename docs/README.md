# PROJETO MINIMAX H3 RECUPERADO — Resultados da Missão Noturna

**Data:** 18/10/2026
**Objetivo:** reconstruir o ambiente pós-formatação (Pinokio + Wan2GP + MiniMax H3),
validar o modelo H3 FL2VA com áudio integrado e entregar 3 vídeos de teste progressivos.

## Estado final (resumo executivo — atualizado 18/10/2026, pós-3 testes)

- **Ambiente: 100% RECONSTRUÍDO E VALIDADO** — Pinokio 8.2.0 (última) + WanGP v18.17
  (commit fde3c7e) + Python 3.12.13 + PyTorch 2.13.0+rocm10.0.0 (TheRock, gfx1200) +
  Triton 3.7.1.post27. RX 9060 XT operacional.
- **Wan2GP: FUNCIONANDO** via Pinokio (UI Gradio online).
- **✅ OS 3 TESTES DE VÍDEO FORAM CONCLUÍDOS COM VÍDEOS VÁLIDOS:**
  - `TESTE_01\teste_01.mp4` — 10,125 s (janela única; 14 min de geração)
  - `TESTE_02\teste_02.mp4` — 12,25 s (janela única + corte narrativo; 18,5 min)
  - `TESTE_03\teste_03_FINAL_18s.mp4` — **18,79 s com 2 janelas emendadas** (31 min;
    checkpoint da janela 1 e parcial da tentativa falha preservados)
- **Desbloqueios desta sessão:** pagefile fixo 32 GB (commit 18,04→47,16 GB medidos;
  rollback documentado) + correção do bug AMD de dispatch (`kernel_precision:"strict"`).
- **Pendências:** sua análise visual/sonora dos 3 vídeos (frames + folhas de contato prontos
  em cada TESTE_NN\ANALISE\ — este agente não processa imagens); watchdog de VRAM a estender.
- **Computador LIGADO** (não desligar antes de sua confirmação, conforme instrução).

> **LEIA PRIMEIRO:** RELATORIO_FINAL.md (visão completa) e PROXIMOS_PASSOS.md
> (o que falta e como destravar em 1 minuto).

## Estrutura desta pasta

| Arquivo/pasta | Conteúdo |
|---|---|
| **RELATORIO_FINAL.md** | **Relatório final completo (seção 16 da missão)** |
| DIAGNOSTICO_INICIAL.md | Fase A: hardware, software, busca pelo print antigo (não encontrado) |
| AMBIENTE_E_VERSOES.md | Pesquisa de versões + decisão de instalação (evidências) |
| CONFIGURACAO_VALIDADA.md | Config de referência × v18.17 + config efetiva dos testes |
| HISTORICO_TESTES.md | **Bloqueio formal**: os 9 experimentos medidos e o diagnóstico |
| PENDENCIAS_E_RISCOS.md | Riscos, bloqueios e decisões que dependem do usuário |
| PROXIMOS_PASSOS.md | **Runbook: como destravar (pagefile) e completar os 3 testes** |
| TESTE_01\, TESTE_02\, TESTE_03\ | (Vazias — testes bloqueados; serão preenchidas pós-desbloqueio) |
| FRAMES_ANALISE\ | (Vazia — sem vídeos para analisar ainda) |
| LOGS\ | Logs, telemetria completa, patches c/ diffs, backups, incidentes |
| MANIFEST_SHA256.txt | Hashes de todos os arquivos desta pasta |

## Caminhos-chave do ambiente

- Pinokio home: `C:\pinokio` (apps em `C:\pinokio\api\<nome>`)
- Wan2GP app: `C:\pinokio\api\wan2gp-amd\app` (modelos em `app\ckpts\`)
- Ambiente Python: `C:\pinokio\api\wan2gp-amd\app\env` (Python 3.12.13)
- UI do WanGP: iniciar pelo Pinokio (botão Start) → `http://127.0.0.1:<porta>/`
- Scripts de automação desta missão: `C:\Users\Guilherme\Documents\Projeto Padrão`

## Alterações de código de terceiros (com backup + diff)

Ver LOGS\PATCHES_DIFF.md — 3 patches no script wan2gp-amd (Python 3.12, índice PyTorch
estável gfx1200, remoção do pin numpy quebrado). Originais em LOGS\*.orig.backup.
Nenhuma alteração no código do WanGP em si (deepbeepmeep/Wan2GP).
