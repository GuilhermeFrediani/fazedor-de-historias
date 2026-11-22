# CHANGELOG v5 — o cérebro de comédia permanente

Data: 22/11/2026 · base: v4 + rodadas de render v7 (Operação Ralo Exato)

## Motivo

O gerador sabia o que FILMAR (v3/v4), mas o conhecimento de comédia que guiou os
acertos do projeto vivia espalhado entre prompts, docs e a cabeça de quem operava.
A partir da v5 ele é **código**: um bloco canônico injetado em toda geração de
história, com a referência Zeca e Joca / Pat & Mat, a teoria do humor e o contrato
de continuidade/causalidade/payoff que os testes de render v4→v7 ensinaram.

## Mudanças

### `fazedor_app/canon_comedia.py` (novo)

- **`REFERENCIA`** — a referência-mãe completa: Pat & Mat / Zeca e Joca (1976,
  Lubomír Beneš e Vladimír Jiránek), premissa dos dois vizinhos faz-tudo, contexto
  do cinema mudo, mecânica do riso (incongruência, expectativa frustrada, escalada,
  slapstick, causa/efeito visível, otimismo cômico, ritmo/repetição), teoria
  (incongruência + superioridade + alívio; set-up/punchline visual), semântica
  (esperado vs cômico, competência no esforço × incompetência no resultado),
  estrutura de 8 passos, 7 regras práticas, 6 perguntas de criação, referências
  irmãs (Tom e Jerry, Pica-Pau, Pantera Cor-de-Rosa, Mr. Bean, Trapalhões,
  Zé Carioca, Wallace & Gromit, Aardman/Shaun the Sheep) e resumo do estilo.
- **`CONTINUIDADE`** — o contrato acumulado: lei do um clipe = um objeto + uma
  causa + um efeito + um payoff; causa visível/herda_de; estado_out(N) ==
  estado_in(N+1); registro de objetos com contagem, plantio e dono da posição;
  SET afirmativo e fechado (negativas viraram conceito em cfg 1); emenda/âncora
  anti-ghost; TÉO mede à esquerda, JUCA executa à direita; zero fala/texto/música;
  dano só material; física de uma primitiva; arco começo→meio→fim com payoff visual.
- **`SCHEMA`** — campos novos do JSON: `canon`, `premissa_simples`,
  `solucao_errada`, `escalada`, `payoff_visual`, `otimismo_final`; por clipe:
  `causa`, `efeito`, `payoff`, `escala` (objeto|parede|piso|teto).
- **`CHECKLIST`** — 12 perguntas de aceite do cérebro.
- **`BLOCO_MESTRE`** (~13,6 k chars) — tudo acima pronto para injeção; `BLOCO_CURTO`
  para contextos apertados.

### `fazedor_app/regras_v4.py`

- `PROMPT_MESTRE_V5 = PROMPT_MESTRE_V4 + BLOCO_MESTRE` — o cérebro entra no prompt
  do roteirista sem reescrever as leis de renderizabilidade da v4.
- `validar_montagem()` ganhou o bloco **CÉREBRO DE COMÉDIA**:
  - com `canon: zeca_joca_v1`, os campos de arco e os campos por clipe são
    contrato (erro se faltarem ou se a escalada voltar atrás);
  - `escalada` só aceita `objeto|parede|piso|teto` e precisa ser monotônica;
  - legado sem `canon` recebe **aviso**, não erro — o passado não quebra;
  - episódio canônico completo ganha o check "cérebro de comédia completo".

### `fazedor_app/fazedor_app.py`

- `instrucoes_dossie()` → `PROMPT_MESTRE_V5` (o AgentRouter força este sistema).
- `reforcar_canon(mensagens)` — injeta o bloco no system de **qualquer** provedor
  (Gemini/OpenAI/LM Studio), sem duplicar (marca idempotente). Chamado no `_gerar`.
- `/api/pieces` expõe `comedia_versao`, `comedia_bloco` e `comedia_canon`.

### `fazedor_app/ui.html`

- O modo **COLA** anexa o cérebro ao pacote (com ou sem dossiê).
- As chamadas de lapidação/correção via API também levam o cérebro no system.

### Documentos

- `CANON_COMEDIA_ZECA_JOCA.md` — versão legível do cérebro (gerada do módulo).
- `PROMPT_SISTEMA_v4.txt` — prompt de sistema completo (v4 + cérebro).
- `fazedor_app/teste_canon.py` — teste seco: presença no prompt/AgentRouter,
  idempotência do reforço, aprovação de episódio canônico e reprovação de clipe
  sem payoff. Não usa GPU nem rede.

## Resultado

```
python fazedor_app/teste_canon.py
OK   versão do canon = zeca_joca_v1
OK   bloco cita Zeca e Joca / Pat & Mat
OK   bloco traz a mecânica do riso
OK   bloco traz a corrente causa→efeito→payoff
OK   bloco traz o contrato anti-teleporte
OK   bloco declara o schema canon
OK   PROMPT_MESTRE_V5 contém o cérebro
OK   instrucoes_dossie() (AgentRouter) contém o cérebro
OK   reforcar_canon anexa ao system existente
OK   reforcar_canon é idempotente (não duplica)
OK   reforcar_canon cria system quando não existe
OK   episódio canon completo não gera erro de CANON
OK   clipe sem payoff é reprovado pelo canon
OK   episódio legado recebe aviso (não quebra o passado)
```

## Custo

0 GPU. Só texto: `PROMPT_SISTEMA_v4.txt` tem ~20,6 k chars e o bloco injetado
~13,6 k chars — folga no orçamento de 96 k tokens do AgentRouter.

## Próximo

- Retomar a fase 60 s do "Operação Ralo Exato": consertar o molde do c05 (céu pelo
  teto / tambor não prensado), renderizar c05/c06 sem `--so20s`, gate episódico e
  `montar_final_v7.py`.
- Re-render de c03/c04 (fallbacks da era da cortina) com a âncora da porta.
- Opcional: refiner H3 com máscara para olhos/rosto (inpaint 2K + distilled LoRA +
  `audio_refinement`).
