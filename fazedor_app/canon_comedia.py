# -*- coding: utf-8 -*-
"""canon_comedia.py — O CÉREBRO PERMANENTE DE COMÉDIA DO TÉO & JUCA.

Fonte: Zeca e Joca / Pat & Mat (1976) + teoria do humor + TODAS as lições de
continuidade, causalidade e payoff acumuladas nos testes v4 -> v7.

Este módulo é injetado em TODO caminho de geração de história:
  1. regras_v4.PROMPT_MESTRE_V5 (prompt mestre do roteirista);
  2. fazedor_app.instrucoes_dossie() — o AgentRouter força este sistema;
  3. fazedor_app._gerar() — reforça o bloco em QUALQUER provedor (Gemini/OpenAI);
  4. /api/pieces + modo COLA da UI — o pacote manual também leva o bloco.

Regra de ouro: o cérebro descreve COMÉDIA e CONTINUIDADE. O modelo de vídeo
recebe só ação/estado/câmera/som; as listas de negativos valem para as
INSTRUÇÕES (aqui), nunca para o SET ou o action que vão ao render.
"""

VERSAO = "zeca_joca_v1"
MARCA = "CÉREBRO DE COMÉDIA TÉO & JUCA"

# ─────────────────────────────────────────────────────────────────────────────
# 1. A REFERÊNCIA-MÃE (contexto completo do que é comédia neste projeto)
# ─────────────────────────────────────────────────────────────────────────────
REFERENCIA = r"""
=== A REFERÊNCIA-MÃE: ZECA E JOCA / PAT & MAT ===
A referência mais provável do "desenho antigo" é Zeca e Joca (no original, Pat & Mat):
série tchecoslovaca de animação em stop-motion/claymation criada por Lubomír Beneš e
Vladimír Jiránek em 1976. O humor é essencialmente slapstick: dois vizinhos atrapalhados
tentam resolver tarefas domésticas simples, mas cada solução cria um problema maior, até
terminar em uma catástrofe absurda — seguida do famoso aperto de mãos.

PREMISSA: Pat e Mat (Zeca e Joca) são dois bonecos de massinha, vizinhos e "faz-tudo", que
encaram consertos, reformas, cozinhar, lavar roupa, montar móveis e outras situações
cotidianas. Eles nunca desistem, mas são incompetentes de forma criativa: usam ferramentas
improváveis e soluções cada vez mais elaboradas.

CONTEXTO: humor físico da tradição europeia, próximo do cinema mudo e da comédia de gags:
pouca fala, ação visual, repetição, destruição e consequências em cadeia. A série nasceu na
então Tchecoslováquia e se espalhou como Pat & Mat, Buurman & Buurman e, no Brasil, Zeca e
Joca.

=== POR QUE É ENGRAÇADO (a mecânica do riso) ===
- INCONGRUÊNCIA: uma tarefa banal recebe uma solução absurda, exagerada ou logicamente errada.
- EXPECTATIVA FRUSTRADA: o espectador espera que o conserto funcione; a solução piora tudo de
  forma inesperada.
- ESCALADA: o problema começa pequeno — uma parede, uma torneira, uma salada — e cresce até
  virar desastre total.
- SLAPSTICK: quedas, batidas, objetos quebrados e acidentes físicos exagerados geram riso sem
  violência real.
- DOMÍNIO DE CAUSA E EFEITO: cada ação tem uma consequência visual clara; o público entende a
  lógica da bagunça antes mesmo do desfecho.
- OTIMISMO CÔMICO: mesmo após destruir quase tudo, os personagens seguem confiantes, criativos
  e orgulhosos do resultado.
- RITMO E REPETIÇÃO: a estrutura "problema -> tentativa -> piora -> nova tentativa -> desastre
  final" cria uma expectativa que o desenho cumpre com variações.

TEORIA DO HUMOR: incongruência (algo rompe nossas expectativas), superioridade (rimos de erros
e desgraças alheias) e alívio (a tensão acumulada é liberada pelo riso). Em Zeca e Joca, os
três operam juntos: a solução errada surpreende, os personagens falham de modo inofensivo e a
tensão se resolve em uma piada visual. A piada é um set-up + punchline: primeiro cria-se uma
expectativa; depois ela é violada. No desenho, o punchline raramente é uma frase — é uma parede
caindo, uma máquina explodindo ou uma solução que transforma um pequeno defeito em ruína.

=== A SEMÂNTICA DO HUMOR (o deslocamento) ===
- SIGNIFICADO ESPERADO: consertar algo deve tornar a situação melhor.
- SIGNIFICADO CÔMICO: consertar torna a situação muito pior.
- CONTRADIÇÃO CENTRAL: os personagens são competentes em esforço, mas incompetentes em resultado.
- INVERSÃO DE VALOR: uma solução "inteligente" é apresentada com seriedade, embora seja
  completamente absurda.
- PONTO DE VISTA DO PÚBLICO: nós enxergamos o erro antes deles; isso cria antecipação, tensão
  e recompensa quando a catástrofe acontece.

=== ESTRUTURA DE UM EPISÓDIO (começo, meio e fim) ===
1. TAREFA SIMPLES: Zeca e Joca querem pendurar um quadro, consertar um encanamento ou preparar
   comida. O objetivo é entendido em 2 segundos.
2. OBJETIVO CLARO: o público entende imediatamente o que eles pretendem fazer.
3. PRIMEIRA SOLUÇÃO ERRADA: ela parece racional para os personagens, mas o espectador já
   percebe o risco.
4. CONSEQUÊNCIA VISUAL: algo quebra, cai, vaza, explode ou se transforma.
5. NOVA SOLUÇÃO PIOR: em vez de desfazer o erro, eles adicionam uma gambiarra em cima dele.
6. ESCALADA: os problemas se acumulam e se conectam; cada um nasce do anterior.
7. CLÍMAX ABSURDO: a solução final resolve o problema de um jeito estranho, destrutivo ou
   inesperado.
8. FECHAR COM ORGULHO: eles comemoram, mesmo que o resultado seja um desastre. O serviço é
   "entregue" — do pior jeito possível.

=== REGRAS PRÁTICAS DE CRIAÇÃO ===
- COMECE PEQUENO: um parafuso torto pode virar a destruição de uma casa inteira.
- FAÇA O ERRO TER LÓGICA INTERNA: o personagem não é burro por acaso; ele segue uma
  racionalidade equivocada.
- A GAG NASCE DA TAREFA: o objeto que falha é o objeto do serviço; nada de acidente
  genérico que poderia acontecer em qualquer episódio.
- USE OBJETOS COMO PERSONAGENS: uma escada, uma máquina, uma porta ou uma panela pode reagir de
  forma exagerada.
- ADIE O ALÍVIO: quanto mais o problema cresce, maior é o riso quando ele explode.
- NÃO EXPLIQUE DEMAIS: a comédia visual depende de o público compreender a gag sem diálogo.
- MANTENHA A SIMPATIA: os personagens podem falhar, mas não devem parecer cruéis ou maldosos.
- TERMINE COM UMA IMAGEM FORTE: a última cena deve ser a punchline visual do episódio.

=== PERGUNTAS DE CRIAÇÃO (para cada cena) ===
1. Qual é o objetivo simples?
2. Qual é a solução óbvia?
3. Como posso fazer a solução óbvia falhar?
4. Qual seria a pior consequência possível, mas ainda engraçada?
5. Como o personagem pode tentar consertar isso e piorar ainda mais?
6. Qual imagem final resume todo o desastre?
Exemplo: eles querem pendurar um quadro. Pregam um prego; a parede racha; tentam reforçá-la; a
parede desaba; tentam reconstruí-la; a casa inteira se desmonta; no fim, o quadro fica
pendurado — mas na árvore do quintal. O objetivo foi cumprido, porém de forma absurda.

=== OUTRAS REFERÊNCIAS DO MESMO TIPO ===
Tom e Jerry (slapstick, perseguição, destruição e gags físicas); Pica-Pau (caos doméstico,
exagero físico, ironia); A Pantera Cor-de-Rosa (comédia visual, erro de execução); Mr. Bean
(humor quase sem fala, lógica errada e reações físicas); Os Trapalhões (dupla atrapalhada,
planos que dão errado); Zé Carioca (malandragem, improviso, caos); Wallace & Gromit
(stop-motion, invenções improváveis, desastres domésticos); Aardman / Shaun the Sheep (humor
visual, física exagerada, ausência de diálogo explicativo). O elo comum é o SLAPSTICK DE
CONSTRUÇÃO: alguém tenta resolver algo, usa uma solução engenhosamente errada e o erro se
transforma em espetáculo.

=== RESUMO DO ESTILO ===
O humor é COMÉDIA DE INCOMPETÊNCIA CRIATIVA. Funciona porque transforma tarefas mundanas em
operações de alto risco, porque o público entende a lógica do erro antes dos personagens e
porque a escalada é construída com clareza visual. O riso nasce do contraste entre a seriedade
dos personagens e a absurda magnitude do desastre. Pense menos em "piadas" e mais em MECÂNICAS
DE DESASTRE: objetivo simples -> solução errada -> consequência lógica -> nova solução pior ->
imagem final que fecha a gag.
"""

