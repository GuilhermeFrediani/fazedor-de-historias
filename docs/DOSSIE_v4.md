# DOSSIÊ v4 — POR QUE NÃO TEM GRAÇA, E O QUE FOI CORRIGIDO

Projeto: **TÉO & JUCA — SERVIÇOS GERAIS** · fumaça de 6 clipes (60 s) · 13/11/2026

---

## 1 · O QUE VOCÊ QUERIA

Um canal dark de YouTube rodando com IA: histórias engraçadas de dois faz-tudo, geradas
em clipes de 10 s, sem bug de frame, com cara de claymation. A v3 já tinha resolvido o
"não filma" (física impossível, plano sem piada, ação enterrada depois de 3.900 chars de
roupa). O que sobrou — e você sentiu exatamente isso — é o **"molho"**: o vídeo ficou
tecnicamente correto e continua sem graça.

---

## 2 · O QUE ESTÁ RUIM (com evidência medida, não opinião)

Analisei o `operacao_ralo_exato_v3_fumaca_6clipes.mp4` (60,8 s, 1152×640, 1458 quadros)
quadro a quadro e medi o áudio. Três números explicam tudo:

| Medida | Valor real | O que deveria ser |
|---|---|---|
| Áudio médio do arquivo | **−38,5 dB** | −14 LUFS (padrão YouTube) |
| Pico de áudio | −7,3 dB | −1,5 dB |
| Planos dentro de cada clipe | **1 plano fixo** em 6 de 6 clipes | 2–3 planos com corte |
| Ar morto (bonecos plantados) | **~24 s de 60 s** | 0 s |
| Trilha musical | **nenhuma** | cama de comédia a −26 dB |
| Cliente militar na tela | 4 s, só no clipe final | abre e fecha o episódio |

### 2.1 · O diagnóstico central: você não tem um problema de piada, tem um problema de MONTAGE

A leitura segundo a segundo do arquivo entregue:

| Trecho | O que acontece na tela | Veredito |
|---|---|---|
| 00:00–00:04 | TEO puxa a trena, atende o telefone, o fone cai no chão | física da v3 **funcionou** |
| 00:04–00:10 | os dois olham o fone no chão, sem fazer nada | **6 s mortos** |
| 00:10–00:18 | tambor sobe, TEO aponta, JUCA coça a cabeça, tambor tomba | ação existe, sem corte |
| 00:18–00:22 | TEO ergue o dedo, JUCA coça a cabeça (loop) | **4 s mortos** |
| 00:20–00:30 | JUCA abre a grelha, TEO "escreve" em prancheta invisível | piada não declarada na tela |
| 00:27–00:30 | os dois olham o buraco escuro | **3 s mortos** |
| 00:30–00:40 | espuma jorra, TEO levanta um bloco de espuma e larga | gag ilegível |
| 00:36–00:40 | os dois parados olhando a pilha | **4 s mortos** |
| 00:40–00:50 | gancho, corrente, sino/domo sobe (**objeto nunca plantado**) | quebra de continuidade |
| 00:50–00:58 | TEO pisa no domo, JUCA põe a grelha, os dois parados | **5 s mortos** |
| 00:58–01:00 | oficial entra pela cortina | único momento de "fecho", 2 s |

**24 segundos de 60 são planos mortos.** Num clipe de 10 s, um plano fixo único é o
formato mais próximo de um slideshow. Comédia muda vive de **corte + reação + som**;
a v3 entregou continuidade e matou o ritmo.

### 2.2 · A v3 otimizou contra a comédia sem perceber

Três regras da v3 trabalhavam contra o riso:

1. **"reação seca"** — em plano geral, reação pequena é reação **inexistente**. Era o que
   fazia o clipe 1 terminar em 6 s de dois bonecos olhando o chão.
2. **"NINGUÉM PERCEBE O ERRO"** (Lei de Ferro nº 5) + murmúrios zerados → tirou o
   resfôlego, o suspiro, o estalo de língua. Em claymation o som de boca **é** metade da piada.
3. **prompt em parágrafo único** — a v3 escrevia `action` corrida; o modelo gasta o
   orçamento de atenção num movimento e nunca recebe ordem de **cortar**.

### 2.3 · A camada de render: separando o que é do gerador e o que é do WanGP

Testei as alavancas contra a documentação atual antes de recomendar qualquer coisa:

