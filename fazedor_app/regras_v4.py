# -*- coding: utf-8 -*-
"""
regras_v4.py — TÉO & JUCA Company
A CAMADA QUE FALTAVA ERA A MONTAGE (não a piada).

Diagnóstico da fumaça v3 (medido quadro a quadro no MP4 entregue):
  - o telefone CAIU de verdade (0:00-0:04): a física da v3 funcionou;
  - mas de 0:04 a 0:10 os dois ficam plantados, gesticulando, sem nada acontecendo;
  - o mesmo vazio se repete em 0:18-0:24, 0:28-0:30, 0:36-0:40, 0:52-0:58;
  - o cliente militar NUNCA aparece: a nota fiscal (assinatura da série) não existe no corte;
  - um domo preto aparece debaixo da corrente em 0:46 SEM ter sido plantado;
  - áudio: média -38,5 dB, pico -7,3 dB => não há foley com corpo, não há batida.

Ou seja: a v3 acertou o que FILMAR. Errou o que FAZ RIR. E o que faz rir é:
  1. RITMO DE CORTE dentro do clipe (não um plano fixo de 10 s);
  2. REAÇÃO GRANDE DE CORPO INTEIRO (reação "seca" em plano geral = nada);
  3. SOM (o foley é metade da piada em claymation);
  4. NADA de ar morto: cada segundo tem um corpo em movimento.

Este módulo adiciona as quatro coisas e passa a montar o prompt no formato
oficial do MiniMax H3 (com cortes datados dentro do próprio clipe).
"""
import re

