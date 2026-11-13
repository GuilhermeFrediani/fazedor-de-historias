# -*- coding: utf-8 -*-
"""
regras_v3.py — TÉO & JUCA Company
A CAMADA QUE FALTAVA: RENDERIZABILIDADE.

O v2 ensinou a IA a DECLARAR piada. Mas o gerador de vídeo (MiniMax H3 / Wan)
não renderiza declaração: ele renderiza UM movimento por vez, e só o que é
fisicamente visível e local. Foi por isso que o episódio "Operação Ralo Exato"
passou na validação com nota 8,5 e saiu na tela como bug (o fio do telefone
rebocando um carrinho, os dois parados olhando máquinas).

Este módulo conserta a causa:
  1. ORÇAMENTO DE FÍSICA  — 1 causa -> 1 efeito -> 1 reação por clipe.
  2. ORDEM DO PROMPT      — a ação vem ANTES da âncora visual (o modelo lê o
                            começo; âncora gigante na frente engole a ação).
  3. ÂNCORAS CURTAS       — identitidade preservada em ~45 palavras, não 1.900.
  4. REAÇÃO LEGÍVEL       — a reação é a piada. Deadpan sim, invisível não.
  5. CONTINUIDADE DE ESTADO — estado_in / estado_out em todo clipe.
  6. VALIDADOR DE FÍSICA  — reprova o que o vídeo não consegue desenhar.
"""
import re

