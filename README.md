# 🎬 FAZEDOR DE HISTÓRIAS — TÉO & JUCA Company

Gerador automático de episódios de claymation muda em **TÉO & JUCA — SERVIÇOS GERAIS**:
você fala uma ideia → a IA (AgentRouter / GPT-6.x via Responses API) escreve o roteiro
completo de **300 s em 30 clipes de 10 s** → valida pelas regras do dossiê → e entrega os
prompts prontos para o pipeline de vídeo (MiniMax H3 via WanGP).

## Como funciona

```
🎙️ ideia falada ──► transcrição (Gemini STT)
        │
        ▼
🧠 lapidação ──► MEMORY DIRECTIVE (dossiê v1.0) + LEI DE FERRO
        │         forçadas no servidor (zero fala · zero texto · zero trilha ·
        │         dano só material · nota fiscal · TÉO ⟂esquerda / JUCA ⟂direita)
        ▼
🎲 autoepisódio ──► matriz de 72.000 temas (12 setores × 10 serviços ×
        │            6 mecanismos × 10 clientes × 10 degraus)
        ▼
✅ validação ──► 30 clipes × 10 s · estágios · foley nomeado · vedações
        │
        ▼
⚙️ settings v2.1 ──► 30 prompts + corrente .ps1 para o gen_test.py (WanGP)
        │
        ▼
🎬 30 clipes renderizados ──► emendados = 1 episódio de 5 minutos
```

## Estrutura

| Arquivo | Papel |
|---|---|
| `DOSSIE_TEO_JUCA_v1.docx` | **Fonte canônica v1.0** — a MEMORY DIRECTIVE é extraída dele a cada boot |
| `blocos_fixos.json` | Âncoras visuais dos personagens + estilo + negativos (verbatim em todo clipe) |
| `montar_prompts.py` | Motor de validação/montagem do formato legado |
| `fazedor_app/` | O app: servidor stdlib + UI (mic 🎙️, 🎲 autoepisódio, cartões, validação, settings) |
| `fazedor_app/certificar_agentrouter.py` | Certifica os 3 modelos no fluxo real (lapidação → validação → correção) |

## Rodar

```
LIGAR_FAZEDOR.bat   (duplo-clique)
```

Servidor em `http://127.0.0.1:8756`. Chaves em `fazedor_app/config_secret.json`
(**nunca versionado** — mantém `agentrouter_key` e `gemini_key`).

## Pipeline de vídeo (fora deste repo)

- `gen_test.py` + WanGP (MiniMax H3, LoRA turbo, 1152×640, 24 fps, spectrum, `--profile 5`)
- ~80 s de GPU por segundo de vídeo → episódio de 300 s ≈ 6,7 h de render

---

*TÉO & JUCA — SERVIÇOS GERAIS: nunca recusam um serviço, nunca desistem, sempre emitem nota fiscal. E nunca falam.*