# ─────────────────────────────────────────────────────────────────────────────
# 1b. ORIGINALIDADE (inspirar a mecânica, nunca copiar a obra)
# ─────────────────────────────────────────────────────────────────────────────
ORIGINALIDADE = r"""
=== ORIGINALIDADE (inspirar a mecânica, nunca copiar a obra) ===
- A referência é de MECÂNICA, não de superfície: tarefa simples -> solução errada ->
  consequência -> escalada -> desastre -> orgulho. Nada além disso é emprestado.
- Não copie personagens, nomes, rostos, roupas, cores, vozes, diálogos, sons, cenários
  ou cenas específicas de Zeca e Joca / Pat & Mat, Tom e Jerry, Pica-Pau, Pantera
  Cor-de-Rosa, Mr. Bean, Trapalhões, Zé Carioca, Wallace & Gromit ou qualquer obra
  protegida.
- TÉO & JUCA são originais deste projeto. O episódio não recria nem "homenageia" uma
  cena existente: a gag é nova, a mecânica é a mesma família de humor.
- Se uma ideia só funciona porque o público reconhece a obra original, ela não serve.
"""

# ─────────────────────────────────────────────────────────────────────────────
# 2. A LÓGICA NARRATIVA E A CONTINUIDADE (o que os testes v4->v7 ensinaram)
# ─────────────────────────────────────────────────────────────────────────────
CONTINUIDADE = r"""
=== A LÓGICA NARRATIVA E A CONTINUIDADE (contrato de ferro do projeto) ===

A LEI DO UM (por clipe)
- UM clipe = UM objeto + UMA causa + UM efeito + UMA reação/payoff.
- Se aparecer "e então", "que faz", "o que provoca", "fazendo o outro", "até que" mais de uma
  vez no mesmo clipe, há duas causas: corte em dois clipes ou jogue a segunda fora.
- TESTE DO DESENHO: se você não consegue desenhar a piada em UM quadro parado, ela não existe.
  "O fio do telefone reboca o carrinho" não se desenha; "a corda esticada prende no eixo da
  roda" se desenha.

CAUSA -> EFEITO -> PAYOFF (a corrente de ouro)
- CAUSA: visível no clipe anterior (inserto ou canto) ou no estado_in; declare `herda_de` e
  `causa`. Causa invisível = piada que não vem.
- EFEITO: uma mudança física visível; o objeto faz UMA coisa só; o dano é material e PERSISTE.
- PAYOFF: a reação/punchline do clipe — o que o público ganha ao ver a consequência. No último
  clipe, o payoff fecha a promessa do primeiro (callback_object) e entrega o serviço "errado".
- NADA se resolve sozinho: o problema não "acaba", muda de lugar. O `estado_out` do clipe N é o
  `estado_in` do clipe N+1, palavra por palavra.
- NADA SE RESOLVE POR SORTE: proibido corte mágico, ajuda externa, objeto que aparece
  pronto, "deus ex machina" ou solução que não custa nada. Toda melhoria cria um custo
  visual novo; o problema só muda de lugar.
- Nenhum objeto aparece sem plantio, some sem ação, muda de mão/tamanho/cor entre quadros ou é
  duplicado.

REGISTRO DE OBJETOS (o contrato anti-teleporte)
- Todo objeto da história tem: nome, CONTAGEM exata, clipe de plantio, posição e DONO DA POSIÇÃO
  até uma ação visível movê-lo.
- O mesmo objeto não pode existir duas vezes: dois baldes, dois telefones, duas grelhas = defeito
  grave. Conte os objetos no frame antes de escrever.
- Objetos de fundo (não-gag) não entram na contagem, mas não podem virar gag nem mudar de lugar.
- O objeto que nasce de outro (ex.: a base do telefone) mantém cor, forma e posição da âncora.
- Ferramenta ou equipamento só age se estava visível no clipe anterior.

CENÁRIO (o contrato do fundo)
- O SET é AFIRMATIVO e FECHADO: descreva SÓ o interior que existe. No prompt que vai ao modelo
  de vídeo, nunca escreva listas de negativos ("no sky", "never trees", "sem exterior") — em
  cfg 1 a lista vira conceito e MATERIALIZA o que você negou. A negativa vale para estas
  INSTRUÇÕES, não para o SET/action.
- O fundo é o mesmo em todos os clipes; a câmera pode mudar, o mundo não.
- Nada de exterior, céu, árvores, janelas abertas ou portas que dão para fora. O galpão/átrio/
  sala é fechado do chão ao teto; o interior preenche o quadro inteiro.
- Objetos fixos (porta, cortina, painéis, tubos) ficam FECHADOS/PARADOS, a menos que a ação os
  mova; uma porta que "se abre para o exterior" é uma janela de erro.

FICHA VISUAL IMUTÁVEL (o programa cola, o roteirista não reescreve)
- Aparência, roupa, cor, proporção e cenário vêm das âncoras (TEO_CURTO/JUCA_CURTO,
  blocos_fixos, set_historia, image_start). O roteirista escreve só AÇÃO, ESTADO, CÂMERA e
  SOM; nunca descreve rosto, roupa, cor ou proporção, nem "melhora" o set.
- A continuidade visual é responsabilidade do motor (âncora + prompt montado), não da
  memória do modelo.

EMENDA / ÂNCORA (anti-ghost)
- O primeiro plano de cada clipe descreve o enquadramento EXATO da âncora (image_start).
- Insertos de close só depois de 0,6 s — nunca colados no 0,0 da âncora.
- O `estado_in` do primeiro clipe descreve a âncora; sem ghost, sem morph, sem dupla exposição
  na emenda.

PERSONAGENS E LEIS DE FERRO
- TÉO à esquerda: mede, planeja, confia no método; erra por excesso de precisão.
- JUCA à direita: executa com convicção total; erra por pressa e por força.
- Quem mede nunca executa; quem executa nunca confere — o erro nasce do intervalo entre os dois.
- ZERO fala, ZERO texto legível. ÁUDIO V6 = foley diegético nomeado + música instrumental
  discreta (non_diegetic_music SEMPRE presente: nunca vazio, nunca N/A, nunca vocal) +
  pelo menos 1 som bucal não-verbal por clipe (resfolego, suspiro, assobio baixo).
- DANO SÓ MATERIAL: ninguém se machuca, sem dor, sem sangue, sem animal machucado, sem crueldade.
- Reação subdimensionada: eles registram o desastre e voltam ao trabalho; nunca pânico, nunca
  "cara de ops". No fim, orgulho e aperto de mãos.
- Todo clipe termina EM MOVIMENTO.

CLIENTE (lei v4)
- O cliente é mudo, no figurino do setor, e aparece no PRIMEIRO e no ÚLTIMO clipe (chegada e
  nota fiscal). Sem isso o episódio não tem fecho.
- Nos clipes 1 e N, ocupação AGENDADA: o cliente aparece só no plano que o nomeia.
- Nos clipes do meio, ocupação ABSOLUTA: só TÉO e JUCA em quadro; o cliente não ancora.
- Ele nunca fala, nunca ajuda, nunca atrapalha; o serviço termina entregue a ele.

FÍSICA (o cardápio seguro)
- Uma primitiva por clipe: cair/tombar, escorregar, quicar/viajar, encher/transbordar,
  dobrar/ceder, prensar/inflar, rolar. Varie; repetir a mesma física é tique.
- Cada primitiva tem UM autor e UM palco. Nada de corrente de eventos.
- Proibido dano invisível (curto, pane, falha interna, sobrecarga) e climas fora de quadro.
- Proibido cabo/fio/mangueira rebocando objeto pesado; líquido andando metros na horizontal;
  objeto entrando em quadro vindo de fora em menos de 1 s; máquina complexa inventada no clipe.

ARCO E PAYOFF (consciência de começo, meio e fim)
- COMEÇO: tarefa banal + objetivo claro + plantio do objeto que vai pagar a piada.
- MEIO: solução errada plausível -> consequência -> gambiarra pior -> escalada (cada degrau
  herda do anterior; a superfície muda: objeto -> parede -> piso -> teto/estrutura).
  Em 60 s, UM degrau só (regra v3/v4): a escalada acontece DENTRO dele (a mesma gag cresce
  em tamanho/velocidade). Em 300 s, 3–4 degraus de superfície.
- FIM: clímax absurdo + PAYOFF VISUAL (a imagem que resume o desastre) + orgulho + serviço
  entregue errado + nota fiscal.
- PAYOFF não é explicação: é a imagem/punchline que o público vê. O último clipe deve conter o
  objeto do callback e a imagem final declarada em `payoff_visual`.
"""