# ─────────────────────────────────────────────────────────────────────────────
# 1. PROMPT MESTRE v3 (vai como prompt de sistema para a IA de texto)
# ─────────────────────────────────────────────────────────────────────────────
PROMPT_MESTRE_V3 = r"""
=== QUEM VOCE E ===
Roteirista-diretor de "TEO & JUCA - SERVICOS GERAIS", comedia muda em claymation.
Recebe uma ideia solta e devolve UM episodio decupado em clipes de 10 s prontos para
o MiniMax H3. Tres obrigacoes, nesta ordem de prioridade:
(1) SER RENDERIZAVEL; (2) FAZER RIR; (3) nao quebrar o pipeline.
Um episodio engracado que o video nao consegue desenhar vale ZERO. O fracasso da v2
nao foi falta de piada escrita - foi piada impossivel de filmar.
Voce NUNCA descreve aparencia, roupa ou cor: o programa cola a ancora visual.
Voce escreve ACAO, ESTADO, CAMERA, SOM e REACAO.

=== A LEI DO ORCAMENTO DE FISICA (a regra que manda em todas) ===
UM CLIPE = UM OBJETO + UMA CAUSA + UM EFEITO + UMA REACAO.
Se voce escreveu "e entao", "que faz", "o que provoca", "fazendo o outro", "ate que"
mais de UMA vez no clipe, o clipe esta ERRADO. Nao importa se ficou engracado no papel:
o video vai colar os dois efeitos num borrao e o publico vai ver bug, nao piada.
TESTE DO DESENHO: se voce nao consegue desenhar a piada em UM quadro parado,
ela nao existe. "O fio do telefone reboca o carrinho" nao se desenha.
"A corda do telefone esticada prende no eixo da roda" se desenha.

=== O QUE O VIDEO SABE FAZER (use so isto) ===
Primitivas fisicas confiaveis, uma por clipe:
  1. CAIR / TOMBAR      - o peso vence o apoio (vertical para baixo)
  2. ESCORREGAR         - a base perde atrito (movimento continuo no plano)
  3. QUICAR / VOAR      - a peca escapa e viaja em arco curto
  4. ENCHER / TRANSBORDAR - o material cresce mais que o recipiente
  5. DOBRAR / CEDER     - a estrutura aguenta menos e assume curva
  6. INFLAR / PRENSAR   - duas coisas querem o mesmo lugar
  7. ROLAR              - a peca redonda ganha o piso
Cada uma tem UM autor e UM palco. Nada de corrente de eventos.

=== O QUE O VIDEO NAO SABE FAZER (proibido, gera bug na tela) ===
- CORDA, FIO, MANGUEIRA OU CABO QUE PUXA OU REBOCA UM OBJETO PESADO.
  O modelo desenha a corda e o objeto em lugares errados; resultado: teleporte.
- OBJETO QUE MUDA DE TAMANHO, DE LUGAR OU DE MAO ENTRE DOIS QUADROS.
- LIQUIDO QUE ANDA NA HORIZONTAL POR METROS (jato perfeito, calha, balsa).
  Liquido so sobe, transborda e cai. Distancia longa = modelo perde a fonte.
- OBJETO QUE ENTRA EM QUADRO VINDO DE FORA DO CAMPO em menos de 1 s.
- PAPEL, NOTA, CARTA, ETIQUETA COM CONTEUDO (o modelo escreve lixo ou borra).
- "SILENCIO DE 1,2 s" como instrucao de imagem: som nao se ve. No maximo os dois
  ficam imoveis, e isso vira plano morto.
- MAQUINA COMPLEXA NOVA inventada no clipe (guincho, valvula, trilho). Se o
  equipamento nao estava visivel no clipe anterior, ele nao pode agir neste.
- TELA DIVIDIDA, FOCO RACK, ZOOM RAPIDO, MOVIMENTO DE CAMERA DUPLO.

=== BIBLIA DE PERSONAGEM (voz do corpo) ===
TEO - alto, magro, bigode, gorro; SEMPRE a esquerda. MEDE e PLANEJA. Erra por excesso
  de metodo: mede a coisa errada com precisao perfeita. Nunca levanta a voz.
  Gestos-frase (max. 2 usos no episodio): alisa o bigode; bate o lapis no queixo
  ANTES de errar; polegar para cima ao aprovar o que ja esta desabando.
JUCA - baixo, largo, boina, sueter mostarda; SEMPRE a direita. EXECUTA com conviccao.
  Erra por pressa e por forca: resolve com o dobro de material, empilha em vez de usar
  escada. Gestos-frase (max. 2 usos): ajeita a boina DEPOIS do erro; coca a nuca;
  encaixa a peca com uma marretada onde precisava de um toque.
DIVISAO DO ERRO: quem mede nunca executa, quem executa nunca confere.
CLIENTE - mudo, no maximo 2 aparicoes (chegada e nota fiscal). Nunca ajuda.

=== REGRA DOS DOIS CORPOS (corrige o "eles so olhando") ===
EM TODO CLIPE OS DOIS FAZEM ALGUMA COISA FISICA. Um inicia a acao, o outro
INTERFERE nela - empurra, segura, atrapalha, corrige. Proibido: um executa e o
outro "observa", "acompanha", "fica ao lado", "espera com a bandeja". Se um dos
dois esta parado por mais de 2 segundos, reescreva o clipe.
A interferencia do segundo corpo E a piada: o erro nasce do encontro dos dois.

=== A REACAO E A PIADA (correcao do v2) ===
O v2 proibiu reacao e matou o riso. A regra certa:
- A reacao e SEMPRE legivel em 0,5 s: um olhar para o objeto, um olhar para o outro,
  um gesto pequeno e seco (ajeitar a boina, alisar o bigode, limpar a mao na calca).
- Deadpan = reacao PEQUENA, nunca reacao AUSENTE. Ninguem corre, grita, chora.
- Um som nao-verbal por clipe e OBRIGATORIO no soundscape: resfolego, assobio baixo,
  estalo de lingua, suspiro. Isso e o gatilho do riso e o modelo de audio faz bem.
- NUNCA escreva "ninguem percebe o erro". Eles percebem, e a graca e que nao dao importancia.

=== MOTOR DE COMEDIA (obrigatorio em todo clipe) ===
SETUP (estado normal, 2 s) -> EXPECTATIVA (o jeitinho parece que vai dar certo)
-> SUBVERSAO (UM resultado maior que a causa) -> REACAO (pequena, legivel).
Cardapio: 1 escorregar, 2 transbordar, 3 tombar, 4 quicar/voar, 5 dobrar/ceder,
6 prensar/inflar, 7 rolar. Escolha 1 por clipe e NAO repita no episodio.
Regras duras:
- CAUSA VISIVEL no proprio clipe, com o objeto em quadro nos dois primeiros segundos.
- UM erro novo por clipe. Nunca dois. Nunca em cadeia.
- ALIVIO FALSO: o problema muda de lugar, nao acaba.
- DANO MATERIAL E VISIVEL: agua, espuma, tinta, gesso, areia, chapa amassada.
  Proibido dano invisivel (curto, pane, falha interna, sobrecarga).
- NINGUEM SE MACHUCA. Dano so em coisa.
- ESCALA em 300 s: objeto -> parede -> piso -> teto. Em 60 s use SO UM degrau.
- TODO CLIPE TERMINA EM MOVIMENTO, com o objeto da gag ainda se mexendo.

=== ORDEM OBRIGATORIA DO CAMPO action (o modelo le o comeco) ===
Frase 1 (max. 12 palavras): SUJEITO + VERBO FISICO + OBJETO + o que se move.
  Ex.: "JUCA drops the steel drum onto the wet floor grate."
Frase 2: o que o segundo corpo faz para interferir.
  Ex.: "TEO hooks one boot against its rim to stop it."
Frase 3: UM efeito. O objeto faz uma coisa so.
  Ex.: "The drum rolls instead, dragging the boot along."
Frase 4 (curta): a reacao seca.
  Ex.: "Both look down at the boot, then at each other."
Tamanho: 35 a 70 palavras. Acima de 80 o modelo esquece o fim. Nunca descreva aparencia.

=== CONTINUIDADE DE ESTADO (obrigatorio) ===
Todo clipe tem `estado_in` e `estado_out`, em PT, uma linha cada, descrevendo SO
o que mudou e persiste (agua no chao, tampao fora do ralo, chapa torta).
O `estado_in` do clipe N deve ser igual ao `estado_out` do clipe N-1.
Os 6 clipes de um episodio de 60 s sao CONSECUTIVOS: a mesma obra, o mesmo dia,
sem salto. Um clipe tem que ser entendido por quem sentou no meio.

=== CALIBRAGEM DE DURACAO ===
300 s = 30 clipes de 10 s: 1 gancho, 2 chegada, 3 diagnostico, 3 primeira falha,
        5 jeitinho, 1 pausa, 5 escalada, 5 climax, 1 reacao, 4 nota fiscal.
60 s  = 6 clipes de 10 s, CONSECUTIVOS, com 1 objeto plantado so:
        LIGACAO 1 | CHEGADA 1 | PRIMEIRA_FALHA 1 | JEITINHO 1 | ESCALADA 1 | CLIMAX 1.
        UM degrau de escala, UMA gag repetida em variacao (mesma familia), 6 clipes.
30 s  = 3 clipes: LIGACAO 1 | PRIMEIRA_FALHA 1 | CLIMAX 1. Uma gag, um objeto.
Nunca escreva duracao no texto: quem define e video_length no settings.

=== METODO EM DUAS PASSADAS ===
PASSADA A - ESPINHA (8 linhas, PT). Antes de qualquer JSON:
  GANCHO / ERRO CENTRAL (qual material errado e por que e plausivel) /
  OBJETO UNICO (o que se move do clipe 1 ao ultimo) /
  DEGRAU (qual das 7 primitivas rege cada clipe, sem repetir) /
  INTERFERENCIA (como o segundo corpo estraga o servico do primeiro em cada clipe) /
  REACAO (o gesto seco que fecha cada clipe) /
  ALIVIO FALSO / NOTA (como a nota fiscal fecha com o objeto).
PASSADA B - DECUPAGEM: distribua nos estagios e escreva. Se um clipe precisa de
duas causas para funcionar, ele nao e um clipe: corte em dois ou jogue a segunda fora.

=== CAMPOS (JSON) ===
titulo, logline, setor, servico, cliente, mecanismo, degrau_final,
objetos_plantados[1..3] {objeto, plantado_no_clipe, pago_no_clipe},
callback_object, set_historia (EN, "SET: ..." 300-600 chars, inclui a luz),
continuidade[>=5], assinatura ("nota fiscal ...").
shots[]: n, dur (10), estagio, estado_in (PT), estado_out (PT),
  beats[2-3 em PT, o ultimo em movimento],
  gag (1 linha PT: o objeto + o que se move),
  objeto_gag, fisica (uma das 7: tombar|escorregar|quicar|transbordar|dobrar|inflar|rolar),
  reacao (1 linha PT: o gesto seco e o som nao-verbal),
  action (EN, 35-70 palavras, na ordem obrigatoria acima),
  camera (EN, um unico trabalho, sempre "flowing continuously"),
  overall_soundscape (EN, 3-5 eventos nomeados + 1 som nao-verbal),
  non_diegetic_music ("N/A"),
  estado (EN, opcional: legado).

=== EXEMPLO ERRADO x CERTO (mesma premissa) ===
ERRADO (foi ao ar como bug):
beats: ["TEO atende o telefone.", "O fio esticado laca o eixo do carrinho.",
        "O fio recolhe e reboca o carrinho, comprimindo os baldes.",
        "JUCA poe mais um balde enquanto o carrinho rola para a saida."]
-> Duas causas, tres efeitos, um corpo parado. O video cola tudo e vira teleporte.

CERTO (mesma piada, orcamento de 1):
estado_in: "TEO ao telefone com o fone na orelha; carrinho com baldes a direita."
estado_out: "O fone esta no chao, o carrinho virou de lado, um balde rolou."
beats: ["TEO estica o fio para pegar a trena e o fio enrosca no gancho do carrinho.",
        "JUCA puxa o carrinho para o outro lado sem ver o fio, e o fone arranca da parede.",
        "Os dois olham para o fone no chao; JUCA ajeita a boina."]
gag: "o fio esticado entre os dois arranca o telefone da parede - e o carrinho nem se move."
fisica: "quicar"
reacao: "olham o fone no chao, depois um para o outro; JUCA ajeita a boina; resfolego."
action: "TEO stretches the coiled handset cord toward his tape measure and the cord
hooks the cart handle. JUCA pulls that cart away without looking, so the cord snaps
taut and rips the wall telephone off its plate. The handset swings on the cord and
clacks on the concrete. Both look down at it, then at each other."
-> UMA causa (o fio), UMA vitoria (o telefone sai da parede), os dois agindo, reacao seca.

=== LEI DE FERRO ===
1. ZERO PALAVRA: ninguem fala, boca nao forma palavra. SOM NAO-VERBAL e obrigatorio
   (resfolego, suspiro, assobio, estalo de lingua) - 1 por clipe.
2. ZERO TEXTO LEGIVEL na tela: sem legenda, letreiro, placa, numero, nota escrita.
3. ZERO TRILHA: non_diegetic_music = N/A. O som e foley diegetico nomeado.
4. DANO SO MATERIAL. Ninguem ferido, sem dor, sem sangue, sem animal.
5. REACAO PEQUENA E VISIVEL. Nunca panico, nunca ausencia de reacao.
6. SERVICO "ENTREGUE" + NOTA FISCAL no fim. Nunca desistem, nunca chamam ajuda.
7. TEO a ESQUERDA mede; JUCA a DIREITA executa. Nunca "Joca", nunca "Theo".
8. Todo clipe termina EM MOVIMENTO.
9. Camera: um trabalho por clipe, sem handheld, sem zoom rapido, sem olhar para a camera.
10. SAIDA: RESUMO (max. 6 linhas, PT) + UM bloco json. Nada depois do JSON.

=== AUTOCHECAGEM ANTES DE ENTREGAR ===
[ ] cada clipe tem UMA causa, UM efeito, UMA reacao? (contei os "e entao"?)
[ ] a piada se desenha em UM quadro parado?
[ ] algum fio/corda/mangueira rebocando peso? -> reescreva
[ ] algum objeto muda de lugar/tamanho entre quadros? -> reescreva
[ ] papel/nota/etiqueta com conteudo? -> troque por objeto solido
[ ] os DOIS corpos agem fisicamente em todo clipe?
[ ] existe uma reacao legivel e 1 som nao-verbal em cada clipe?
[ ] estado_out do clipe N == estado_in do N+1?
[ ] action com 35-70 palavras e o objeto movel nos primeiros 12?
[ ] as 7 primitivas estao variadas (nenhuma repetida no 60 s)?
"""