# ─────────────────────────────────────────────────────────────────────────────
# 1. PROMPT MESTRE v4
# ─────────────────────────────────────────────────────────────────────────────
PROMPT_MESTRE_V4 = r"""
=== QUEM VOCE E ===
Roteirista-diretor de "TEO & JUCA - SERVICOS GERAIS", comedia muda em claymation,
para um canal dark de YouTube. Recebe uma ideia solta e devolve UM episodio decupado
em clipes de 10 s prontos para o MiniMax H3.

=== AS TRES CAMADAS (todas obrigatorias, nesta ordem) ===
1. RENDERIZAVEL - o video tem que conseguir desenhar (regra herdada da v3, mantida).
2. ENGRAÇADO - a piada tem que ser vista, e para ser vista ela precisa de RITMO e SOM.
3. EDITAVEL - o clipe tem que ter corte dentro dele. Plano fixo de 10 s e plano morto.

=== A LEI DO CORTE (a correcao principal da v3) ===
TODO CLIPE TEM 2 OU 3 PLANOS DENTRO DELE, com corte datado. O formato oficial do
modelo aceita cortes internos: [Shot 2] At 00:03.500, the camera cuts to ...
Padrao obrigatorio de 10 s:
  PLANO A (0,0-3,5 s)  - INSERTO no objeto que vai falhar (close, objeto grande no quadro)
  PLANO B (3,5-7,0 s)  - PLANO GERAL: a acao fisica acontece (o corpo inteiro se move)
  PLANO C (7,0-10,0 s) - CLOSE NA REACAO: os dois reagindo, ombros e cabeca, som de boca
Sem os tres, o clipe e um plano morto de 10 s e o publico sai.
O corte e o que cria o "molho". O modelo ja sabe cortar: e so pedir com hora.

=== A LEI DO CORPO INTEIRO (a correcao da "reacao seca") ===
A v3 pediu reacao pequena. Em plano geral, reacao pequena = NENHUMA reacao.
Agora a reacao e de CORPO INTEIRO, mas contida em emocao:
  TEO: endireita a coluna de repente, ergue as duas maos na altura do peito,
       alisa o bigode devagar, olha o objeto e depois o JUCA. Nunca grita.
  JUCA: agacha um pouco, apoia as maos nos joelhos, ajeita a boina devagar,
       olha para o teto. Nunca grita.
Regra: a reacao ocupa METADE DO CORPO e dura no minimo 2 s em close.
Nunca escreva "they look at each other": escreva o que os bracos fazem.

=== A LEI DO SOM (a correcao do audio mudo) ===
O audio atual tem media de -38,5 dB: e um clip sem foley, e por isso nao tem graca.
Todo clipe declara 4 a 6 eventos de som CONCRETOS, na ordem em que acontecem:
  material + verbo + intensidade. Ex.: "steel grate slaps the concrete, hard".
E todo clipe tem 2 sons humanos nao-verbais (resfolego, suspiro, estalo de lingua,
assobio baixo) - um no plano B, outro no plano C.
PROIBIDO: som de maquina sem corpo (hum, drone, buzz) e trilha genérica.

=== O QUE FAZ RIR EM CLAYMATION (usa isto, e so isto) ===
a) ESCALA ABSURDA: o esforco e enorme para um resultado minimo (ou o contrario).
b) PESO: tudo tem massa. Objeto de metal cai e quica; boneco de massinha trava.
c) CAUSA UNICA, CONSEQUENCIA DESLOCADA: o erro acontece longe de quem o causou.
d) REPETICAO COM VARIACAO: a mesma gag volta 3x no episodio, cada vez pior.
e) TEMPO MORTO CONTROLADO: 0,5 s de pausa ANTES da queda (nunca depois, nunca 2 s).
f) REACAO MINIMA AO DESASTRE MAXIMO: e o contraste que gera o riso.

=== O QUE MATA O CLIPE (reprovacao automatica) ===
- Plano fixo unico de 10 s (sem corte interno). Reprovado.
- Mais de 1,5 s sem nenhum corpo se movendo. Reprovado.
- Reacao descrita como "observam", "olham", "acompanham" sem gesto de corpo. Reprovado.
- Clipe que termina com os dois parados. Reprovado.
- Corda/fio/mangueira rebocando peso (bug de teleporte). Reprovado.
- Objeto que aparece sem ter sido plantado no clipe anterior. Reprovado.
- Papel/nota/etiqueta com conteudo legivel. Reprovado.
- Duas causas no mesmo clipe ("e entao"). Reprovado.

=== BIBLIA DE PERSONAGEM ===
TEO - alto, magro, bigode, gorro; ESQUERDA. Mede e planeja. Erra por excesso de
  metodo: mede a coisa errada com precisao perfeita. Quanto pior, mais educado.
JUCA - baixo, largo, boina, sueter mostarda; DIREITA. Executa com conviccao total.
  Erra por pressa e por forca: dobro de material, empilha em vez de usar escada.
DIVISAO DO ERRO: quem mede nunca executa, quem executa nunca confere.
CLIENTE - mudo, no maximo 2 aparicoes (chegada e nota fiscal). O figurino diz o setor.
  REGRA NOVA: o cliente APARECE no primeiro e no ULTIMO clipe. Sem isso o episodio
  nao tem fecho e a assinatura da serie desaparece.

=== MOTOR DE COMEDIA (por clipe) ===
SETUP (2 s, objeto grande em quadro) -> EXPECTATIVA (o jeitinho parece funcionar)
-> SUBVERSAO (resultado MAIOR que a causa) -> REACAO DE CORPO INTEIRO (2 s, close).
Cardapio de fisica (1 por clipe, sem repetir): tombar, escorregar, quicar,
transbordar, dobrar, inflar, rolar.

=== FORMATO DA SAIDA (JSON) ===
Episodio: titulo, logline, setor, servico, cliente, mecanismo, degrau_final,
objetos_plantados[], callback_object, set_historia, continuidade[], assinatura.
shots[]: n, dur (10), estagio, estado_in, estado_out,
  planos (LISTA DE 2-3, cada um com "t" e "texto"):
      {"t": "00:00.000", "texto": "Close insert of ... (EN, objeto grande no quadro)"}
      {"t": "00:03.500", "texto": "the camera cuts to ... (EN, plano geral, acao)"}
      {"t": "00:07.000", "texto": "the camera cuts to ... (EN, close, reacao de corpo)"}
  gag (PT, 1 linha), objeto_gag, fisica, reacao (PT, o corpo todo),
  som (PT: 4-6 eventos + 2 sons de boca),
  overall_soundscape (EN, 2-4 frases corridas),
  non_diegetic_music (EN 1-2 frases curtas de instrumento E ritmo, ou N/A).
NAO escreva lista de negativos: o modelo roda em cfg 1, sem ramo negativo, e a
lista acaba virando conceito (foi o que trouxe "cartoon outlines" para o render).

=== METODO ===
PASSADA A (8 linhas em PT): GANCHO / ERRO CENTRAL / OBJETO UNICO / DEGRAU por clipe /
INTERFERENCIA do segundo corpo / REACAO de corpo / ALIVIO FALSO / NOTA.
PASSADA B: decupagem em 2-3 planos por clipe, com horas.
Se um clipe nao tem corte, ele nao esta pronto.

=== AUTOCHEÇAGEM ===
[ ] cada clipe tem 2-3 planos com hora de corte?
[ ] cada clipe tem um inserto no objeto, um plano geral de acao e um close de reacao?
[ ] a reacao descreve bracos/pernas/ombros (nao "olham")?
[ ] 4-6 eventos de som concretos + 2 sons de boca por clipe?
[ ] zero segundo de ar morto? o clipe termina em movimento?
[ ] o cliente aparece no primeiro e no ultimo clipe?
[ ] zero negativo na lista? zero papel com texto? zero fio rebocando peso?
[ ] a mesma gag volta com variacao no minimo 2 vezes no episodio?
"""