| Alavanca | Situação | O que a documentação diz |
|---|---|---|
| **6 steps + LoRA turbo 1.0** | ok, mantenha | O LoRA lightx2v é destilado para 6–8 steps; acima de 8 vem over-sharpening e **nenhum ganho** ([larryvrh/MiniMax-H3-Turbo-Lora](https://huggingface.co/larryvrh/MiniMax-H3-Turbo-Lora)) |
| **Aumentar steps para 12–20** | **não resolve bug** e custa 3x GPU | Mesmo guia: 4–8 steps é a faixa; passar disso não conserta morfologia, só endurece textura |
| **CFG** | mantenha 1.0 | O H3 é destilado para cfg 1 — não existe ramo negativo real |
| **Lista de negativos** | **removida na v4** | Em cfg 1 a lista vira **conceito**: foi ela que trouxe "cartoon outlines" e brilho plástico para o render |
| **shift (flow_shift 12)** | ok | Faixa usada nos perfis WanGP para 10 s |
| **q4_K_M → q8** | **troca real, se a VRAM deixar** | Q5_K_M/Q8 mantêm mais detalhe; Q4_K_M é o ponto de partida por VRAM ([guia GGUF](https://willitrunai.com/blog/quantization-guide-gguf-explained)) |
| **1152×640** | ok | Resolução nativa do modelo; subir para 1344×768 dá +40% de tempo por clipe |

**Conclusão sobre o render:** os artefatos que você vê (mão fundindo, corrente esticando,
tambor clipando no piso) **não são falta de steps** — são o modelo resolvendo uma
instrução que pede dois eventos no mesmo plano. A prova está no próprio arquivo: os
quadros do clipe 1 (uma causa, um objeto) são limpos; os do clipe 4 (espuma + manta +
dois corpos) são os borrados. **A correção de render é de prompt e de corte, não de steps.**

Se quiser atacar o resíduo de nitidez sem pagar 3x: **subir q4_K_M → q5_K_M** mantendo
6 steps. Custo: ~8% mais VRAM, ~5% mais tempo. É a única alavanca de render barata que
sobrou.

---

## 3 · O QUE FOI ARRUMADO (v4)

### 3.1 · `regras_v4.py` — a camada de montage que faltava

| Lei nova | O que exige | Por que |
|---|---|---|
| **LEI DO CORTE** | todo clipe tem **2–3 planos com hora de corte** no formato oficial do H3: `[Shot 1] ... [Shot 2] At 00:03.500, the camera cuts to ...` | é o que cria ritmo; o modelo já sabe cortar quando recebe a hora |
| **LEI DO CORPO INTEIRO** | reação de **metade do corpo**: coluna, ombros, joelhos, mãos — nunca "olham" | substitui a "reação seca" que não aparecia em plano geral |
| **LEI DO SOM** | 4–6 eventos concretos (material + verbo + intensidade) + **2 sons de boca** por clipe | ataca direto os −38,5 dB |
| **LEI DO AR MORTO** | nenhum plano descreve alguém parado; o clipe termina em movimento | mata os 24 s de slideshow |
| **CLIENTE ABRE E FECHA** | o cliente aparece no 1º e no último clipe | a assinatura da série (nota fiscal) existia no dossiê e **não existia na tela** |
| **NEGATIVOS APOSENTADOS** | zero lista de negativos no prompt | cfg 1: a lista vira conceito |
| **MÚSICA OBRIGATÓRIA** | `non_diegetic_music` com instrumento **e** ritmo (tuba + woodblock, 88 BPM, parada seca em cada impacto) | o arquivo atual não tinha trilha nenhuma |

Estrutura obrigatória de cada clipe de 10 s:

```
PLANO A  0,0–3,5 s  INSERT no objeto que vai falhar (close, objeto grande no quadro)
PLANO B  3,5–7,0 s  PLANO GERAL — a ação física acontece, os DOIS corpos se movem
PLANO C  7,0–10,0 s CLOSE NA REAÇÃO — meia-linha do corpo + som de boca
```

### 3.2 · `montar_prompt_v4` — prompt no formato oficial, com os cortes datados

Antes: ~3.900 chars de descrição de roupa, depois a ação (o modelo renderizava a roupa).
Agora: âncoras de identidade em **~30 palavras cada**, e o corpo do prompt são os planos:
`[Shot 1] close insert ...` / `[Shot 2] At 00:03.500, the camera cuts to ...`. Total
**2.100–2.450 chars** por clipe, com cabeça (`estilo + set + TEO + JUCA`) antes dos planos.

### 3.3 · `pipeline/pos_producao.py` — a camada que nenhum prompt resolve

O gerador entrega clipes crus. Clipe cru não tem molho. Este script é o editor:
mede o ar morto (`freezedetect`), normaliza para **−14 LUFS**, corta o rabo morto de cada
clipe, abre um **punch-in de 1,25× no meio** (corte seco sem regerar nada — 0 GPU),
mistura cama musical a −26 dB, e concatena com `+faststart`.

```
python pos_producao.py --analisar CLIPES                 # mede ar morto + volume
python pos_producao.py --pasta CLIPES --saida EP.mp4 --musica bed.mp3
```

Saída real do analisador no arquivo que você me mandou:

```
clipe                 dur   media    pico  ar morto
v3.mp4               60.8   -38.5    -7.3  0.0s em 0 trecho(s)
```

−38,5 dB médio é 24 dB abaixo do padrão. Só normalizar já muda a percepção de "sem graça".

### 3.4 · Validador composto `0,30 humor + 0,35 render + 0,35 montage`

A nota antiga era `0,35 humor + 0,65 render`: dava 9,0/10 para um episódio que na tela era
um slideshow. Agora montage tem o mesmo peso de render, e **reprova** com plano único,
reação sem corpo, soundscape sem som de boca e clipe sem objeto de gag.

---

## 4 · CUSTO DE GPU — o que muda no bolso

| Cenário | v3 | v4 |
|---|---|---|
| Fumaça 6 clipes | ~90 min | **~90 min** (mesmos 6 clipes de 10 s) |
| Episódio 30 clipes | ~7,3 h | **~7,3 h** |
| Pós-produção | 0 | **~40 s de CPU** (ffmpeg, 0 GPU) |
| Validar antes de gastar GPU | `--seco` instantâneo | `--seco` instantâneo |
| Se subir q4→q5 | — | +5% de tempo (~4,5 min por fumaça) |
| Se subir steps 6→12 | ~2x GPU | **não recomendado: não corrige bug** |

O ganho de qualidade vem de **corte + som + pós**, que custam CPU, não GPU. Aumentar
steps é o caminho mais caro e o menos eficaz.

---

## 5 · COMO RODAR O TESTE (ordem exata)

```bat
REM 1. substituir a pasta do projeto pela versão v4 (backup .py.v3.bak já está dentro)
REM 2. aplicar o patch no app (uma vez)
cd fazedor_app
python aplicar_v4.py

REM 3. fumaça seca — instantânea, 0 GPU
python fumaca_v4.py --seco
REM esperado: NOTA 10/10 (humor 9 · render 7 · montage 10), 6 settings escritos

REM 4. só se a nota >= 7: gastar GPU (~90 min)
python fumaca_v4.py

REM 5. MONTAR (o passo que faltava no seu fluxo)
cd ..\pipeline
python pos_producao.py --pasta "C:\pinokio\api\wan2gp-amd\app\outputs" ^
       --saida operacao_ralo_exato_v4_FINAL.mp4
```

### O que olhar no MP4 (12 perguntas de julgamento)

1. Cada clipe tem **3 planos diferentes** (inserto → ação → reação)?
2. Em algum momento os dois ficam parados mais de 1,5 s?
3. A reação ocupa **ombros/braços/joelhos**, ou só a cabeça?
4. Você ouve **resfôlego/suspiro/estalo de língua** em cada clipe?
5. Tem **trilha** por baixo? Ela para no impacto?
6. O clipe termina com alguém se mexendo?
7. O cliente aparece no 1º e no último clipe?
8. O telefone continua no chão do clipe 1 ao 2 (sem voltar para a parede)?
9. A grelha sai do ralo no 1 e volta no 2 em cima do tambor?
10. O buraco fica aberto do 2 ao 5 e é selado no 6?
11. A água cresce (seco → molhado → alagado)?
12. Algum objeto aparece sem ter sido plantado? (era o domo preto do clipe 5 na v3)

Se as 12 passarem e ainda faltar graça, o problema é de **escrita**: me diga qual clipe
não tem piada e eu reescrevo só aquele prompt (rerender = ~15 min).

---

## 6 · PRÓXIMO DEGRAU, DEPOIS DA v4 PASSAR

1. **Voz em pós** — murmúrio executivo gravado por você (2 clipes por episódio) resolve
   o "sem molho" melhor que qualquer prompt. Claymation vive de grunhido humano.
2. **Foley em pós** — o `pos_producao.py` já normaliza; o passo seguinte é uma pasta de
   12 sons (metal, borracha, água, papel) disparada por evento declarado no JSON.
3. **Repetição com variação** — a mesma gag (o tambor) volta no clipe 2, 5 e 6. Isso é o
   que faz o público rir na terceira vez, e a v4 já planta isso no `objetos_plantados`.
4. **Episódio completo de 300 s** só depois de 2 fumaças aprovadas no checklist de 12.