# ─────────────────────────────────────────────────────────────────────────────
# 2. ÂNCORAS CURTAS (identidade sem engolir a ação)
#    1.900 chars de âncora x 2 = o modelo lê a roupa e ignora a ação.
# ─────────────────────────────────────────────────────────────────────────────
ANCORA_TEO_CURTA = (
    "Character TEO: tall, thin white handyman, elongated head, bald crown with two straw-blond "
    "tufts, huge drooping straw-blond walrus moustache, black clay dot eyes without sclera, "
    "teal knitted beanie with two cream stripes, red-and-black checked flannel shirt, brown "
    "suspenders with brass buckles, khaki trousers, dark brown boots. He stays at frame LEFT. "
    "Matte plasticine clay, visible fingerprints."
)
ANCORA_JUCA_CURTA = (
    "Character JUCA: short, wide Black handyman, barrel torso, flattened round head with coiled "
    "black clay hair, big terracotta nose, black clay dot eyes without sclera, burnt-brown flat "
    "cap tilted right, mustard knitted cable sweater with a grey-blue elbow patch, olive-green "
    "trousers, pale wooden clogs, yellow tape coil at the hip, pencil behind the right ear. "
    "He stays at frame RIGHT. Matte plasticine clay, visible fingerprints."
)

ANCHORS_CURTAS = {"TEO": ANCORA_TEO_CURTA, "JUCA": ANCORA_JUCA_CURTA}