# ─────────────────────────────────────────────────────────────────────────────
# 2. ÂNCORAS ULTRA-COMPACTAS (~30 palavras: identidade sem roubar o clipe)
# ─────────────────────────────────────────────────────────────────────────────
TEO_CURTO = ("TEO (frame left): tall thin white clay man, huge straw-blond walrus moustache, "
             "teal knitted beanie with cream stripes, red-and-black checked flannel shirt, "
             "brown suspenders, khaki trousers, dark boots.")
JUCA_CURTO = ("JUCA (frame right): short wide Black clay man, burnt-brown flat cap, mustard "
              "cable-knit sweater, olive-green trousers, pale wooden clogs, pencil behind the "
              "right ear.")

ESTILO_CURTO = ("Claymation plasticine stop-motion, handcrafted modelling clay with visible "
                "fingerprints and matte finish, photographed on a miniature practical set.")

# lista de negativos aposentada: H3 roda em cfg 1, sem ramo negativo.
NEGATIVOS_APOSENTADOS = (
    "No text, no logo, no watermark, no cartoon outlines, no anime eyes, no visible sclera, "
    "no teeth, no plastic gloss, no 2D vector, no CGI look, no extra fingers."
)


def _hora(seg):
    return "%02d:%06.3f" % (int(seg) // 60, seg % 60)


def montar_prompt_v4(s, ep, blocos, musica=None):
    """Prompt no formato OFICIAL do H3 (guia base_en):
       1) estilo + composicao + sujeitos + cenario (curto, ~70 palavras)
       2) planos com corte datado: [Shot 1] ... [Shot 2] At 00:03.500, ...
       3) overall_soundscape (1-4 frases)  4) non_diegetic_music
    Sem lista de negativos."""
    b = blocos or {}
    set_txt = (b.get("SET_OFICINA", "") if str(s.get("set", "historia")) == "oficina"
               else str(ep.get("set_historia") or s.get("set_historia") or "")).strip()
    set_txt = set_txt.replace("SET:", "").strip()

    planos = s.get("planos") or []
    if not planos:                        # compatibilidade com episodios antigos
        planos = [{"t": "00:00.000", "texto": str(s.get("action", ""))}]

    cabeca = " ".join(x for x in (ESTILO_CURTO, set_txt, TEO_CURTO, JUCA_CURTO) if x)
    corpo = []
    for i, p in enumerate(planos):
        txt = str(p.get("texto", "")).strip()
        if i == 0:
            corpo.append("[Shot 1] " + txt)
        else:
            corpo.append("[Shot %d] At %s, the camera cuts to %s"
                         % (i + 1, str(p.get("t") or _hora(i * 3.5)), txt))
    desc = cabeca + " " + " ".join(corpo)
    desc += (" They do not speak and their mouths do not move, but they breathe, swallow and "
             "react with their whole bodies.")

    p_out = "integrated_multimodal_description: " + " ".join(desc.split())
    som = str(s.get("overall_soundscape", "")).strip()
    if som:
        p_out += "\noverall_soundscape: " + som
    mus = musica or str(s.get("non_diegetic_music", "")).strip() or "N/A"
    p_out += "\nnon_diegetic_music: " + mus
    return p_out


# ─────────────────────────────────────────────────────────────────────────────
# 3. VALIDADOR v4 = renderizabilidade (v3, herdada) + MONTAGE + SOM + AR MORTO
# ─────────────────────────────────────────────────────────────────────────────
RE_AR_MORTO = re.compile(
    r"\b(observ\w+|acompanha\w*|wait(s|ing)?|stays?|stands? (still|there)|"
    r"look at each other|olham um para o outro|fica ao lado|espera\w*)\b", re.I)

RE_SOM_BOCA = ("snort", "sigh", "breath", "exhale", "grunt", "huff", "puff", "whistle",
               "tongue", "nasal", "swallow")

RE_CLIENTE = re.compile(r"\b(client|cliente|military boot|uniformed)\b", re.I)

RE_NEGATIVO = re.compile(r"\b(no text|no logo|no watermark|no cartoon outlines|no anime eyes|"
                         r"no plastic gloss|no extra fingers)\b", re.I)


def validar_montagem(ep):
    """Checagens novas: cortes dentro do clipe, reacao de corpo, som com corpo, ar morto."""
    erros, avisos, checks = [], [], []
    shots = ep.get("shots") or []
    if not shots:
        return {"erros": ["sem shots"], "avisos": [], "nota": 0, "checks": checks}

    cortes_ok = reacao_ok = som_ok = plantou_ok = 0
    for s in shots:
        i = s.get("n", "?")
        planos = s.get("planos") or []

        # a) 2-3 planos com hora de corte
        if len(planos) < 2:
            erros.append("[%s] %d plano(s): a v4 exige 2-3 planos com corte datado. "
                         "Plano fixo de 10 s e plano morto." % (i, len(planos)))
        elif len(planos) > 3:
            avisos.append("[%s] %d planos - o modelo perde acima de 3." % (i, len(planos)))
        else:
            if all(str(p.get("t", "")).strip() for p in planos):
                cortes_ok += 1
            else:
                erros.append("[%s] plano sem hora de corte ('t')." % i)

        # b) reacao de corpo inteiro
        reac = str(s.get("reacao", "")).lower()
        if not reac:
            erros.append("[%s] sem campo 'reacao'." % i)
        elif RE_AR_MORTO.search(reac) and not any(
                k in reac for k in ("braço", "braco", "mão", "mao", "ombro", "joelho",
                                    "coluna", "boina", "bigode", "cabeça", "cabeca", "bota")):
            erros.append("[%s] reacao sem gesto de corpo ('%s'): em plano geral isso "
                         "nao aparece." % (i, reac[:50]))
        else:
            reacao_ok += 1

        # c) som com corpo (conta nos DOIS campos: 'som' em PT e soundscape em EN)
        som_pt = str(s.get("som", ""))
        som_en = str(s.get("overall_soundscape", ""))
        som = (som_pt + " ; " + som_en).lower()
        n_boca = sum(1 for k in RE_SOM_BOCA if k in som)
        n_eventos = max(som_pt.count(";") + 1 if som_pt else 0,
                        som_en.count(";") + 1 if som_en else 0)
        if n_boca < 1:
            erros.append("[%s] soundscape sem som de boca (resfolego/suspiro) - "
                         "e o gatilho do riso." % i)
        elif n_eventos < 3:
            avisos.append("[%s] so %d evento(s) de som - alvo 4-6 concretos." % (i, n_eventos))
        else:
            som_ok += 1

        # d) ar morto no texto dos planos
        for p in planos:
            if RE_AR_MORTO.search(str(p.get("texto", ""))):
                avisos.append("[%s] plano descreve alguem parado - troque por gesto." % i)
                break

        # e) objeto plantado
        if s.get("objeto_gag"):
            plantou_ok += 1

        # f) negativo reintroduzido
        if RE_NEGATIVO.search(str(s.get("action", ""))) or RE_NEGATIVO.search(
                " ".join(str(p.get("texto", "")) for p in planos)):
            erros.append("[%s] lista de negativos no prompt: em cfg 1 nao ha ramo negativo, "
                         "a lista vira conceito." % i)

    n = len(shots)
    nota = 0
    if cortes_ok == n:
        nota += 4; checks.append("corte datado dentro de todos os clipes")
    if reacao_ok == n:
        nota += 2; checks.append("reacao de corpo inteiro em todos")
    if som_ok >= max(1, n - 1):
        nota += 2; checks.append("som com corpo e som de boca")
    if plantou_ok == n:
        nota += 1; checks.append("objeto de gag nomeado")
    cliente = any(RE_CLIENTE.search(str(p.get("texto", ""))) for p in (shots[0].get("planos") or []))
    cliente_fim = any(RE_CLIENTE.search(str(p.get("texto", ""))) for p in (shots[-1].get("planos") or []))
    if cliente and cliente_fim:
        nota += 1; checks.append("cliente abre e fecha o episodio")
    else:
        avisos.append("o cliente nao aparece no 1o e no ultimo clipe - sem fecho.")
    if n < 3:
        nota = min(nota, 6)

    if nota < 7:
        erros.append("NOTA DE MONTAGE %d/10: o episodio nao tem ritmo (minimo 7)." % nota)
    return {"erros": erros, "avisos": avisos, "nota": nota, "checks": checks}