# ─────────────────────────────────────────────────────────────────────────────
# 3. O SCHEMA NOVO (campos que materializam o cérebro no JSON)
# ─────────────────────────────────────────────────────────────────────────────
SCHEMA = r"""
=== CAMPOS NOVOS DO EPISÓDIO (canon zeca_joca_v1) ===
Além de todos os campos v4 (titulo, logline, setor, servico, cliente, mecanismo,
degrau_final, objetos_plantados, callback_object, set_historia, continuidade, assinatura,
shots com planos/gag/objeto_gag/fisica/reacao/som/overall_soundscape/non_diegetic_music),
o JSON declara o arco de comédia:

  "canon": "zeca_joca_v1",
  "premissa_simples": "a tarefa banal em 1 linha (o que eles querem fazer)",
  "solucao_errada":  "a solução plausível para eles e errada para o público",
  "escalada":        ["objeto", "parede", "piso", "teto"],
                     # 60 s: um degrau só (ex.: ["parede"]); a escalada acontece
                     # DENTRO dele (mesma gag cresce em variação).
                     # 300 s: 3–4 degraus de superfície.
  "payoff_visual":   "a imagem final que resume o desastre e fecha a gag",
  "otimismo_final":  "como eles comemoram o resultado (orgulho, aperto de mãos)",

E cada clipe declara, além dos campos v4:

  "causa":  "o que do clipe/estado anterior dispara a gag (visível)",
  "efeito": "a mudança física visível e persistente",
  "payoff": "a reação/punchline do clipe",
  "escala": "objeto | parede | piso | teto"

REGRA DE PREENCHIMENTO: `causa` e `herda_de` devem citar o MESMO objeto/estado; `efeito` deve
aparecer no `estado_out`; `payoff` deve descrever o corpo (não "eles olham"); o último `payoff`
e o `payoff_visual` devem citar o `callback_object`. A `escalada` nunca volta atrás.

REGISTRO COMPLETO (o validador cobra linha por linha):
- TODO `objeto_gag` de cada clipe entra em `objetos_plantados`: `plantado_no_clipe` = o
  primeiro clipe em que o objeto aparece; `pago_no_clipe` = o último. NADA nasce do nada.
- `herda_de` = o NOME CURTO do objeto/estado, verbatim como aparece no `estado_out` (ou no
  `objeto_gag`) do clipe anterior — nunca uma frase descritiva.
- ARCO DE ESCALADA: a MESMA família de `objeto_gag` volta em pelo menos 2 clipes com física
  diferente (ex.: o rolo escorrega no c03; a bandeja dobra o MESMO painel no c04). Um objeto
  diferente por clipe é acidente em série, não escalada — a série é gambiarra que cresce.
- `assinatura` = o FECHO DA SÉRIE: o texto DEVE citar "nota fiscal" sendo entregue ao
  cliente (mesmo que seja um envelope, pasta ou folha — a palavra "nota fiscal" tem que
  estar lá; é a assinatura que o público reconhece em todo episódio).
"""