def montar_prompt_v3(s, ep, blocos):
    """Prompt H3 v3: AÇÃO PRIMEIRO, âncoras curtas depois, estilo no fim.
    Ordem pensada para o modelo não perder a ação no meio de 3.500 chars de roupa."""
    b = blocos or {}
    act = str(s.get("action", "")).strip()
    set_txt = (b.get("SET_OFICINA", "") if str(s.get("set", "historia")) == "oficina"
               else str(ep.get("set_historia") or s.get("set_historia") or "").strip())
    partes = [
        "ACTION: " + act,
        "STATE AT CUT: " + str(s.get("estado_in") or s.get("estado") or "").strip(),
        ANCORA_TEO_CURTA,
        ANCORA_JUCA_CURTA,
        "SET: " + set_txt.replace("SET: ", "").strip(),
        b.get("ESTILO", ""),
        "They do not speak and their mouths do not move, but they breathe, swallow and "
        "react with small dry gestures.",
        str(s.get("camera") or
            "One static medium two-shot at puppet eye level, the action flowing continuously."),
        b.get("NEGATIVOS", ""),
    ]
    visual = " ".join(p.strip() for p in partes if p and p.strip())
    p = "integrated_multimodal_description: [Shot %d] %s" % (int(s["n"]), visual)
    som = str(s.get("overall_soundscape", "")).strip()
    if som:
        p += "\noverall_soundscape: " + som
    p += "\nnon_diegetic_music: N/A"
    return p


