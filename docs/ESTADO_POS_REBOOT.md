# ESTADO PÓS-REBOOT — Missão de Recuperação (Teste 1)

**Criado em:** 18/10/2026 12:45 (antes do reinício autorizado)

## O que foi feito (evidências em LOGS\PAGEFILE_APLICACAO.log)

1. Pagefile fixo **32 GB** aplicado (elevado, UAC aprovado por você):
   - `AutomaticManagedPagefile: false`
   - `C:\pagefile.sys: Initial=32768, Maximum=32768` (verificado no registro: `PagingFiles: C:\pagefile.sys 32768 32768`)
   - **Rollback documentado**: LOGS\ROLLBACK_PAGEFILE.txt (retornar ao automático com 1 comando)
2. Medição honesta pré-reboot: limite de commit **continua 18,04 GB** — o novo valor
   só entra em vigor após o reinício (esperado: **~48 GB**; a medir, sem presunção).
3. **RunOnce registrado**: no próximo logon, o Teste 1 inicia sozinho após 90 s
   (wrapper com marcador anti-execução-dupla; o watchdog de margem ≥ 5 GB está embutido
   no gen_test.py e continua protegendo a geração).
   - Saída: `Temp\opencode\TESTE_01_*.{jsonl,csv,json}` + `TESTE_01_STARTED.txt`
4. Reinício solicitado: `shutdown /r /t 30` (sem forçar encerramentos).

## Ao retomar a sessão (agente ou você), verificar NA ORDEM:

1. `Temp\opencode\TESTE_01_STARTED.txt` → existe? com "finalizado"? (teste auto já rodou)
2. `Temp\opencode\TESTE_01_summary.json` → success? generated_files?
3. Limite de commit: `Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory` (esperado ~48 GB)
4. Se o teste auto já tiver concluído → analisar vídeo (analyze_video.py) e completar a
   entrega em TESTE_01\; se ainda estiver rodando → monitorar sem iniciar outro; se não
   rodou → executar manualmente:
   `& "C:\pinokio\api\wan2gp-amd\app\env\Scripts\python.exe" gen_test.py --settings test1_settings.json --tag TESTE_01`
   (a partir de `Temp\opencode`, que tem as cópias; ou do workspace "Documents\Projeto Padrão")

## Configuração efetiva do Teste 1 (inalterada da missão noturna)

Profile 5 • encoder GGUF Q4_K_M • sem preload manual • SDPA • Spectrum on •
LoRA turbo Lightx2v FL2V 8-step v1.0 @1.0 • 6 passos • guidance 1 • flow_shift 12 •
1152×640 @ 24 fps • 10 s • seed 7001 • prompt oficial pt-BR (fala intacta, bytes verificados).

## Critérios de parada vigentes (inalterados)

Margem de commit < 5 GB (watchdog, 2 amostras) • VRAM reservada > 15 GB • driver free ~0 •
falhas HIP/ROCm/NaN • lentidão anormal persistente. Sem retry automático. Sem segundo
teste simultâneo. NÃO desligar o computador nesta etapa.