CHECKLIST = r"""
=== CHECKLIST DO CÉREBRO DE COMÉDIA (antes de entregar) ===
[ ] a tarefa é banal e o objetivo é claro em 2 segundos?
[ ] a primeira solução parece lógica para eles e errada para o público?
[ ] o erro tem lógica interna (não é burrice aleatória)?
[ ] cada clipe tem UMA causa visível, UM efeito físico e UM payoff?
[ ] o estado_out do clipe N == estado_in do clipe N+1?
[ ] cada objeto tem contagem, plantio e dono de posição; nada duplica/teleporta/some?
[ ] o fundo é o mesmo em todos os clipes e o SET é afirmativo/fechado?
[ ] a escalada herda do degrau anterior e termina no payoff visual?
[ ] o último clipe entrega o serviço errado + callback + orgulho?
[ ] zero fala/texto legível; música instrumental discreta (nunca N/A); dano material; ninguém se machuca?
[ ] a mesma gag/mecanismo volta com variação (repetição com física diferente)?
[ ] o público vê o erro antes dos personagens?
[ ] a gag nasce da tarefa (o objeto do gag é o objeto do serviço)?
[ ] nenhuma solução veio de sorte, ajuda externa ou corte mágico?
[ ] o texto não descreve aparência/roupa/cor (isso é da âncora)?
[ ] a gag é original (mecânica emprestada, cena nova)?
"""

