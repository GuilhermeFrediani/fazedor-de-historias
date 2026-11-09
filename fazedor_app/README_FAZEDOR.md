# FAZEDOR DE HISTÓRIAS — como rodar

**TÉO & JUCA Company · app v1.3 · dossiê v1.0 · zero instalação (Python stdlib + Edge)**

## Ligar o programa

```
python "C:\Users\Guilherme\Desktop\PROJETO_MINIMAX_H3_RECUPERADO\fazedor de histórias\fazedor_app\fazedor_app.py"
```

Abre sozinho no navegador em `http://127.0.0.1:8756`. Fechar = `Ctrl+C` na janela.

## Motor de lapidação (fixo): AgentRouter

- Provedor único: **AgentRouter** (`https://agentrouter.org/v1/responses`, OpenAI Responses API).
- Modelos: `gpt-6.1-sol` · `gpt-6-astra` · `gpt-5.6-sol` (lista oficial via `GET /v1/models`).
- Chave em `config_secret.json` (`agentrouter_key`) — pré-carregada no app automaticamente.
- Obstáculos que o app resolve sozinho: o WAF do painel só aceita UA de agente
  (usamos o do Codex CLI); os modelos **raciocinam** (esforço low, orçamento 96k
  tokens — o JSON do episódio é grande); imperativos de geração no input são bloqueados
  (todo o conteúdo vai em `instructions` e o input é só `ok`); a chamada é em
  **streaming** (síncrona estoura o 504 do ALB deles).
- Lapidação demora **5–15 min por rodada** — normal, são modelos de raciocínio.
- STT (transcrição do 🎙️) continua no **Gemini** — o token do AgentRouter não tem
  permissão para modelos de áudio.

## Fluxo de uma sessão

1. **🎙️ FALAR** — grava o microfone (MediaRecorder) e transcreve pelo Gemini.
   Na 1ª vez: autorize o microfone para `127.0.0.1`.
   Ferramentas de socorro: **🩺 diagnóstico** (6 testes + relatório copiável) ·
   **🔊 eco-teste** (grava 3 s, toca a sua voz de volta e transcreve o eco) ·
   **🪟 áudio Windows** (abre as permissões globais do sistema).
   *Fallbacks*: digitar na caixa · ditar com `Win+H`.
2. **Lapidar** — botão **🤖 Lapidar com API** (AgentRouter; correção reenvia o histórico
   completo). *Modo Cola*: **Gerar pacote** agora usa a MEMORY DIRECTIVE do dossiê —
   cole num chat gratuito e traga a resposta para **Validar JSON colado**.
3. **Validar** — 0 erros → **Salvar** → **⚙️ Settings v2.1**.
4. **Saída** — `EPISODIOS/<slug>/` com `episodio.json`, `shot_NN.txt` (prompts),
   `manifest.json` + `settings/` com `<slug>_cNN_<estagio>_settings.json`
   (LoRA turbo, seed 7001, 1152×640, spectrum, `--profile 5`, clipes de **10 s**)
   + o script **`<slug>_gerar_todos.ps1`** com a corrente inteira (@80 s/s).

## Formato do episódio (dossiê v1.0 — DOSSIE_TEO_JUCA_v1.docx)

- **300 s = 30 clipes de 10 s** · estrutura obrigatória: LIGACAO 1 · CHEGADA 2 ·
  DIAGNOSTICO_ERRADO 3 · PRIMEIRA_FALHA 3 · JEITINHO 5 · PAUSA_COMICA 1 · ESCALADA 5 ·
  CLIMAX 5 · REACAO_EM_CORO 1 · NOTA_FISCAL 4.
- **MEMORY DIRECTIVE (seção 12 do .docx)** é injetada VERBATIM pelo servidor em toda
  lapidação AgentRouter — junto do vocabulário fixo (`blocos_fixos.json`) e da
  **LEI DE FERRO** (zero fala · zero texto na tela · zero trilha · dano só material ·
  ninguém percebe o erro · nota fiscal · TÉO à esquerda, JUCA à direita).
- JSON do episódio: `titulo, logline, setor, servico, cliente, mecanismo,
  degrau_final, objetos_plantados[3], callback_object, shots[{n, dur, estagio, beats,
  action, overall_soundscape, non_diegetic_music}], continuidade, assinatura`.
- O campo `action` já É o prompt do pipeline; o app só acrescenta o prefixo
  `integrated_multimodal_description: [Shot N]` + as linhas `overall_soundscape:` e
  `non_diegetic_music: N/A` (formato idêntico ao `quadro_s1_settings.json`).
- Validador do dossiê no servidor (`validar_dossie`): contagem de estágios, 30 clipes
  de 10 s, `They do not speak…` em todo action, termos vedados
  (freeze/exactly/handheld/says…), foley com evento nomeado (material + verbo),
  música sempre N/A, 3 objetos plantados (clipes 1–10) pagos no clímax (25–30),
  JUCA/TÉO (nunca Joca/Theo), teto absoluto de 7.000 chars por action.

## Onde o programa conhece TÉO, JUCA e o pipeline

- `DOSSIE_TEO_JUCA_v1.docx` (raiz do projeto) — **fonte canônica v1.0**; o app extrai
  a MEMORY DIRECTIVE direto do .docx a cada boot (nunca o modifica).
- `blocos_fixos.json` — âncoras de personagens/estilo/negativos, usadas verbatim.
- Formato legado (`SISTEMA_GERADOR_TEO_JUCA_v1.md` + `exemplo_episodio_pintura.json` +
  `montar_prompts.py`) — continua funcionando para episódios antigos; o app detecta o
  formato pelo shape do JSON (dossiê tem `dur`/`objetos_plantados`, legado tem `duracao_s`).

## Microfone — problemas comuns

- Erro `NotAllowedError`: cadeado na barra de endereço → Microfone → Permitir → F5;
  se persistir, 🪟 áudio Windows (acesso global de apps de desktop) e reabra o navegador.
- Sem bolinhas `●●●●` durante a gravação = nada captado: veja 🩺 diagnóstico.
- Sempre disponível: digitar ou `Win+H`.

## Certificação

`python certificar_agentrouter.py` (com o servidor ligado) — roda os 3 modelos no
fluxo real (lapidação → validação → correção) e imprime o placar por modelo.
