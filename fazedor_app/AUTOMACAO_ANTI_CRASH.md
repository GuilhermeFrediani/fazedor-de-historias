# Automação anti-crash do render — diagnóstico e plano

## 1. Incidente de 26/11/2026

| Hora | Evento |
|---|---|
| 11:15 | app `fazedor_app.py` e geração do episódio |
| 11:34:47 | **START** do render (âncora + 6 clipes, 8 steps/1152×640) |
| 11:40 | âncora aprovada (6,2 min) |
| 12:00 | c01 renderizado (16,2 min); gate reprovou; fallback |
| 12:29 | c02 renderizado (16,2 min); gate em andamento |
| ~12:35 | **queda**: app + render morreram juntos; log para no gate do c02 |
| 13:15:10 | retomada destacada, ancorada no c02; c03–c06 |
| 14:53:09 | `SMOKE60.mp4` montado, 61,8 s, 31,8 MB |
| 15:00 | supervisor anexado detecta o final |

**Tempo total:** 3h18min22s (11:34:47 → 14:53:09). **Retomada:** 1h37min59s
(13:15:10 → 14:53:09). O alvo de 1h37 era só render (6 × 16,2 min); gates,
montagem e o crash de 40 min ficaram fora da conta.

**Qualidade:** 0/6 clipes aprovados pelo gate; o final é montagem de 6
fallbacks. c01/c02 têm personagem extra atrás do vidro e props duplicados;
c06 tem ghost/morph e 5 lâmpadas (registro: 3). É entrega de continuidade, não
entrega de qualidade.

## 2. Causas-raiz

1. **Processo preso à sessão do agente.** App e render eram filhos do shell do
   servidor. O restart do servidor matou a árvore inteira; não houve exceção
   Python, o log simplesmente para.
2. **Sem watchdog/heartbeat.** Ninguém detectou a morte; o `smoke_timer.json`
   ficou aberto e o usuário só descobriu 30+ min depois.
3. **Checkpoint tarde demais.** `smoke_bancados.json` só era gravado **depois**
   do gate. O c02 tinha mp4 pronto, mas não estava no banco; um restart
   re-renderizaria 16,2 min.
4. **Gate caro e sem timeout de estágio.** `qc_visao` tenta 2 modelos com
   timeout de 600 s cada, depois Gemini; o smoke ainda repete 15× com sleep de
   120 s. Em indisponibilidade, são 30 min e `SystemExit(7)`.
5. **`subprocess.run` sem timeout.** Um `gen_test.py` ou gate travado pode
   segurar o render para sempre.
6. **Sem lock.** Dois smokes no mesmo episódio podem disputar GPU/banco.
7. **Sem retomada de montagem.** Se o processo morre depois dos 6 clipes e
   antes do `SMOKE60`, não havia um "final-only" idempotente.

## 3. Sistema de emergência implementado

Arquivo: `fazedor_app/render_supervisor.py` (lançador:
`iniciar_supervisor.py`).

### O que ele faz

- **Roda destacado** (`DETACHED_PROCESS`), fora da sessão do servidor.
- **Lock por episódio** (`automation/supervisor.lock`): impede dois supervisores.
- **Monitora PID + atividade real** (mtime de `smoke_run.log`,
  `smoke_resume.log`, `automation/heartbeat.json`).
- **Morte:** se o PID sumiu e o final não existe, recupera o que já foi
  renderizado e reinicia.
- **Hang:** se o PID está vivo mas sem atividade por `--stale-min` (padrão 45),
  mata a árvore (`taskkill /T`) e reinicia.
- **Recuperação sem re-render:** se existe mp4 válido (7,5–12,5 s) de um clipe
  ainda não bancado, extrai o frame 9.9 e grava o clipe no
  `smoke_bancados.json` como fallback recuperado. Foi exatamente o caso do c02.
- **Retomada:** reinicia `smoke_60s.py`; ele pula o banco e continua do
  próximo clipe. Se os 6 já estão bancados e falta o final, ele só monta.
- **Gate indisponível:** detecta `CADEIA PAUSADA` e espera 5 min antes de
  tentar de novo, em vez de queimar render.
