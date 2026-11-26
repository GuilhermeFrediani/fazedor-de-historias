# PACOTE PARA ANALISE V6 — arquivos e trechos
Commit de referencia: `9a979f3` (main, sincronizado com origin/main).
Arquivos completos:
- `fazedor_app/fazedor_app.py` — app, extrator de JSON, `SOM_NOMEADO`, `VERBOS_GAG`, `validar_dossie()`.
- `fazedor_app/regras_v4.py` — `montar_prompt_v4()` e `validar_montagem()`.
- `fazedor_app/regras_v6.py` — `PROMPT_MESTRE_V6` (copia canonica em `PROMPT_SISTEMA_v6.txt`, byte-igual).
- `pipeline/qc_visao.py` — gate de visao como terceira camada (visual/fisica).

## 1. fazedor_app.py — extrator e vocabulario do validador

### extrair_json

`fazedor_app.py:135-152`

```python
def extrair_json(txt):
    """Resumo (antes do ```json) + JSON do episódio, tolerando cercas."""
    if not txt:
        return None, None
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", txt, re.S)
    if m:
        bruto = m.group(1)
        resumo = txt[:max(txt.find("```"), 0)].strip()
    else:
        i, j = txt.find("{"), txt.rfind("}")
        if i < 0 or j <= i:
            return txt.strip(), None
        bruto = txt[i:j + 1]
        resumo = txt[:i].strip()
    try:
        return resumo, json.loads(bruto)
    except Exception:
        return resumo, None
```
### SOM_NOMEADO (whitelist atual)

`fazedor_app.py:202-209`

```python
SOM_NOMEADO = re.compile(
    r"\b(hit|fall|creak|scatter|pour|hiss|rattle|knock|click|buzz|clank|slide|drip|tap|snap|"
    r"pop|squeak|tremble|roll|spray|spark|shatter|stretch|scrape|sizzle|whoosh|thud|bang|"
    r"ring|squeal|flap|whir|chime|slosh|crack|crumple|swish|grind|patter|crackle|clatter|"
    r"groan|hum|lap|slap|rumble|thump|tick|clink|rustle|splash|bump|whistle|sputter|clang|"
    r"blare|blast|chug|clop|clump|jangle|sway|fizz|drip|echo|vibrat|wheeze|sniff|chomp|"
    r"scritch|shuffl|whizz|zing|tonk|tock|creek|creak)"
    r"(?:s|es|ed|ing)?\b", re.I)
```
### VERBOS_GAG (check de piada fisica)

`fazedor_app.py:577-584`

```python
VERBOS_GAG = ("escorrega", "escorreg", "desliza", "tomba", "voa", "voou", "quica", "rola",
              "dobra", "curva", "arca", "cede", "racha", "estala", "estoura", "esguicha",
              "vaza", "transborda", "incha", "cresce", "sobe", "levanta", "empurra", "prensa",
              "esmaga", "arranca", "torce", "gira", "despenca", "cai", "fura", "quebra",
              "derruba", "salta", "estufa", "suga", "chupa", "espirra", "entorna", "treme",
              "cusp", "jorra", "vira", "tomb", "estica", "encolhe", "desaba", "afunda",
              "quica", "desliz", "explode", "vibra", "rasga", "enrosca", "trav", "sobe")
VERBOS_PROCESSO = ("mede", "medir", "confere", "conferir", "verifica", "aprova", "calcula",
```
### validar_dossie (validador narrativo do /api/validar)

`fazedor_app.py:1368-1398`

```python
def validar_dossie(ep):
    ep_med = _com_action(ep)
    base = _validar_dossie_v2(ep_med)
    # v4 substitui tres regras da v2: trilha obrigatoria (nao N/A), montagem em planos
    # (nao 'beats') e prompt curto (nao 300-900 chars de acao corrida).
    if any(s.get("planos") for s in (ep_med.get("shots") or [])):
        # v6: o erro de musica NAO e mais suprimido — non_diegetic_music instrumental
        # passou a ser obrigatorio. So as regras de forma do formato v2 caem.
        base["avisos"] = [a for a in base["avisos"]
                          if "beats:" not in a and "alvo v2: 300-900" not in a]
    render = regras_v3.validar_renderizavel(ep_med)
    erros = list(base.get("erros", [])) + list(render.get("erros", []))
    avisos = list(render.get("avisos", [])) + list(base.get("avisos", []))
    humor = base.get("humor", 0)
    nota = round(0.35 * humor + 0.65 * render["nota"], 1)
    avisos.insert(0, "RENDERIZABILIDADE: %d/10 (peso 65%%) - %s"
                  % (render["nota"], "; ".join(render["checks"]) or "nada comprovado"))
    mont = regras_v4.validar_montagem(ep_med)
    erros += [e for e in mont["erros"] if e not in erros]
    avisos = ["MONTAGE: %d/10 - %s" % (mont["nota"], "; ".join(mont["checks"]) or "-")] + \
             mont["avisos"] + avisos
    nota = round(0.30 * humor + 0.35 * render["nota"] + 0.35 * mont["nota"], 1)
    base.update({"erros": erros, "avisos": avisos, "humor": humor,
                 "render": render["nota"], "montage": mont["nota"], "nota": nota,
                 "formato": "dossie_v4", "checks_render": render["checks"],
                 "checks_montage": mont["checks"]})
    return base


if __name__ == "__main__":
    main()
```
## 2. regras_v4.py — montagem do prompt H3 e validacao de renderizabilidade

### montar_prompt_v4 (contrato H3)

`regras_v4.py:190-269`

```python
def montar_prompt_v4(s, ep, blocos, musica=None, cliente_autorizado=False,
                    ancora_descricao=None, exigir_cortes=False):
    """Prompt no formato OFICIAL do H3 (guia base_en):
       1) estilo + composicao + sujeitos + cenario (curto, ~70 palavras)
       2) planos com corte datado: [Shot 1] ... [Shot 2] At 00:03.500, ...
       3) overall_soundscape (1-4 frases)  4) non_diegetic_music
    Sem lista de negativos.

    CONSERTO 5 (auditoria 21/11): cliente_autorizado=True → OCUPACAO AGENDADA
    (o cliente militar de uniforme olive aparece so no plano que o nomeia) para os
    clipes 1 e N; False → ocupacao absoluta nos clipes do meio. A ocupacao
    absoluta em TODOS os clipes brigava com a lei v4 e com o gate de ancora.

    CONSERTO 6 (auditoria 21/11): ancora_descricao (EN) forca planos[0] a
    descrever EXATAMENTE o enquadramento da ancora (image_start). Sem isso, nos
    clipes com image_start o modelo faz MORPH da ancora para o plano 1 dentro do
    1o segundo — foi o ghost/double-exposure medido em 1 s no teste de 20 s.
    Inserto (plano de close) jamais nasce em 0,0 s: vale o piso de 0,6 s.
    """
    b = blocos or {}
    set_txt = (b.get("SET_OFICINA", "") if str(s.get("set", "historia")) == "oficina"
               else str(ep.get("set_historia") or s.get("set_historia") or "")).strip()
    set_txt = set_txt.replace("SET:", "").strip()

    planos = s.get("planos") or []
    if exigir_cortes and len(planos) < 2:
        # v6: barreira de producao — clipe sem corte nao chega ao render.
        raise ValueError(
            "[clipe %s] %d plano(s): a v4/v6 exige 2-3 planos com corte datado."
            % (s.get("n", "?"), len(planos)))
    if not planos:                        # compatibilidade com episodios antigos
        planos = [{"t": "00:00.000", "texto": str(s.get("action", ""))}]

    # CONSERTO 6: planos[0] DESCREVE A ANCORA (image_start) — sem isso o modelo
    # faz morph do enquadramento da ancora para o plano 1 no 1o segundo (ghost).
    if ancora_descricao:
        p0 = dict(planos[0]) if planos else {"t": "00:00.000"}
        p0["t"] = "00:00.000"
        p0["texto"] = str(ancora_descricao)
        planos = [p0] + list(planos[1:])
    # CONSERTO 6b: inserto datado em >= 0,6 s (nunca colado no 0,0 da ancora).
    for p in planos[1:]:
        t = str(p.get("t") or "").strip()
        try:
            seg = float(t.split(":")[-1])
        except (ValueError, AttributeError):
            continue
        if 0 < seg < 0.6:
            p["t"] = "00:00.600"

    cabeca = " ".join(x for x in (ESTILO_CURTO, set_txt, TEO_CURTO, JUCA_CURTO) if x)
    # OCCUPACAO: AGENDADA (cliente autorizado nos clipes 1 e N) ou ABSOLUTA (meio).
    # CONSERTO 5: a ocupacao absoluta em todo clipe apagava o cliente da lei v4.
    ocupacao_absoluta = ("Exactly two clay puppets appear in the frame: TEO stays at frame left "
                         "and JUCA stays at frame right; no other people or animals appear.")
    ocupacao_agendada = ("TEO stays at frame left and JUCA stays at frame right. The military "
                         "client in olive uniform appears ONLY in the shot that names him, "
                         "silent, no dialogue; no other people or animals appear.")
    ocupacao = ocupacao_agendada if cliente_autorizado else ocupacao_absoluta
    # CADEIA DE ESTADO (P0-2): o modelo precisa SABER como o mundo amanhece e como termina.
    estado_in = str(s.get("estado_in", "")).strip().rstrip(".")
    estado_out = str(s.get("estado_out", "")).strip().rstrip(".")
    corpo = []
    for i, p in enumerate(planos):
        txt = str(p.get("texto", "")).strip()
        if i == 0:
            corpo.append("[Shot 1] " + txt)
        else:
            corpo.append("[Shot %d] At %s, the camera cuts to %s"
                         % (i + 1, str(p.get("t") or _hora(i * 3.5)), txt))
    desc = cabeca + " " + ocupacao + " "
    if estado_in:
        desc += "AT START: " + estado_in + ". "
    desc += " ".join(corpo)
    desc += (" They do not speak and their mouths do not move, but they breathe, swallow and "
             "react with their whole bodies.")
    if estado_out:
        desc += " AT END: " + estado_out + "."

    p_out = "integrated_multimodal_description: " + " ".join(desc.split())
```
### validar_montagem (renderizabilidade)

`regras_v4.py:296-537`

```python
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
    # v5.2: o cliente nao e sempre o militar — o ep diz quem e (padre, sindico...).
    palavras_cli = ["client", "cliente", "military boot", "uniformed"]
    nome_cli = str(ep.get("cliente", "")).strip().lower()
    palavras_cli += [w for w in re.split(r"[\s/]+", nome_cli) if len(w) >= 4]
    RE_CLIENTE_EP = re.compile(
        r"\b(" + "|".join(re.escape(w) for w in dict.fromkeys(palavras_cli)) + r")\b", re.I)
    cliente = any(RE_CLIENTE_EP.search(str(p.get("texto", ""))) for p in (shots[0].get("planos") or []))
    cliente_fim = any(RE_CLIENTE_EP.search(str(p.get("texto", ""))) for p in (shots[-1].get("planos") or []))
    if cliente and cliente_fim:
        nota += 1; checks.append("cliente abre e fecha o episodio")
    else:
        avisos.append("o cliente nao aparece no 1o e no ultimo clipe - sem fecho.")
    if n < 3:
        nota = min(nota, 6)

    # g) CADEIA DE ESTADO (P0-1): estado_in(N) deve casar com estado_out(N-1).
    #    A v3 comparava o clipe com ele mesmo e contava OK quando DIFERIA; a v4
    #    simplesmente não checava. Aqui a corrente é real e bloqueante.
    def _norm(t):
        return " ".join(t.lower().strip().rstrip(".").split())

    cadeia_ok = 0
    prev_out = None
    for s in shots:
        i = s.get("n", "?")
        ei = _norm(str(s.get("estado_in", "")))
        eo = _norm(str(s.get("estado_out", "")))
        if not ei or not eo:
            erros.append("[%s] falta estado_in/estado_out - a cadeia de continuidade "
                         "nao pode ser validada." % i)
        elif prev_out is not None and ei != prev_out:
            erros.append("[%s] QUEBRA DE CADEIA: estado_in nao casa com o estado_out do "
                         "clipe anterior.\n     estado_out(N-1): %s\n     estado_in(N)   : %s"
                         % (i, prev_out, ei))
        else:
            cadeia_ok += 1
        prev_out = eo
    if cadeia_ok == n:
        checks.append("cadeia de estado emendada (estado_out N-1 == estado_in N)")

    # ── CHECKS CAUSAIS (v4.2) ────────────────────────────────────────────────
    # h) registro de props: todo objeto_gag[N] deve estar plantado (plantado <= N)
    plantados = ep.get("objetos_plantados") or []
    for s in shots:
        i = s.get("n", "?")
        og = str(s.get("objeto_gag", "")).strip().lower()
        if not og:
            continue
        if not any((og in po or po in og)
                   and int(p.get("plantado_no_clipe", 999)) <= int(i)
                   for p in plantados
                   for po in [str(p.get("objeto", "")).lower()]):
            # CONSERTO 7 (auditoria 21/11): plantio era AVISO e nao bloqueava —
            # promovido a ERRO: objeto que nasce do nada e defeito de contrato.
            erros.append("[%s] objeto_gag '%s' nao esta no registro objetos_plantados "
                         "(com plantado <= %s) - objeto pode nascer do nada." % (i, og, i))

    # i) callback + degrau_final no ULTIMO clipe (o fecho precisa existir)
    if shots:
        ult = shots[-1]
        fecho = " ".join([str(ult.get("estado_out", ""))] +
                         [str(p.get("texto", "")) for p in (ult.get("planos") or [])]).lower()
        cb = str(ep.get("callback_object", "")).strip().lower()
        og_ult = str(ult.get("objeto_gag", "")).strip().lower()
        if cb and cb not in fecho and cb not in og_ult and og_ult not in cb:
            # CONSERTO 7: callback ausente era AVISO — promovido a ERRO (fecho).
            erros.append("callback_object '%s' nao aparece no ultimo clipe - o payoff "
                         "da assinatura ficou no papel." % cb)
        if not str(ep.get("degrau_final", "")).strip():
            erros.append("episodio sem degrau_final - a escada nao tem topo.")

    # j) fisica distinta (cardapio tem 7; repetir e tique)
    fis = [str(s.get("fisica", "")).strip().lower() for s in shots if s.get("fisica")]
    dup = sorted({f for f in fis if fis.count(f) > 1})
    if dup:
        avisos.append("fisica repetida: %s - o cardapio tem 7 primitivas, varie." % ", ".join(dup))

    # k) herda_de (causa visivel): o objeto do clipe N nasce do clipe N-1
    for idx, s in enumerate(shots):
        i = s.get("n", "?")
        if idx == 0:
            continue  # o primeiro clipe nao herda de ninguem
        hd = str(s.get("herda_de", "")).strip().lower()
        if not hd:
            erros.append("[%s] sem 'herda_de' - declare de qual objeto/estado do clipe "
                          "anterior esta gag nasce (causa visivel)." % i)
            continue
        ei = str(s.get("estado_in", "")).lower()
        og_prev = str(shots[idx - 1].get("objeto_gag", "")).lower()
        if hd in ei or hd in og_prev or og_prev in hd:
            continue
        erros.append("[%s] herda_de '%s' nao aparece nem no estado_in nem no objeto_gag "
                      "do clipe anterior - causa pode estar invisivel." % (i, hd))

    # l) ARCO: repeticao com variacao (a mesma gag/mecanismo volta escalando)
    if len(shots) >= 6:
        arc_ok = False
        for a in range(len(shots)):
            for b in range(a + 1, len(shots)):
                oa = str(shots[a].get("objeto_gag", "")).strip().lower()
                ob = str(shots[b].get("objeto_gag", "")).strip().lower()
                fa = str(shots[a].get("fisica", "")).strip().lower()
                fb = str(shots[b].get("fisica", "")).strip().lower()
                if oa and (oa in ob or ob in oa) and fa != fb:
                    arc_ok = True
                    break
            if arc_ok:
                break
        if arc_ok:
            checks.append("arco de repeticao com variacao (mesmo objeto, fisica diferente)")
        else:
            erros.append("sem arco: nenhuma gag volta com fisica diferente - a serie e "
                          "gambiarra que escala, nao acidente novo a cada clipe.")

    # ── CÉREBRO DE COMÉDIA (canon zeca_joca_v1) ──────────────────────────────
    # m) começo/meio/fim + causa → efeito → payoff declarados e coerentes.
    #    Legado (sem 'canon') recebe só aviso; o prompt v5 exige o canon em toda
    #    geração nova. Com o canon declarado, os campos são CONTRATO (erro).
    canon = str(ep.get("canon", "")).strip().lower()
    versao_ok = bool(canon_comedia) and canon == canon_comedia.VERSAO
    if not canon:
        avisos.append("CANON: episódio sem 'canon: zeca_joca_v1' — o prompt v5 exige o "
                      "cérebro de comédia declarado (premissa_simples, solucao_errada, "
                      "escalada, payoff_visual, otimismo_final).")
    elif not versao_ok:
        erros.append("CANON: versão '%s' desconhecida — use canon: zeca_joca_v1." % canon)
    else:
        for campo in ("premissa_simples", "solucao_errada", "payoff_visual",
                      "otimismo_final"):
            if not str(ep.get(campo, "")).strip():
                erros.append("CANON: campo '%s' ausente — o arco começo→meio→fim precisa "
                             "declarar a tarefa, a solução errada, o payoff visual e o "
                             "orgulho final." % campo)
        esc = [str(x).strip().lower() for x in (ep.get("escalada") or [])
               if str(x).strip()]
        ordem_esc = {"objeto": 1, "parede": 2, "piso": 3, "teto": 4}
        min_deg = 1 if n <= 6 else 3
        if len(esc) < min_deg:
            erros.append("CANON: 'escalada' precisa de %d degrau(s) para %d clipes "
                         "(60 s: um degrau de superfície; 300 s: objeto→parede→piso→teto)."
                         % (min_deg, n))
        else:
            vals = [ordem_esc.get(e) for e in esc]
            if any(v is None for v in vals):
                erros.append("CANON: 'escalada' usa só objeto|parede|piso|teto "
                             "(recebido: %s)." % esc)
            elif vals != sorted(vals):
                erros.append("CANON: a escalada volta atrás (%s) — cada degrau deve "
                             "herdar do anterior." % esc)
        for s in shots:
            i = s.get("n", "?")
            for campo in ("causa", "efeito", "payoff", "escala"):
                if not str(s.get(campo, "")).strip():
                    erros.append("CANON [%s]: campo '%s' ausente — o clipe precisa da "
                                 "corrente causa→efeito→payoff." % (i, campo))
            e = str(s.get("escala", "")).strip().lower()
            if e and e not in ordem_esc:
                erros.append("CANON [%s]: escala '%s' inválida (objeto|parede|piso|teto)."
                             % (i, e))
        if versao_ok and not any("CANON" in x for x in erros):
            checks.append("cérebro de comédia completo (causa→efeito→payoff + payoff visual)")

    if nota < 7:
        erros.append("NOTA DE MONTAGE %d/10: o episodio nao tem ritmo (minimo 7)." % nota)
    return {"erros": erros, "avisos": avisos, "nota": nota, "checks": checks}
```
## 3. regras_v6.py — secoes onde inserir a REGRA DE TRANSICAO FISICA VISIVEL

### PARTE 10 — FISICA EXECUTAVEL (local sugerido)

`regras_v6.py:447-470`

```python
# PARTE 10 — LIMITES DE SEGURANÇA E FÍSICA

## 35. DANO MATERIAL

Desastre é material. Proibido ferimento, sangue, dor, crueldade, animal machucado,
sofrimento, violência realista. A comédia física é inofensiva.

## 36. FÍSICA EXECUTÁVEL

Primitivas preferidas (UMA por clipe): cair/tombar, escorregar, quicar/viajar,
rolar, dobrar/ceder, transbordar/encher, prensar/inflar. Varie; repetir a mesma
física é tique.

Proibido: cabo/fio/mangueira rebocando objeto pesado; líquido andando metros na
horizontal; objeto entrando em quadro vindo de fora em menos de 1 s; máquina
complexa inventada no clipe; dano invisível (curto, pane, falha interna, sobrecarga).

---

# PARTE 11 — PROCESSO OBRIGATÓRIO (5 FASES)

## 37. FASE 1 — COMPREENSÃO

Extraia: setor, serviço, cliente, objetivo, conflito e a característica dos personagens
```
### PARTE 13 — CONTRATO DE SAIDA (campos V6, nao alterar)

`regras_v6.py:549-560`

```python
# PARTE 13 — CONTRATO DE SAÍDA

## 45. FORMATO OFICIAL

O pipeline recebe o formato PROMPT_MESTRE. NÃO substitua por `beats + action`.

A estrutura é: dados do episódio + `shots[]` com `planos[]`, `estado_in`, `estado_out`,
`overall_soundscape`, `non_diegetic_music`. Os campos de planejamento e auditoria
continuam no JSON mesmo quando não vão direto ao render.

## 46. CAMPOS DO EPISÓDIO (todos obrigatórios e não vazios)

```
### PARTE 14 — APROVACAO

`regras_v6.py:655-670`

```python
# PARTE 14 — APROVAÇÃO

## 52. METAS DE QUALIDADE (0 a 10)

Estética/renderizabilidade 9 · Consistência dos personagens 9 · Acting e gags 8 ·
Continuidade 9 · Causalidade 9 · Ritmo 8.
São metas de desenvolvimento, não resultados presumidos.

## 53. REPROVAÇÃO AUTOMÁTICA

JSON inválido · clipe com menos de 2 planos · estado incompatível entre clipes ·
objeto duplicado ou teleportado · causa sem origem · efeito sem ação física ·
consequência que desaparece sem explicação · gag sem payoff identificável · música
vocal ou diálogo · descrição incompatível com as âncoras · acontecimento sem função
narrativa.

```

## Notas de compatibilidade

- O contrato JSON nao muda: `shots[]`, `planos[]`, `estado_in/out`, `overall_soundscape`, `non_diegetic_music`.
- A regra de transicao entra como texto no system; nenhum campo novo e exigido do modelo.
- O check de piada fisica deve ler `planos[]`, `fisica`, `gag`, `causa`, `efeito`, `payoff` — mantendo `beats/action` apenas como legado.
- `SOM_NOMEADO` deve virar: fonte sonora (foam/paper/steel/leaves/ice) + evento (squish/rasp/click/tap/scrape/brush), sem reduzir o rigor.