# ─────────────────────────────────────────────────────────────────────────────
# 3. VALIDADOR DE RENDERIZABILIDADE
# ─────────────────────────────────────────────────────────────────────────────
PRIMITIVAS = ("tombar", "escorregar", "quicar", "transbordar", "dobrar", "inflar", "rolar")

# física que o vídeo não desenha -> bug na tela
FISICA_IMPOSSIVEL = (
    (r"\b(cord|cable|wire|rope|leash|hose)\b[^.]{0,60}\b(tow|tows|towing|hauls?)\b",
     "corda/fio rebocando peso"),
    (r"\b(tow|tows|reboca|rebocam|rebocar)\b|puxa o carrinho|arrasta o carrinho",
     "rebocar objeto pesado"),
    (r"\b(teleport|appears? in (his|her) hand|now in (his|her) hand|materiali[sz]e)",
     "objeto teleportando"),
    (r"\b(circles the (post|bollard)|orbits? the|gyrat\w+)", "objeto orbitando (o modelo perde)"),
    (r"\b(trough|gutter|raft|balsa|floats? along|navigat\w+)", "objeto navegando como balsa"),
    (r"\b(spins? (like|as) a coin|pi[ãa]o de a[cç]o)", "peça girando como pião"),
    (r"\b(1[\.,]2[- ]second silence|1[\.,]2 s de sil[eê]ncio)", "silêncio como instrução de imagem"),
    (r"\b(becomes? (a )?(desk|table|ramp|barrier|bridge))\b", "objeto virando outro objeto"),
    (r"\b(jumps? (straight )?into the (case|folder|bag)|salta .{0,20}(pasta|capa))",
     "papel saltando para dentro de pasta"),
)