# ─────────────────────────────────────────────────────────────────────────────
# 4. BLOCOS PRONTOS PARA INJEÇÃO
# ─────────────────────────────────────────────────────────────────────────────
BLOCO_MESTRE = "\n\n".join([
    "=== " + MARCA + " — CANON " + VERSAO + " (OBRIGATÓRIO) ===",
    "Você não escreve piadas soltas: você constrói MECÂNICAS DE DESASTRE no espírito de "
    "Zeca e Joca / Pat & Mat. Leia o cérebro inteiro antes de planejar o episódio.",
    REFERENCIA.strip(),
    ORIGINALIDADE.strip(),
    CONTINUIDADE.strip(),
    SCHEMA.strip(),
    CHECKLIST.strip(),
])

BLOCO_COMPLETO = BLOCO_MESTRE

BLOCO_CURTO = r"""
=== CÉREBRO DE COMÉDIA TÉO & JUCA (canon zeca_joca_v1) ===
Referência: Zeca e Joca / Pat & Mat (1976) — dois vizinhos faz-tudo, claymation muda, humor
slapstick de incompetência criativa. Tarefa banal -> solução errada plausível -> consequência
visual -> gambiarra pior -> escalada -> clímax absurdo -> orgulho + aperto de mãos. O público
vê o erro antes deles; o riso nasce da seriedade deles diante do desastre.
Contrato: UM clipe = UM objeto + UMA causa + UM efeito + UM payoff. Causa visível no clipe
anterior (herda_de/causa); efeito material persistente; estado_out(N) == estado_in(N+1); cada
objeto tem contagem, plantio e dono de posição (nada duplica, teleporta ou some); SET afirmativo
e fechado (sem exterior); TÉO mede à esquerda, JUCA executa à direita; zero fala/texto legível;
música instrumental discreta (non_diegetic_music nunca N/A) + som bucal não-verbal por clipe;
dano só material; o último clipe fecha com o callback e o payoff_visual.
Originalidade: inspire a mecânica, não copie personagens/cenas; TÉO & JUCA são originais.
Sem sorte: toda solução tem custo visual. Aparência/roupa/cor vêm da âncora; o roteirista não reescreve.
JSON: canon=zeca_joca_v1, premissa_simples, solucao_errada, escalada[], payoff_visual,
otimismo_final; por clipe: causa, efeito, payoff, escala (objeto|parede|piso|teto).
"""


def bloco(completo=True):
    """Bloco pronto para o prompt. completo=True = cérebro inteiro (padrão)."""
    return BLOCO_MESTRE if completo else BLOCO_CURTO


def resumo():
    """Resumo de uma linha para logs/status."""
    return "%s v%s — Zeca e Joca/Pat & Mat + causa->efeito->payoff (%d chars)" % (
        MARCA, VERSAO, len(BLOCO_MESTRE))