- **Limite:** `--max-restarts` (padrão 10). Ao estourar, grava
  `automation/ALERTA.txt` e para — sem loop infinito.
- **Estado observável:** `automation/status.json` com status, PID, restarts,
  última atividade, histórico, vídeo final.
- **Parada limpa:** criar `automation/STOP`; o supervisor mata o render e sai.

### Comandos

```powershell
# produção nova, destacada (não morre com o servidor)
python iniciar_supervisor.py --slug MEU_EPISODIO

# anexar a um render já rodando
python iniciar_supervisor.py --attach-pid 10156 --since "2026-11-26 13:15:10"

# acompanhar
python render_supervisor.py --status
Get-Content EPISODIOS\MEU_EPISODIO\automation\supervisor.log -Tail 50

# parar
New-Item EPISODIOS\MEU_EPISODIO\automation\STOP -ItemType File
```

## 4. Testes

- `python verificar_alinhamento_v6.py` — checagem estática V6 × pipeline (sem API).
- `py_compile` OK; `teste_canon` OK; `benchmark_v6.py --dry` EXIT 0.
- `--once --attach-pid 10156` detectou o final e gravou `status=concluido`.
- Teste de morte real: pendente; fazer em episódio descartável (matar o
  render no c03 e conferir retomada no c04 em < 60 s). Não executar no
  episódio de entrega.

## 5. Implementado no smoke (retomada fina)

1. **Heartbeat atômico** — `smoke_60s.py` grava
   `EPISODIOS/<slug>/automation/heartbeat.json` a cada fase (iniciando, ancora,
   cXX_inicio, cXX_aprovado/fallback, montagem, concluido). O supervisor usa
   esse arquivo como sinal de vida, além do mtime dos logs.
2. **Checkpoint bruto antes do gate** — `refs/raw_cXX.json` guarda
   `{mp4, seed, dur}`. Se o processo morrer no gate, o restart **re-gateia** o
   mp4 em vez de re-renderizar 16,2 min; o arquivo é removido após decisão.
3. **Timeout de render** — `gen_test.py` tem teto de 35 min; `TimeoutExpired`
   vira tentativa falha e o supervisor mata órfãos/GPU antes de reiniciar.
4. **Recuperação de clipes já renderizados e não bancados** — mantida no
   supervisor (foi o caso do c02 no incidente).

## 6. Ainda pendente (próximos testes)

1. **Gate com backoff exponencial** e fallback controlado sem 15×120 s.
2. **Montagem idempotente `--final-only`:** se o banco tem 6/6 e falta o
   final, não reabrir GPU (hoje o restart já pula os 6 e só monta).
3. **Windows Scheduled Task** no logon para subir o supervisor; ele já
   sobrevive ao restart do servidor, mas não a um reboot.
4. **Qualidade:** corrigir o set do episódio (vidro que gera atendente extra;
   envelope/paquímetro duplicados) ou sortear história com set simples.

## 7. Alinhamento V6 (obra antes dos testes)

- `PROMPT_SISTEMA_v6.txt` reescrito byte a byte a partir de
  `regras_v6.PROMPT_MESTRE_V6` (25.686 chars, LF).
- `benchmark_v6.py --dry` aceito (o modo seco já era o padrão).
- `regras_v4.montar_prompt_v4()` nunca mais emite `non_diegetic_music: N/A`:
  usa `MUSICA_INSTRUMENTAL_PADRAO` quando o clipe não traz trilha.
- Âncora do smoke (`smoke_60s.py`) deixou de fixar `N/A`: herdou
  `overall_soundscape`/`non_diegetic_music` do clipe 1, com fallback
  instrumental.
- Contrato H3 preservado: `integrated_multimodal_description` +
  `overall_soundscape` + `non_diegetic_music`.
- `FORMATOS` segue 3/6/30; produção de 90–102 clipes continua desabilitada até
  o benchmark Astra × Sol e o teste de fumaça da V6.

## 8. Regra de ouro

O supervisor garante **continuidade e entrega**, não aprovação de qualidade.
Se o gate reprovar tudo, ele entrega o fallback e registra 0/6 — como neste
incidente. A decisão de refazer por qualidade é humana.