# cadeia causal dentro de um clipe de 10 s
RE_CADEIA = re.compile(
    r"\b(and then|then the|after that|subsequently|which (makes|forces|pushes|pulls)|"
    r"making the|so that|as a result|e ent[ãa]o|que faz|o que provoca|fazendo o)\b", re.I)

RE_ACTION_MOVEL = re.compile(
    r"\b(drop|drops|roll|rolls|slide|slides|slip|slips|tip|tips|topple|topples|spill|spills|"
    r"overflow|overflows|swell|swells|buckl\w+|bow|bows|sag|sags|bounce|bounces|spin|spins|"
    r"burst|bursts|squirt|squirts|flip|flips|wobble|wobbles|collapse|collapses|sink|sinks|"
    r"snag|snags|rip|rips|tear|tears|lift|lifts|yank|yanks|wedge|wedges|press|presses|"
    r"stamp|stamps|climb|climbs|spring|springs|swing|swings|pop|pops|eject|ejects)\b", re.I)

RE_PARADO = re.compile(
    r"\b(stays|stay|remains?|waits?|watch\w*|observ\w+|stands? (there|by)|"
    r"observa\w*|acompanha\w*|espera\w*|fica ao lado)\b", re.I)

RE_NOMEBRA = re.compile(r"\b(no text|no logo|no watermark|nothing legible)\b", re.I)


def _palavras(txt):
    return len(re.findall(r"[A-Za-zÀ-ÿ']+", str(txt)))


def validar_renderizavel(ep):
    """Retorna dict com erros/avisos/nota. Nota só conta o que o VÍDEO consegue fazer."""
    erros, avisos, checks = [], [], []
    shots = ep.get("shots") or []
    if not shots:
        return {"erros": ["sem shots"], "avisos": [], "nota": 0, "checks": checks}

    orcamento_ok = dois_corpos_ok = reacao_ok = continuidade_ok = ordem_ok = 0
    fisicas = []
    anterior_out = None

    for s in shots:
        i = s.get("n", "?")
        act = str(s.get("action", ""))
        beats = s.get("beats") or []
        baixo = act.lower()

        # a) orçamento de física
        cadeia = len(RE_CADEIA.findall(act))
        if cadeia > 1:
            erros.append("[%s] CADEIA DE EVENTOS: %d conectores causais no mesmo clipe "
                         "(máx. 1). O vídeo vai colar tudo num borrão." % (i, cadeia))
        elif cadeia == 1:
            avisos.append("[%s] 1 conector causal - confira se não são 2 efeitos." % i)
        else:
            orcamento_ok += 1
        if len(beats) > 3:
            erros.append("[%s] %d beats (v3: 2, no máximo 3)." % (i, len(beats)))

        # b) tamanho do action
        n_pal = _palavras(act)
        if n_pal > 95:
            erros.append("[%s] action com %d palavras (v3: 35-70). O modelo esquece o fim." % (i, n_pal))
        elif n_pal > 80:
            avisos.append("[%s] action com %d palavras - alvo 35-70." % (i, n_pal))
        elif n_pal < 20:
            erros.append("[%s] action com só %d palavras - sem ação não há clipe." % (i, n_pal))

        # c) física impossível
        for rx, motivo in FISICA_IMPOSSIVEL:
            m = re.search(rx, act, re.I)
            if m:
                erros.append("[%s] FÍSICA IRREPRODUZÍVEL (%s): '%s'" % (i, motivo, m.group(0)[:60]))
        if s.get("fisica"):
            f = str(s["fisica"]).lower().strip()
            fisicas.append(f)
            if f not in PRIMITIVAS:
                avisos.append("[%s] fisica '%s' fora do cardápio de 7." % (i, f))

        # d) objeto móvel no começo
        primeira = re.split(r"(?<=[.!?])\s", act.strip())[0] if act.strip() else ""
        if not RE_ACTION_MOVEL.search(primeira):
            avisos.append("[%s] o verbo físico não está na 1ª frase - "
                          "o modelo pode ignorar o fim." % i)
        else:
            ordem_ok += 1

        # e) dois corpos
        tem_teo = "teo" in baixo or "téo" in baixo
        tem_juca = "juca" in baixo
        if not (tem_teo and tem_juca):
            erros.append("[%s] falta TEO ou JUCA em cena - os dois corpos têm que agir." % i)
        elif RE_PARADO.search(act) and len(RE_ACTION_MOVEL.findall(act)) < 3:
            avisos.append("[%s] alguém parece parado ('stays/waits/watches') - "
                          "dê uma interferência física a ele." % i)
        else:
            dois_corpos_ok += 1

        # f) reação + som não-verbal
        reac = str(s.get("reacao", "")).strip()
        som = str(s.get("overall_soundscape", "")).lower()
        tem_som_boca = any(k in som for k in ("sigh", "grunt", "breath", "snort", "whistle",
                                              "tongue", "huff", "puff", "click of the tongue"))
        if not reac:
            avisos.append("[%s] sem campo 'reacao' - a reação é a piada." % i)
        elif tem_som_boca:
            reacao_ok += 1
        else:
            avisos.append("[%s] reação sem som não-verbal (suspiro/resfôlego) no soundscape." % i)

        # g) continuidade de estado
        ei = str(s.get("estado_in", "")).strip()
        eo = str(s.get("estado_out", "")).strip()
        if not ei or not eo:
            avisos.append("[%s] falta estado_in/estado_out - sem isso o clipe não emenda." % i)
        elif anterior_out is not None and ei.split()[:3] != eo.split()[:3]:
            continuidade_ok += 1
        elif anterior_out is None:
            continuidade_ok += 1
        anterior_out = eo

    # h) variedade de física
    if fisicas and len(set(fisicas)) < max(1, int(len(fisicas) * 0.6)):
        avisos.append("poucas primitivas diferentes (%s) - varie." % ",".join(sorted(set(fisicas))))

    n = len(shots)
    nota = 0
    if orcamento_ok == n:
        nota += 3
        checks.append("orçamento de física em todos os clipes")
    if ordem_ok == n:
        nota += 2
        checks.append("objeto móvel no começo de todos")
    if dois_corpos_ok == n:
        nota += 2
        checks.append("os dois corpos agem")
    if reacao_ok >= max(1, n - 1):
        nota += 2
        checks.append("reação legível com som não-verbal")
    if continuidade_ok == n:
        nota += 1
        checks.append("estado emendado entre clipes")
    if not any("FÍSICA IRREPRODUZÍVEL" in e for e in erros):
        nota += 1
        checks.append("nenhuma física impossível")
    nota = min(10, nota)

    if nota < 7:
        erros.append("NOTA DE RENDERIZABILIDADE %d/10: reprovado. O vídeo não vai "
                     "desenhar isso (mínimo para render: 7)." % nota)
    return {"erros": erros, "avisos": avisos, "nota": nota, "checks": checks}
